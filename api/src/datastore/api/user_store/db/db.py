from flask import g
from flask.ext.login import login_user, logout_user

from datastore.api import encryption, login_manager
from datastore.api.errors import BasicError
from datastore.api.helpers import auth
from datastore import models


@login_manager.user_loader
def load_user(email):
    """Flask-Login user loader implementation: fetch the user is the database
    from its primary key.
    """
    clause = models.User.email == email
    db_user = g.db_session.query(models.User).filter(clause).first()
    return db_user and auth.User(db_user)


def login(form):
    """Verify email password against the values stored in database."""
    clause = models.User.email == form['email']
    dbuser = g.db_session.query(models.User).filter(clause).first()

    attempt = form['password']
    if not dbuser or not encryption.verify_password(dbuser.password,
                                                    dbuser.salt, attempt):
        raise BasicError(403, 'Bad login or password')
    login_user(auth.User(dbuser))


def logout():
    logout_user()


def update_user(form):
    # Extract each available editable field from the post data.
    make_pair = lambda f: (f, form.pop(f))
    editables = ['country', 'display_name', 'email']
    updateset = dict(make_pair(f) for f in editables if f in form)

    # If the password is part of the modified fields, we have to rehash it.
    new_password = form.pop('password', None)
    if new_password:
        hashed_password, salt = encryption.hash_password(new_password)
        updateset['salt'] = salt
        updateset['password'] = hashed_password

    # If there are any field specified which are not part of those that can be
    # edited, we abort. We also validate that the country is a digram.
    if form:
        message = 'Only the following fields can be updated: {0}'
        raise BasicError(400, message.format(', '.join(editables)))
    if len(updateset.get('country', '__')) != 2:
        message = 'Invalid country code "{0}"'
        raise BasicError(400, message.format(updateset['country']))

    # Update the user data and commit the changes.
    for field, value in updateset.items():
        setattr(g.user.dbuser, field, value)
    g.db_session.commit()
