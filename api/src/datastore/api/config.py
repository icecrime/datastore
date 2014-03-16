import os
import os.path

import yaml


# Pick the right configuration file based on the DATASTORE_API_CONFIG_PATH and
# DATASTORE_API_CONFIG_FILE environment variables.
config_path = os.environ.get('DATASTORE_API_CONFIG_PATH', 'api/conf/')
config_file = os.environ.get('DATASTORE_API_CONFIG_FILE', 'config.yaml')

# Inject the YAML configuration file describing database connection and stuff.
with open(os.path.join(config_path, config_file)) as f:
    locals().update(yaml.load(f))

# API version tag
api_version = (0, 0, 1)

# Server timezone
server_tz = 'Europe/Paris'

# Storage configuration
chunk_storage = '_chunked_uploads'
storage_nodes = ['main', 'sandbox']

# Storage policy regarding history (usefull if you want to revert any change
# have a sort of 'time-machine', but at the cost of performance)
enable_full_history = False
