class User(object):

    """Models a User object, to be used by Flask-Login. Wraps an underlying
    database user.
    """

    def __init__(self, dbuser):
        self.dbuser = dbuser

    def get_id(self):
        # Returns a unicode that uniquely identifies this user, and can be used
        # to load the user from the user_loader callback
        return unicode(self.dbuser.email)

    def is_authenticated(self):
        return True

    def is_active(self):
        """Always return true: there is no notion of 'active' for a database
        user. However, there will be for a LDAP / AD authenticated user.
        """
        return True

    def is_anonymous(self):
        return False
