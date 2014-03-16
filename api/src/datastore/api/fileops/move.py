from flask import request
from flask.ext.login import login_required

from datastore.api import app, tools
from datastore.api.files import metadata
from datastore.api.fileops import copy, delete
from datastore.api.helpers import database as database, decorators


def _get_params():
    items = tools.get_params(request.form, 'root', 'from_path', 'to_path')
    tools.validate_root_or_abort(items[0])
    tools.validate_path_or_abort(items[1])
    tools.validate_path_or_abort(items[2])
    return items


@app.route('/fileops/move', methods=['POST'])
@login_required
@decorators.api_endpoint
def fileops_move():
    root, from_path, to_path = _get_params()
    tools.validate_root_or_abort(root)

    # Move is implemented in terms of copy.
    commit = database.create_commit(root)
    obj, obj_copy = copy.do_copy(commit.root, root, from_path, to_path)

    # Delete the source object.
    source = database.get_stored_object(root, from_path, commit.root)
    delete.recursive_delete(source)

    # Store the commit, and return the metadata for the new object.
    database.store_commit(root, commit)
    return metadata.make_metadata(root, to_path, obj_copy)
