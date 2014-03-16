import base64
from datetime import datetime, timedelta
import hashlib

from flask import g, request, url_for
from flask.ext.login import login_required

from sqlalchemy.sql.expression import and_

from datastore.api import app, tools
from datastore.api.errors import *
from datastore.api.helpers import database, decorators, display
from datastore import models


def _create_blob_ref(root, path, obj):
    ref = models.BlobRef(key=_make_file_ref(obj), root=root, path=path,
                         blob=obj, owner=g.user.dbuser)
    g.db_session.add(ref)
    return ref


def _find_ref_by_key(key):
    res = g.db_session.query(models.BlobRef).filter(models.BlobRef.key == key)
    if g.user.is_authenticated():
        res.filter(models.BlobRef.owner_id == g.user.dbuser.id)
    return res.first()


def _make_file_ref(obj):
    sha1 = hashlib.sha1()
    sha1.update(obj.hash)
    sha1.update(g.user.dbuser.email)
    return base64.urlsafe_b64encode(sha1.digest())


def _purge_expired_links():
    clause = models.BlobRef.expires < datetime.utcnow()
    expired_items = g.db_session.query(models.BlobRef).filter(clause)
    expired_items.delete()
    g.db_session.commit()


def find_obj_ref(obj):
    clause = models.BlobRef.blob_id == obj.id
    if g.user.is_authenticated():
        clause = and_(clause, models.BlobRef.owner_id == g.user.dbuser.id)
    return g.db_session.query(models.BlobRef).filter(clause).first()


def make_link_data(db_ref):
    return {
        'key': db_ref.key,
        'link': url_for('files_get_key', key=db_ref.key),
        'metadata': url_for('files_metadata_key', key=db_ref.key),
        'expires': display.human_timestamp(db_ref.expires),
    }


def retrieve_ref(key):
    db_ref = _find_ref_by_key(key)
    if not db_ref:
        raise BasicError(404, '{0} "{1}"'.format(E_INVALID_LINK, key))
    if datetime.utcnow() > db_ref.expires:
        raise BasicError(404, '{0} "{1}"'.format(E_INVALID_LINK, key))
    return db_ref


@app.route('/shares/<key>', methods=['DELETE'])
@login_required
@decorators.api_endpoint
def files_remove_shares(key):
    g.db_session.delete(retrieve_ref(key))
    g.db_session.commit()
    return {'result': 'OK'}


@app.route('/shares/<storage_node:root>/<path:path_>', methods=['POST'])
@login_required
@decorators.api_endpoint
def files_shares(root, path_):
    tools.validate_root_or_abort(root)

    try:
        stored_object = database.get_stored_object(root, path_)
    except database.MissingNodeException:
        raise BasicError(404, E_FILE_NOT_FOUND)
    else:
        if not stored_object or type(stored_object) != models.BlobLink:
            raise BasicError(404, E_FILE_NOT_FOUND)

    # Start by purging the table of all expired uploads.
    _purge_expired_links()

    # If we already have a reference to this file, no need to recreate one.
    db_ref = _find_ref_by_key(_make_file_ref(stored_object))
    if not db_ref:
        db_ref = _create_blob_ref(root, path_, stored_object)

    # Number of days to expiration.
    expire_days = int(request.args.get('expire_days', '1'))
    if not (0 < expire_days <= 10000):
        raise BasicError(406, E_EXPIRE_DAYS(0, 10000))

    # Regardless of the fact that the reference previously existed, its expiry
    # is reset.
    db_ref.blob = stored_object
    db_ref.expires = datetime.utcnow() + timedelta(days=expire_days)
    g.db_session.commit()

    # Return the reference for this file, used for retrieval.
    return make_link_data(db_ref)
