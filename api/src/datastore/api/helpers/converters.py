from werkzeug.exceptions import Forbidden
from werkzeug.routing import PathConverter, UnicodeConverter

from datastore.api import tools
from datastore.api.errors import BasicError


class BadNodeException(Forbidden):

    def __init__(self, root):
        self.root = root

    def get_response(self, environ):
        try:
            tools.validate_root_or_abort(self.root)
        except BasicError, e:
            return e.format_response()


class InvalidPathException(Forbidden):

    def __init__(self, path):
        self.path = path

    def get_response(self, environ):
        try:
            tools.validate_path_or_abort(self.path)
        except BasicError, e:
            return e.format_response()


class StorageNodeConverter(UnicodeConverter):

    """The StorageNodeConverter ensures that the provided storage node is part
    of the configured list.
    """

    def to_python(self, value):
        if not tools.is_valid_root(value):
            raise BadNodeException(value)
        return super(UnicodeConverter, self).to_python(value)


class FiledepotPathConverter(PathConverter):

    """The FiledepotPathConverter replaces the standard werkzeug one, altough
    it reuses its implementation.

    The idea here is to detected invalid paths by searching for any . or .. at
    any path element.
    """

    def to_python(self, value):
        if not tools.is_valid_path(value):
            raise InvalidPathException(value)
        return super(PathConverter, self).to_python(value)


converters_map = {
    'path': FiledepotPathConverter,
    'storage_node': StorageNodeConverter,
}
