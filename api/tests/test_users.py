import json

import tools

user_data = {
    'email': 'email',
    'password': 'password'
}


class UserManagementTestCase(tools.FiledepotTestCase):

    def test_create(self):
        rv = self.user.create(user_data)
        self.assertEqual(rv.data, 'OK')
        self.assertEqual(rv.status_code, 200)

    def test_get_user(self):
        rv = self.user.create(user_data)
        rv = self.user.login(user_data)
        rv = self.user.info()

        self.assertEqual(rv.status_code, 200)
        self.assertIn('uid', rv.json)
        self.assertIn('country', rv.json)
        self.assertIn('display_name', rv.json)
        self.assertEqual(rv.json['email'], user_data['email'])

    def test_login(self):
        rv = self.user.create(user_data)
        rv = self.user.login(user_data)
        self.assertEqual(rv.status_code, 200)

    def test_logout(self):
        rv = self.user.create(user_data)
        rv = self.user.login(user_data)
        rv = self.user.logout()
        self.assertEqual(rv.data, 'OK')
        self.assertEqual(rv.status_code, 200)

    def test_dup_create(self):
        rv = self.user.create(user_data)
        rv = self.user.create(user_data)
        self.assertEqual(rv.status_code, 409)

    def test_bad_get(self):
        rv = self.user.info()
        self.assertEqual(rv.status_code, 401)

    def test_bad_login__no_user(self):
        rv = self.user.login(user_data)
        self.assertEqual(rv.status_code, 403)

    def test_bad_login__wrong_password(self):
        borked_data = user_data.copy()
        borked_data['password'] = ''

        rv = self.user.create(user_data)
        rv = self.user.login(borked_data)
        self.assertEqual(rv.status_code, 403)

    def test_create_none(self):
        rv = self.user.create(None)
        self.assertEqual(rv.status_code, 400)

    def test_login_none(self):
        rv = self.user.login(None)
        self.assertEqual(rv.status_code, 400)

    def test_update(self):
        rv = self.user.create(user_data)
        rv = self.user.login(user_data)
        self.assertEqual(rv.status_code, 200)

        rv = self.user.update({'country': 'FR', 'display_name': 'name'})
        self.assertEqual(rv.status_code, 200)

        self.assertEqual(rv.json['country'], 'FR')
        self.assertEqual(rv.json['display_name'], 'name')
        self.assertEqual(rv.json['email'], user_data['email'])

    def test_update_bad_country(self):
        rv = self.user.create(user_data)
        rv = self.user.login(user_data)
        self.assertEqual(rv.status_code, 200)

        rv = self.user.update({'country': 'FRANCE'})
        self.assertEqual(rv.status_code, 400)

    def test_update_forbidden(self):
        rv = self.user.create(user_data)
        rv = self.user.login(user_data)
        self.assertEqual(rv.status_code, 200)

        rv = self.user.update({'uid': '5'})
        self.assertEqual(rv.status_code, 400)

    def test_update_password(self):
        rv = self.user.create(user_data)
        rv = self.user.login(user_data)
        self.assertEqual(rv.status_code, 200)

        rv = self.user.update({'password': 'new_password'})
        self.assertEqual(rv.status_code, 200)
        rv = self.user.logout()

        rv = self.user.login(user_data)
        self.assertEqual(rv.status_code, 403)
        rv = self.user.login({'email': 'email', 'password': 'new_password'})
        self.assertEqual(rv.status_code, 200)
