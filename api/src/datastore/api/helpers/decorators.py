import functools

from flask import jsonify

from datastore.api import config


def as_json(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return jsonify(fn(*args, **kwargs))
    return wrapper


def api_header(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        result = fn(*args, **kwargs)
        result['api-version'] = '.'.join(str(i) for i in config.api_version)
        return result
    return wrapper


def api_endpoint(fn):
    return as_json(api_header(fn))
