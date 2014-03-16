from flask import request
from flask.ext.login import login_required

from datastore.api import app, tools
from datastore.api.errors import *
from datastore.api.files import metadata
from datastore.api.helpers import database, decorators
from datastore import models


@app.route('/fileops/create_folder', methods=['POST'])
@login_required
@decorators.api_endpoint
def fileops_createfolder():
    # Root and path data are passed as POST data rather than URL args.
    root = request.form['root']
    path_ = request.form['path']
    tools.validate_root_or_abort(root)
    tools.validate_path_or_abort(path_)

    # A file operation is always traduced by a new Commit object in order to
    # track the changes.
    try:
        commit = database.create_commit(root)
        ref_node, new_node = database.copy_hierarchy(root, path_, commit.root)
    except database.MissingNodeException:
        raise BasicError(404, E_NON_EXISTING_DESTINATION_PATH)

    # To stick with Dropbox behaviour, we raise a 403 if the directory already
    # exists.
    treename = tools.split_path(path_)[-1]
    existing = ref_node and ref_node.sub_trees.get(treename)
    if existing and not existing.is_deleted:
        raise BasicError(403, E_DIR_ALREADY_EXISTS)

    # Create the new directory and commit the change.
    output = models.TreeLink(tree=models.Tree(), path=treename)
    new_node.sub_trees[treename] = output
    database.store_commit(root, commit)
    return metadata.make_metadata(root, path_, output)
