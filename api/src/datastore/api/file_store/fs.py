"""Filesystem file storage: the default implementation.

We implement a git-like storage model:
    - Content SHA1 hex digest gives us the identity of the file
    - The first two bytes gives us the storage directory
    - The rest of the digest gives us the storage filename.

"""

import os
import tempfile

from flask import safe_join
from werkzeug import FileStorage

from datastore.api import config, tools


storage_root = os.path.abspath(config.storage['fs_root'])


def _make_storage_key(root, content_hash):
    filepath = safe_join(storage_root, root)
    filepath = safe_join(filepath, content_hash[:2])
    filepath = safe_join(filepath, content_hash[2:])
    return filepath


def _save_request_content(destination, stream):
    file_storage = FileStorage(stream)
    file_storage.save(destination)


def initialize():
    tools.make_dirs(storage_root)
    for storage_node in config.storage_nodes:
        tools.make_dirs(os.path.join(storage_root, storage_node))
    tools.make_dirs(os.path.join(storage_root, config.chunk_storage))


def register_blob(root, path, stream, hasher):
    # Store the data to a temporary file. Reading the stream triggers the
    # checksum calculation.
    with tempfile.NamedTemporaryFile() as temp_file:
        _save_request_content(temp_file, stream)

        # Now the data has been read and the checksum computed accordingly, the
        # file may be moved to its final location (based on its hash).
        filepath = _make_storage_key(root, hasher.hexdigest())

        # If the file already exists, there is no need to go further (assuming
        # that SHA1 collisions are out of the picture).
        if not os.path.exists(filepath):
            tools.make_dirs(os.path.dirname(filepath))
            os.rename(temp_file.name, filepath)
            temp_file.delete = False

    return hasher.hexdigest()


def register_chunk(upload_id, content):
    # Computing the sha1 upon retrieval is useless, because it is the final
    # hash that matters, not the hash of the different chunks.
    filepath = _make_storage_key(config.chunk_storage, upload_id)

    # Save the chunk to a file which path depends on the generated upload_id.
    tools.make_dirs(os.path.dirname(filepath))
    with open(filepath, 'ab+') as upload_file:
        _save_request_content(upload_file, content)
        return upload_file.tell()


def remove_chunked_upload(upload_id):
    # Aborting a chunked upload consists of removing any temporary file that
    # may have been created.
    filepath = _make_storage_key(config.chunk_storage, upload_id)
    try:
        os.remove(filepath)
    except OSError:  # pragma: no cover
        pass  # Silently ignore any removal error


def retrieve_blob_stream(root, content_hash):
    """Returns data as a file-like object."""
    filepath = _make_storage_key(root, content_hash)
    return open(filepath, 'rb')


def retrieve_chunk_stream(upload_id):
    """Returns data as a file-like object."""
    return retrieve_blob_stream(config.chunk_storage, upload_id)


def stat_blob(root, path, content_hash):
    filepath = _make_storage_key(root, content_hash)
    try:
        fileinfo = os.stat(filepath)
    except OSError:
        return None, None
    return fileinfo.st_mtime, fileinfo.st_size
