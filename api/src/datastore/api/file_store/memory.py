"""Memory file storage: helpful for unit tests.
"""

import cStringIO
from datetime import datetime

from datastore.api import config


# Use a simple memory dictionary as a store.
store = {}


def initialize():
    pass


def register_blob(root, path, stream, hasher):
    content_data = stream.read()
    content_hash = hasher.hexdigest()
    store.setdefault(root, {})[content_hash] = (datetime.now(), content_data)
    return content_hash


def register_chunk(upload_id, stream):
    storage_root = config.chunk_storage
    content_data = stream.read()
    data = store.setdefault(storage_root, {}).setdefault(upload_id, (0, b''))
    store[storage_root][upload_id] = (0, data[1] + content_data)
    return len(data[1]) + len(content_data)


def remove_chunked_upload(upload_id):
    storage_root = config.chunk_storage
    del store[storage_root][upload_id]


def retrieve_blob_stream(root, content_hash):
    """Returns data as a file-like object."""
    stored_data = store.get(root, {}).get(content_hash)
    return cStringIO.StringIO(stored_data[1]) if stored_data else None


def retrieve_chunk_stream(upload_id):
    """Returns data as a file-like object."""
    return retrieve_blob_stream(config.chunk_storage, upload_id)


def stat_blob(root, path, content_hash):
    stored_data = store.get(root, {}).get(content_hash)
    if not stored_data:
        return None, None
    return (stored_data[0], len(stored_data[1]))
