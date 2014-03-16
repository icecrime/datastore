import itertools
import os.path

from flask import g, request
from flask.ext.login import login_required

from datastore.api import app, file_store, tools
from datastore.api.errors import *
from datastore.api.files import metadata
from datastore.api.helpers import database, decorators, stream
from datastore import models


def _find_or_create_blob(filehash, encryption_iv):
    # Check if we already hold the provided file, or create a new Blob object
    # as necessary.
    tabl = g.db_session.query(models.Blob)
    blob = tabl.filter(models.Blob.hash == filehash).first()
    if not blob:
        blob = models.Blob(hash=filehash, iv=encryption_iv)
    return blob


def _get_url_params():
    params = {}
    if 'overwrite' in request.args:
        params['overwrite'] = tools.get_boolean_arg(request.args, 'overwrite')
    if 'parent_rev' in request.args:
        params['parent_rev'] = request.args['parent_rev']
    return params


def _handle_conflict(directory, filename, **kwargs):
    overwrite = kwargs.get('overwrite', True)
    parent_rev = kwargs.get('parent_rev', '')

    # Step 1: create conflicted copy when a bad revision is being edited. Note
    # that When creating a conflicted copy, we always set overwrite to False
    # because it would make it transparent to overwrite previous copies.
    if not directory.sub_files[filename].hash.startswith(parent_rev):
        overwrite = False
        filename = _make_new_filename(filename, 'conflicted copy')

    # Step 2: append a unique index if the (potentially conflicted) filename is
    # already taken.
    if filename in directory.sub_files and not overwrite:
        filename = _make_unique_filename(filename, directory)
    return filename


def _make_new_filename(original, append_str):
    name, ext = os.path.splitext(original)
    return '{0} ({1}){2}'.format(name, append_str, ext)


def _make_unique_filename(original, directory):
    for index in itertools.count(1):
        attempt = _make_new_filename(original, index)
        if attempt not in directory.sub_files:
            return attempt


def do_put(root, path_, stream, hasher, encryption_iv):
    # A file operation is always traduced by a new Commit object in order to
    # track the changes. If copying fails because of an incomplete source
    # hierarchy we abort with a 404.
    try:
        commit = database.create_commit(root)
        ref_node, new_node = database.copy_hierarchy(root, path_, commit.root)
    except database.MissingNodeException:
        raise BasicError(404, E_NON_EXISTING_DESTINATION_PATH)

    # Handle the case where the file already exists. In the general case, if
    # the filename already exists and that 'overwrite' is set to False, we put
    # to a new filename such that 'test.txt' becomes 'test (1).txt'. Also, when
    # a content is put to an older revision (identified by 'parent_rev'), then
    # the filename 'test.txt' becomes 'test (conflicted copy).txt'.
    split_pt = tools.split_path(path_)
    filename = split_pt[-1]

    # It is an error to post a file named like an (non deleted) directory.
    existing_dir = ref_node.sub_trees.get(filename)
    if existing_dir and not existing_dir.is_deleted:
        raise BasicError(403, E_DIR_ALREADY_EXISTS)

    if filename in ref_node.sub_files:
        filename = _handle_conflict(ref_node, filename, **_get_url_params())
        path_ = '/'.join(['/'.join(split_pt[:-1]), filename])

    # We start by storing the provided content, and then we try and make the
    # database structure reflect the requested change.
    filehash = file_store.register_blob(root, path_, stream, hasher)
    fileblob = _find_or_create_blob(filehash, encryption_iv)

    # Update the blob entry if it's actually different from the previous one,
    # and commit to the database. Considering that the on disk blobs are
    # encrypted with a randomly generated IV, this is more than unlikely.
    old_blob = ref_node and ref_node.sub_files.get(filename)
    if old_blob and (old_blob.hash == fileblob.hash):  # pragma: no cover
        output = old_blob
        old_blob.is_deleted = False  # Restore the file if it was deleted
    else:
        output = models.BlobLink(blob=fileblob, path=filename, parent=old_blob)
        new_node.sub_files[filename] = output
        database.store_commit(root, commit)
    return metadata.make_metadata(root, path_, output)


@app.route('/files/<storage_node:root>/<path:path_>', methods=['PUT', 'POST'])
@login_required
@decorators.api_endpoint
def files_put(root, path_):
    tools.validate_root_or_abort(root)

    # Install a AES256 encrypting stream on the request. All the posted data
    # will be encrypted on the fly as it is read. A specific IV will be
    # generated in the process and inserted to the database later on. We use
    # the user's hashed password as encryption key: if a user believes if was
    # compromised and changes his password, all the files are made unusable.
    crypt_key = g.user.dbuser.password[:32]
    enc_stream = stream.install_stream(stream.AESEncryptionStream, crypt_key)

    # Install a SHA1 hash calculating stream on the request. This will allow us
    # to compute the file's hash as it is written to disk.
    hash_stream = stream.install_stream(stream.ChecksumCalcStream)

    data_stream = request.stream or request.data
    return do_put(root, path_, data_stream, hash_stream.hash, enc_stream.IV)
