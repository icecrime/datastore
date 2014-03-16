"""Storage package implements the different ways to handle file storage.

Possible implementations:
    - filesystem: store files on disk
    - memory: in memory storage, used for testing purposes

"""


def from_config(app, config):
    """Import the appropriate encryption module according to the config."""
    encryption = config.storage.get('backend', 'fs')
    return __import__('%s.%s' % (__name__, encryption), fromlist=[None])
