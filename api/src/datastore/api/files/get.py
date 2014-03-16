import json
import urllib2

from flask import g, send_file
from flask.ext.login import login_required

from datastore.api import app, file_store, tools
from datastore.api.files import metadata, shares
from datastore.api.errors import *
from datastore.api.helpers import database
from datastore.api.helpers.stream import AESDecryptionStream


def _send_file(stream, path, metadata, encryption_iv):
    if not stream:
        raise BasicError(404, E_FILE_NOT_FOUND)

    # The file will be decrypted with the user's password as it is read.
    crypt_key = g.user.dbuser.password[:32]
    stream = AESDecryptionStream(stream, crypt_key, encryption_iv)

    filename = tools.split_path(path)[-1]
    response = send_file(stream, add_etags=False, as_attachment=True,
                         attachment_filename=filename)
    response.headers['x-datastore-metadata'] = json.dumps(metadata)
    return response


@app.route('/files/<storage_node:root>/<path:path_>', methods=['GET'])
@login_required
def files_get(root, path_):
    tools.validate_root_or_abort(root)

    # Attempt to retrieve the database representation of the requested file
    # from the database, and raise a 404 if we failed in doing so.
    try:
        dbobject = database.get_stored_object(root, path_)
    except database.MissingNodeException:
        raise BasicError(404, E_FILE_NOT_FOUND)

    # Request the actual disk object to the file_store, and send the result as
    # a file to the client.
    fmdata = metadata.make_metadata(root, path_, dbobject)
    stream = file_store.retrieve_blob_stream(root, dbobject.hash)
    return _send_file(stream, path_, fmdata, dbobject.iv)


@app.route('/files/<key>', methods=['GET'])
def files_get_key(key):
    db_ref = shares.retrieve_ref(urllib2.unquote(key))
    fmdata = metadata.make_metadata(db_ref.root, db_ref.path, db_ref.blob)
    stream = file_store.retrieve_blob_stream(db_ref.root, db_ref.blob.hash)
    return _send_file(stream, db_ref.path, fmdata, db_ref.blob.iv)
