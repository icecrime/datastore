from flask import g, request

from sqlalchemy.exc import IntegrityError

from datastore.api import app, config, encryption
from datastore.api.errors import BasicError
from datastore.models import Commit, Node, Tree, User


@app.route('/users', methods=['POST'])
def create_user():
    """Create a database user with the provided information."""
    hashed_password, salt = encryption.hash_password(request.form['password'])
    user = User(
        email=request.form['email'],
        password=hashed_password,
        salt=salt
    )

    for storage_node in config.storage_nodes:
        head = Commit(root=Tree())
        user.nodes[storage_node] = Node(path=storage_node, head=head)

    # Register the user into the database.
    try:
        g.db_session.add(user)
        g.db_session.commit()
    except IntegrityError:
        raise BasicError(409, '"{0}" is already registed'.format(user.email))
    return 'OK'
