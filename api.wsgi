import os
import os.path


DATASTORE_API_ROOT = '/var/www/api.datastore.fr'

# Activate virtual environment for this application
activate_this = os.path.join(DATASTORE_API_ROOT, '.env/bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

# Pick the appropriate configuration file with an environment variable.
os.environ['DATASTORE_API_CONFIG_FILE'] = 'config_prod.yaml'
os.environ['DATASTORE_API_CONFIG_PATH'] = os.path.join(DATASTORE_API_ROOT, 'api/conf/')

# Import the application
from datastore.api import app as application
