import itertools
import json

from flask import request
from flask.ext.login import login_required

from datastore.api import app, tools
from datastore.api.errors import *
from datastore.api.files import metadata
from datastore.api.helpers import database
from datastore import models


@app.route('/revisions/<storage_node:root>/<path:path_>', methods=['GET'])
@login_required
def files_revisions(root, path_):
    tools.validate_root_or_abort(root)

    try:
        stored_object = database.get_stored_object(root, path_)
    except database.MissingNodeException:
        raise BasicError(404, E_FILE_NOT_FOUND)
    else:
        if not isinstance(stored_object, models.BlobLink):
            raise BasicError(404, E_FILE_NOT_FOUND)

    # Maximum number of file revision to fetch (up to 1000).
    rev_limit = int(request.args.get('rev_limit', '10'))
    if not (0 < rev_limit <= 1000):
        raise BasicError(406, E_REV_LIMIT(0, 1000))

    def _revisions(stored_object):
        while stored_object:
            yield stored_object
            stored_object = stored_object.parent

    # Remark: we cannot use flask.jsonify here (through our usual api_endpoint
    # decorator), see http://flask.pocoo.org/docs/security/#json-security.
    return json.dumps([
        metadata.make_metadata(root, path_, obj)
        for obj in itertools.islice(_revisions(stored_object), rev_limit)
    ]), 200, {'content-type': 'application/json'}
