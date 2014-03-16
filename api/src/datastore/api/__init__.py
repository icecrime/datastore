from flask import Flask, g
from flask.ext.login import current_user, LoginManager

from datastore.api import config, encryption, errors, file_store, user_store
from datastore.api.helpers import converters, session
from datastore.models import session_maker


# Setup Flask app
app = Flask(__name__)
app.config.update(config.api)
app.url_map.converters.update(converters.converters_map)

# Replace the default session management
app.session_interface = session.ItsdangerousSessionInterface()


# Database session factory
def create_session_factory():
    return session_maker(config.database, config.database_options)
Session = create_session_factory()


@app.before_request
def before_request():
    g.user = current_user
    g.db_session = Session()


@app.teardown_request
def teardown_request(exception):
    Session.remove()


@app.errorhandler(errors.BasicError)
def datastore_exception_handler(error):
    return error.format_response()


# Setup Flask-Login and import the appropriate login backend based on the
# login_backend configuration key (must provide the user loader and any
# specific view function.
#
# /!\ Must be created _after_ setting up the flask request hooks, or the user
# loader will be called without a db session initialized.
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = 'strong'

# Setup file storage, login storage, and password encryption backends.
encryption = encryption.from_config(app, config)
file_store = file_store.from_config(app, config)
user_store = user_store.from_config(app, config)

# Initialize the file store.
file_store.initialize()


# Import view modules
import datastore.api.users
import datastore.api.files
import datastore.api.fileops
