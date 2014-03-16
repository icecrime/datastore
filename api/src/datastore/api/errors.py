from functools import partial

from flask import jsonify


class Error(Exception):
    """Base class for API exceptions."""
    def format_response(self):  # pragma: no cover
        raise NotImplementedError("Exceptions should implement this!")


class BasicError(Error):
    def __init__(self, status_code, message):
        self.message = message
        self.status_code = status_code

    def format_response(self):
        body = {'status_code': self.status_code, 'message': self.message}
        response = jsonify(body)
        response.status_code = self.status_code
        return response


###############################################################################


INVALID_OP = 'Invalid operation: '
INVALID_RANGE = lambda f, l, h: '"%s" must be between %d and %d' % (f, l, h)

E_ALREADY_DELETED = INVALID_OP + 'file already deleted'
E_BAD_DESTINATION = INVALID_OP + 'bad destination path'
E_CPY_BAD_PATHS = INVALID_OP + 'bad paths provided'
E_DEST_EXISTS = INVALID_OP + 'destination already exists'
E_DEST_DOES_NOT_EXIST = INVALID_OP + 'destination does not exist'
E_DIR_ALREADY_EXISTS = INVALID_OP + 'a directory with that name already exists'
E_FILE_NOT_FOUND = INVALID_OP + 'file not found'
E_EXPIRE_DAYS = partial(INVALID_RANGE, 'expire_days')
E_FILE_LIMIT = partial(INVALID_RANGE, 'file_limit')
E_INVALID_LINK = lambda d: 'Invalid file link "{0}"'.format(d)
E_INVALID_PATH = lambda d: 'Invalid path "{0}"'.format(d)
E_INVALID_ROOT = lambda d: 'Invalid root "{0}"'.format(d)
E_NON_EXISTING_DESTINATION_PATH = 'Non existing destination path'
E_QUERY_LEN = lambda l: '"query" must be at least %d characters long' % l
E_REV_LIMIT = partial(INVALID_RANGE, 'rev_limit')
E_SEARCH_DIR_NOT_FOUND = 'Search directory not found'
E_SEARCH_PATH_NOT_A_DIR = 'Search path is not a directory'
E_SOURCE_NOT_FOUND = 'Source file was not found'
E_SOURCE_DELETED = 'Source file has been deleted'
