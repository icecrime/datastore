from flask import g, request
from flask.ext.login import login_required

from datastore.api import app, user_store
from datastore.api.helpers import decorators


def _make_account_info():
    return {
        'country': g.user.dbuser.country or '',
        'display_name': g.user.dbuser.display_name or '',
        'email': g.user.dbuser.email,
        'uid': g.user.dbuser.id,
    }


@app.route('/account/info', methods=['GET'])
@login_required
@decorators.api_endpoint
def account_info():
    return _make_account_info()


@app.route('/account/info', methods=['POST'])
@login_required
@decorators.api_endpoint
def update_account_info():
    user_store.update_user(request.form.copy())
    return _make_account_info()


@app.route('/login', methods=['POST'])
def login():
    user_store.login(request.form.copy())
    return account_info()


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    user_store.logout()
    return 'OK'
