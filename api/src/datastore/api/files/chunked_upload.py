import datetime
import hashlib

from flask import g, request
from flask.ext.login import login_required

from datastore.api import app, file_store, tools
from datastore.api.errors import BasicError
from datastore.api.files import put
from datastore.api.helpers import decorators, display, stream
from datastore import models


def _compute_expire_date():
    # We use a default 24 hours expire date.
    return datetime.datetime.utcnow() + datetime.timedelta(days=1)


def _find_existing_upload(upload_id):
    clause = models.ChunkedUpload.upload_id == upload_id
    return g.db_session.query(models.ChunkedUpload).filter(clause).first()


# The _make_response function gets the as_json decorator because its the one we
# rely on to build the JSON reply, although the chunked_upload call may want to
# override the HTTP status code in some code paths.
@decorators.as_json
def _make_response(db_upload):
    return {
        'expires': display.human_timestamp(db_upload.expires),
        'offset': db_upload.offset,
        'upload_id': db_upload.upload_id,
    }


def _purge_expired_uploads():
    clause = models.ChunkedUpload.expires < datetime.datetime.utcnow()
    expired_items = g.db_session.query(models.ChunkedUpload).filter(clause)
    for expired_upload in expired_items.all():
        file_store.remove_chunked_upload(expired_upload.upload_id or '')
    expired_items.delete()
    g.db_session.commit()


def _start_new_upload():
    expires = _compute_expire_date()
    obj = models.ChunkedUpload(expires=expires, offset=0, owner=g.user.dbuser)
    g.db_session.add(obj)
    g.db_session.commit()

    # Now that the object is persisted in the database, we use its primary key
    # as the upload_id (using its SHA1).
    obj.upload_id = hashlib.sha1(str(obj.id)).hexdigest()
    return obj


@app.route('/chunked_upload', methods=['PUT'])
@login_required
def chunked_upload():
    # An offset without an upload_id doesn't mean anything.
    offset = request.args.get('offset', 0, type=int)
    upload_id = request.args.get('upload_id', '')

    # Start by purging the table of all expired uploads.
    _purge_expired_uploads()

    # A request without an upload_id is a new upload and should be registered
    # as such.
    if not upload_id:
        obj = _start_new_upload()
    else:
        # A missing object for /chunked_upload gives a 404.
        obj = _find_existing_upload(upload_id)
        if not obj:
            raise BasicError(404, 'Unknown upload_id {0}'.format(upload_id))

    # Either it's a new upload, or a previously existing one, but in both case
    # we expect the offset to match our expected values. The response contains
    # the regular JSON data (containing our expected offset) but with a 400.
    if offset != obj.offset:
        return _make_response(obj), 400

    # We call our storage strategy to append the received data to previously
    # received chunks.
    data_stream = request.stream or request.data
    obj.offset = file_store.register_chunk(obj.upload_id, data_stream)
    g.db_session.commit()
    return _make_response(obj)


@app.route('/commit_chunked_upload/<storage_node:root>/<path:path_>',
           methods=['POST'])
@login_required
@decorators.api_endpoint
def commit_chunked_upload(root, path_):
    tools.validate_root_or_abort(root)

    # A missing object for /commit_chunked_upload gives a 400.
    upload_id = request.form['upload_id']
    db_upload = _find_existing_upload(upload_id)
    if not db_upload:
        raise BasicError(400, 'Unknown upload_id {0}'.format(upload_id))

    # Start by purging the table of all expired uploads.
    _purge_expired_uploads()

    # We retrieve a file-like object to the uploaded data, and use this as an
    # input stream to a regular file upload request.
    data_stream = file_store.retrieve_chunk_stream(upload_id)

    # Install a SHA1 hash calculating stream on the request. This will
    # allow us to compute the file's hash as it is written to disk.
    crypt_key = g.user.dbuser.password[:32]
    enc_stream = stream.AESEncryptionStream(data_stream, crypt_key)
    hash_stream = stream.ChecksumCalcStream(enc_stream)
    put_result = put.do_put(root, path_, hash_stream, hash_stream.hash,
                            enc_stream.IV)

    # Close the input stream.
    data_stream.close()

    # Delete the temporary upload file.
    file_store.remove_chunked_upload(upload_id)

    # If we got here, it means that the storage is successful and the database
    # object can now be safely deleted.
    g.db_session.delete(db_upload)
    g.db_session.commit()
    return put_result
