import json
import os.path

from flask import request
from flask.ext.login import login_required

from datastore.api import app, tools
from datastore.api.errors import *
from datastore.api.files import metadata
from datastore.api.helpers import database
from datastore.api.tools import get_boolean_arg
from datastore import models


def _gen_metadata(obj, root, path, query, **kwargs):
    accept = lambda o: kwargs.get('include_deleted', False) or not o.is_deleted
    if query in obj.path and accept(obj):
        yield metadata.make_metadata(root, path, obj, **kwargs)
    for _, subd in sorted(obj.tree.sub_trees.items()):
        sub_path = os.path.join(path, subd.path)
        for m in _gen_metadata(subd, root, sub_path, query, **kwargs):
            yield m
    for _, subf in sorted(obj.tree.sub_files.items()):
        if query in subf.path and accept(subf):
            sub_path = os.path.join(path, subf.path)
            yield metadata.make_metadata(root, sub_path, subf, **kwargs)


@app.route('/search/<storage_node:root>/<path:path_>')
@app.route('/search/<storage_node:root>/', defaults={'path_': ''})
@login_required
def files_search(root, path_):
    tools.validate_root_or_abort(root)

    # First step is to verify that we have a valid query in the request, there
    # is no need to go further and query the DB if this condition is not met.
    query = request.args['query']
    if len(query) < 3:
        raise BasicError(400, E_QUERY_LEN(3))

    # Find the root for the search, identified by the provided path.
    try:
        stored_object = database.get_stored_object(root, path_)
    except database.MissingNodeException:
        raise BasicError(404, E_SEARCH_DIR_NOT_FOUND)
    else:
        if not isinstance(stored_object, models.TreeLink):
            raise BasicError(404, E_SEARCH_PATH_NOT_A_DIR)

    # Maximum number of results to fetch (up to 1000).
    file_limit = int(request.args.get('file_limit', '1000'))
    if not (0 < file_limit <= 1000):
        raise BasicError(406, E_FILE_LIMIT(0, 1000))

    # We handle the same URL parameters as the metadata call, although we
    # explicitely disable listing.
    kwargs = {
        'list': False,
        'include_deleted': get_boolean_arg(request.args, 'include_deleted')
    }

    # Remark: we cannot use flask.jsonify here (through our usual api_endpoint
    # decorator), see http://flask.pocoo.org/docs/security/#json-security.
    return json.dumps([
        m for m in _gen_metadata(stored_object, root, path_, query, **kwargs)
    ]), 200, {'content-type': 'application/json'}

files_search.methods = ['GET']
