from collections import namedtuple
import json
import requests

ServerData = namedtuple('ServerData', ['url', 'login', 'password'])

HOME = ServerData(
    'http://127.0.0.1:5001',
    'icecrime@kuracistino.fr',
    'icecrime'
)
PROD = ServerData(
    'http://api.kuracistino.fr',
    'icecrime@kuracistino.fr',
    'icecrime'
)

SERVER = HOME

session = requests.Session()

###############################################################################


def go(server=None):
    global SERVER
    if server:
        SERVER = server
    return login(SERVER.login, SERVER.password)


###############################################################################


class expects(object):

    @staticmethod
    def _format_json(rv):
        return json.dumps(rv.json(), indent=4)

    @staticmethod
    def _wrapper(fn, printer):
        def _wrapped(*args, **kwargs):
            rv = fn(*args, **kwargs)
            if rv.status_code == requests.codes.ok:
                print printer(rv)
            else:
                try:
                    print expects._format_json(rv)
                except ValueError:
                    print rv.status_code
        return _wrapped

    @staticmethod
    def content(fn):
        return expects._wrapper(fn, lambda rv: rv.content)

    @staticmethod
    def json(fn):
        return expects._wrapper(fn, expects._format_json)

    @staticmethod
    def text(fn):
        return expects._wrapper(fn, lambda rv: rv.text)


###############################################################################


def chunked_upload(data, **params):
    url = '%s/chunked_upload' % SERVER.url
    rv = session.put(url, data=data, params=params)
    print json.dumps(rv.json, indent=4)
    print rv.status_code


@expects.json
def commit_chunked_upload(root, path, upload_id, **params):
    url = '%s/commit_chunked_upload/%s/%s' % (SERVER.url, root, path)
    return session.post(url, data={'upload_id': upload_id}, params=params)


@expects.json
def copy(root, from_path, to_path):
    url = '%s/fileops/copy' % SERVER.url
    data = {'root': root, 'from_path': from_path, 'to_path': to_path}
    return session.post(url, data=data)


@expects.json
def create_folder(root, path):
    url = '%s/fileops/create_folder' % SERVER.url
    data = {'root': root, 'path': path}
    return session.post(url, data=data)


@expects.content
def create_user(email, password):
    url = '%s/users' % SERVER.url
    data = {'email': email, 'password': password}
    return session.post(url, data=data)


@expects.json
def delete(root, path):
    url = '%s/fileops/delete' % SERVER.url
    data = {'root': root, 'path': path}
    return session.post(url, data=data)


@expects.text
def get(root, path):
    url = '%s/files/%s/%s' % (SERVER.url, root, path)
    return session.get(url)


@expects.text
def get_link(key):
    url = '%s/files/%s' % (SERVER.url, key)
    return session.get(url)


@expects.json
def info():
    url = '%s/account/info' % SERVER.url
    return session.get(url)


@expects.json
def login(email, password):
    url = '%s/login' % SERVER.url
    data = {'email': email, 'password': password}
    return session.post(url, data=data)


@expects.content
def logout():
    url = '%s/logout' % SERVER.url
    return session.get(url)


@expects.json
def metadata(root='', path='', **params):
    url = '/'.join(filter(bool, [SERVER.url, 'metadata', root, path]))
    return session.get(url, params=params)


@expects.json
def move(root, from_path, to_path):
    url = '%s/fileops/move' % SERVER.url
    data = {'root': root, 'from_path': from_path, 'to_path': to_path}
    return session.post(url, data=data)


@expects.json
def put(root, path, filename):
    url = '%s/files/%s/%s' % (SERVER.url, root, path)
    with open(filename, 'r') as f:
        return session.post(url, data=f)


def put_chunked(root, path, **kwargs):
    url = '%s/chunked_upload' % SERVER.url
    params = {'offset': 0, 'upload_id': ''}

    while True:
        line = raw_input('... ')
        if not line:
            break
        rv = session.put(url, data=line + '\n', params=params)
        params['offset'] = rv.json()['offset']
        params['upload_id'] = rv.json()['upload_id']

    params.pop('offset')
    return commit_chunked_upload(root, path, params['upload_id'], **kwargs)


@expects.json
def revisions(root, path):
    url = '%s/revisions/%s/%s' % (SERVER.url, root, path)
    return session.get(url)


@expects.json
def search(root, path, query, **params):
    url = '%s/search/%s/%s' % (SERVER.url, root, path)
    params.update({'query': query})
    return session.get(url, params=params)


@expects.json
def shares(root, path):
    url = '%s/shares/%s/%s' % (SERVER.url, root, path)
    return session.post(url)


@expects.json
def shares_remove(key):
    url = '%s/shares/%s' % (SERVER.url, key)
    return session.delete(url)


@expects.json
def update_info(**kwargs):
    url = '%s/account/info' % SERVER.url
    return session.post(url, data=kwargs)
