from flask import request
from flask.ext.login import login_required

from datastore.api import app, tools
from datastore.api.errors import *
from datastore.api.files import metadata
from datastore.api.helpers import database, decorators
from datastore import models


def _get_params():
    # Root and path data are passed as POST data rather than URL args.
    root, path_ = tools.get_params(request.form, 'root', 'path')
    tools.validate_root_or_abort(root)
    tools.validate_path_or_abort(path_)
    return root, path_


def recursive_delete(obj):
    obj.is_deleted = True
    if type(obj) == models.TreeLink:
        for subf in obj.tree.sub_files.values():
            subf.is_deleted = True
        for subd in obj.tree.sub_trees.values():
            recursive_delete(subd)


@app.route('/fileops/delete', methods=['POST'])
@login_required
@decorators.api_endpoint
def fileops_delete():
    root, path_ = _get_params()
    tools.validate_root_or_abort(root)
    commit = database.create_commit(root)

    # Retrieve the stored object (could be a blob or tree link) or abort with
    # a 404 if we fail.
    try:
        stored_object = database.get_stored_object(root, path_, commit.root)
    except database.MissingNodeException:
        raise BasicError(404, E_FILE_NOT_FOUND)

    # Mark the database object as deleted if it's not already.
    if stored_object.is_deleted:
        raise BasicError(404, E_ALREADY_DELETED)

    # Recursively delete the object (if necessary), and commit the transaction.
    recursive_delete(stored_object)
    database.store_commit(root, commit)
    return metadata.make_metadata(root, path_, stored_object)
