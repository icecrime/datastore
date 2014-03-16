import functools
import hashlib
import mimetypes
import urllib2

from flask import request, Response
from flask.ext.login import login_required

from datastore.api import app, file_store, tools
from datastore.api.errors import *
from datastore.api.files import shares
from datastore.api.helpers import database, decorators, display
from datastore import models


# We restrict the size of our SHA1 hashes considering the likelyness of a
# conflict, and the fact that our revisions aren't used for much anyway.
hash_size = 20


def _append(path_, char='/'):
    return path_ if path_.endswith(char) else path_ + char


def _prepend(path_, char='/'):
    return path_ if path_.startswith(char) else char + path_


def _get_url_params():
    fn = functools.partial(tools.get_boolean_arg, request.args)
    url_params = ('list', 'include_links', 'include_deleted')
    return dict((k, fn(k)) for k in url_params if k in request.args)


def _make_dir_content(root, path_, tree, **kwargs):
    # Each directory listing contains a hash value which helps the client
    # determine if anything has changed. This hash takes into account:
    #   - each sub directory name and deleted status
    #   - each sub file name, deleted status and hash.
    #
    # As a result, the hash will change only if any top level element changes,
    # without taking sub directories content into account.
    hash_ = hashlib.sha1()
    path_ = _append(path_)
    accept = lambda o: kwargs.get('include_deleted', False) or not o.is_deleted

    def _gen_md(collection):
        for _, obj in sorted(collection.items()):
            hash_.update(_object_hash(obj))
            if accept(obj):
                yield make_metadata(root, path_ + obj.path, obj, **kwargs)

    content = [m for c in [tree.sub_trees, tree.sub_files] for m in _gen_md(c)]
    return content, hash_.hexdigest()[:hash_size]


def _make_base_metadata(root, path_, obj):
    metadata = {
        'path': _prepend(path_),
        'root': root,
    }
    if obj.is_deleted:
        metadata['is_deleted'] = True
    return metadata


def _make_dir_metadata(root, path_, tree_link, **kwargs):
    tree = tree_link.tree

    # Build and return the metadata dictionary.
    metadata = _make_base_metadata(root, path_.rstrip('/'), tree_link)
    metadata.update({
        'bytes': 0,
        'is_dir': True,
        'modified': display.human_timestamp(tree.created),
        'rev': _make_tree_rev(tree)[:hash_size],
        'size': display.human_size(0),
    })

    # Handle the (default) list mode, where a 'contents' sub-entry contains the
    # metadatas for each file in the directory.
    if kwargs.get('list', True):
        options = kwargs.copy()
        options['list'] = False  # Don't list recursively
        contents, hash_ = _make_dir_content(root, path_, tree, **options)
        metadata.update(hash=hash_, contents=contents)
    return metadata


def _make_file_metadata(root, path_, blob, **kwargs):
    # Retrieve the blob statistics from the file_store.
    file_date, file_size = file_store.stat_blob(root, path_, blob.hash)

    # Build and return the metadata dictionary.
    metadata = _make_base_metadata(root, path_, blob)
    metadata.update({
        'bytes': file_size,
        'is_dir': False,
        'modified': display.human_timestamp(file_date or 0),
        'rev': blob.hash[:hash_size],
        'size': display.human_size(file_size or 0),
    })

    # Try to deduce a mime type from the filename.
    mime_type, _ = mimetypes.guess_type(path_)
    if mime_type:
        metadata['mime_type'] = mime_type

    # Fetch the associated link information if requested.
    if kwargs.get('include_links', False):
        db_ref = shares.find_obj_ref(blob)
        if db_ref:
            metadata['link'] = shares.make_link_data(db_ref)
    return metadata


def _make_tree_rev(tree):
    return hashlib.sha1(str(tree.id)).hexdigest()


def _object_hash(obj):
    hash_str = ''
    if isinstance(obj, models.TreeLink):
        hash_str = str((obj.path, obj.is_deleted))
    elif isinstance(obj, models.BlobLink):
        hash_str = str((obj.path, obj.is_deleted, obj.blob.hash))
    return hash_str


def make_metadata(root, path_, obj, **kwargs):
    # Retrieve the stored object and send the metadata depending on its type,
    # which can either be a Tree or a BlobLink.
    metadata = None
    if isinstance(obj, models.TreeLink):
        metadata = _make_dir_metadata(root, path_, obj, **kwargs)
    elif isinstance(obj, models.BlobLink):
        metadata = _make_file_metadata(root, path_, obj, **kwargs)
    return metadata or {}


@app.route('/metadata/<storage_node:root>/<path:path_>')
@app.route('/metadata/<storage_node:root>/', defaults={'path_': ''})
@login_required
def files_metadata(root, path_):
    tools.validate_root_or_abort(root)

    try:
        stored_object = database.get_stored_object(root, path_)
    except database.MissingNodeException:
        raise BasicError(404, E_FILE_NOT_FOUND)

    # If the client has provided a hash value and it compares equal to the one
    # we have just generated, return a 304 (Not Modified).
    params = _get_url_params()
    metadata = make_metadata(root, path_, stored_object, **params)
    if request.args.get('hash') == metadata.get('hash', ''):
        return Response(status=304)

    # Little hack here: we cannot decorate files_metadata function as an json
    # api endpoint because it may return a 304 without data. We use this tiny
    # internal decorated function to the job when there is data to return.
    @decorators.api_endpoint
    def _json_metadata_return(metadata):
        return metadata
    return _json_metadata_return(metadata)

files_metadata.methods = ['GET']


@app.route('/metadata', methods=['GET'])
@decorators.api_endpoint
def files_metadata_key():
    params = _get_url_params()
    db_ref = shares.retrieve_ref(urllib2.unquote(request.args['key']))
    return make_metadata(db_ref.root, db_ref.path, db_ref.blob, **params)
