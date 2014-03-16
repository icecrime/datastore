from flask import request
from flask.ext.login import login_required

from datastore.api import app, tools
from datastore.api.errors import *
from datastore.api.files import metadata
from datastore.api.helpers import database, decorators
from datastore import models


def _copy_err(*args, **kwargs):  # pragma: no cover
    raise BasicError(500, 'Unexpected object type for copy')


def _copy_dir(obj, tree, dst_path):
    # Source path is a TreeLink: create a new TreeLink pointing of the same
    # sub hierarchy but for the new path.
    output = models.TreeLink(tree=obj.tree, path=dst_path)
    tree.sub_trees[dst_path] = output
    return output

def _copy_file(obj, tree, dst_path):
    # Source path is a BlobLink: create a new BlobLink pointing on the same
    # blob object but for the new path.
    output = models.BlobLink(blob=obj.blob, path=dst_path)
    tree.sub_files[dst_path] = output
    return output


def _get_params():
    items = tools.get_params(request.form, 'root', 'from_path', 'to_path')
    tools.validate_root_or_abort(items[0])
    tools.validate_path_or_abort(items[1])
    tools.validate_path_or_abort(items[2])
    return items


def _get_source_object(root, from_path, target_node):
    try:
        source = database.get_stored_object(root, from_path, target_node)
    except database.MissingNodeException:
        raise BasicError(404, E_SOURCE_NOT_FOUND)
    if source.is_deleted:
        raise BasicError(404, E_SOURCE_DELETED)
    return source


def _validate_paths(root, from_path, to_path, target_node):
    # The source path should not be a parent of the destination.
    p_to = tools.split_path(to_path)
    p_from = tools.split_path(from_path)
    if not (p_to and p_from) or (p_from == p_to[:len(p_from)]):
        raise BasicError(403, E_CPY_BAD_PATHS)

    # Attempt to retrieve the parent directory for the destination file, and
    # fail with a 403 if it doesn't exist.
    try:
        obj = database.get_stored_object(root, '/'.join(p_to[:-1]))
    except database.MissingNodeException:
        raise BasicError(403, E_DEST_DOES_NOT_EXIST)

    # The destination path should start with an existing object, which type
    # must be a directory. The destination path should always end with a new
    # path element (copy cannot overwrite).
    is_directory = obj and (type(obj) == models.TreeLink)
    if not is_directory:
        raise BasicError(403, E_BAD_DESTINATION)

    # Attempt to retrieve the original item to copy.
    source = _get_source_object(root, from_path, target_node)
    source_is_dir = source and (type(source) == models.TreeLink)

    # We verify that there is no (undeleted) item at the destination path.
    target = obj.tree.sub_trees if source_is_dir else obj.tree.sub_files
    if p_to[-1] in target and not target[p_to[-1]].is_deleted:
        raise BasicError(403, E_DEST_EXISTS)


def copy_object(obj, tree, dst_path):
    # The actual copying depends on the object type.
    copy_fns = {models.TreeLink: _copy_dir, models.BlobLink: _copy_file}
    return copy_fns.get(type(obj), _copy_err)(obj, tree, dst_path)


def do_copy(target_node, root, from_path, to_path):
    _validate_paths(root, from_path, to_path, target_node)

    # We start by retrieving the original object to copy. If it exists but is
    # deleted, we raise a 404.
    obj = _get_source_object(root, from_path, target_node)

    # Do the copy and return both the original and the copy.
    _, new_node = database.copy_hierarchy(root, to_path, target_node)
    return obj, copy_object(obj, new_node, tools.last_element(to_path))


@app.route('/fileops/copy', methods=['POST'])
@login_required
@decorators.api_endpoint
def fileops_copy():
    root, from_path, to_path = _get_params()
    tools.validate_root_or_abort(root)

    # A copy operation is always traduced by a new Commit object in order to
    # track the changes.
    commit = database.create_commit(root)
    obj, obj_copy = do_copy(commit.root, root, from_path, to_path)

    # Store the commit, and return the metadata for the new object.
    database.store_commit(root, commit)
    return metadata.make_metadata(root, to_path, obj_copy)
