"""Miscellaneous general purpose utilities.
"""

import os
import os.path

from datastore.api import config
from datastore.api.errors import *


def get_boolean_arg(args, var, default=False):
    values = ['false', 'true']
    urlval = args.get(var, values[default]).lower()
    if urlval not in values:
        raise BasicError(400, 'Bad value "{0}" for {1}'.format(urlval, var))
    return urlval == 'true'


def get_params(dic, *params):
    return [dic[param] for param in params]


def is_valid_path(path):
    if not path:
        return False
    path_elements = split_path(path)
    return not any(e in path_elements for e in ['.', '..'])


def is_valid_root(root):
    return root in config.storage_nodes


def last_element(path):
    split = split_path(path)
    return None if not split else split[-1]


def make_dirs(path):
    try:
        os.makedirs(path)
    except:
        if not os.path.exists(path):  # pragma: no cover
            raise


def split_path(path):
    directory_list = []
    while path and (path != '/'):
        path, tail = os.path.split(path)
        if tail:
            directory_list.append(tail)
    directory_list.reverse()
    return directory_list


def validate_path_or_abort(path, status_code=403):
    if not is_valid_path(path):
        raise BasicError(403, E_INVALID_PATH(path))


def validate_root_or_abort(root, status_code=403):
    if not is_valid_root(root):
        raise BasicError(403, E_INVALID_ROOT(root))
