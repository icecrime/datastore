import argparse
from collections import namedtuple
import os
import random
import sys
import thread
import threading
import uuid

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

###############################################################################


def go(session, server=None):
    global SERVER
    if server:
        SERVER = server
    return login(session, SERVER.login, SERVER.password)


###############################################################################


def chunked_upload(session, data, **params):
    url = '%s/chunked_upload' % SERVER.url
    return session.put(url, data=data, params=params)


def commit_chunked_upload(session, root, path, upload_id, **params):
    url = '%s/commit_chunked_upload/%s/%s' % (SERVER.url, root, path)
    return session.post(url, data={'upload_id': upload_id}, params=params)


def copy(session, root, from_path, to_path):
    url = '%s/fileops/copy' % SERVER.url
    data = {'root': root, 'from_path': from_path, 'to_path': to_path}
    return session.post(url, data=data)


def create_folder(session, root, path):
    url = '%s/fileops/create_folder' % SERVER.url
    data = {'root': root, 'path': path}
    return session.post(url, data=data)


def create_user(session, email, password):
    url = '%s/users' % SERVER.url
    data = {'email': email, 'password': password}
    return session.post(url, data=data)


def delete(session, root, path):
    url = '%s/fileops/delete' % SERVER.url
    data = {'root': root, 'path': path}
    return session.post(url, data=data)


def get(session, root, path):
    url = '%s/files/%s/%s' % (SERVER.url, root, path)
    return session.get(url)


def get_link(session, key):
    url = '%s/files/%s' % (SERVER.url, key)
    return session.get(url)


def info(session):
    url = '%s/account/info' % SERVER.url
    return session.get(url)


def login(session, email, password):
    url = '%s/login' % SERVER.url
    data = {'email': email, 'password': password}
    return session.post(url, data=data)


def logout(session):
    url = '%s/logout' % SERVER.url
    return session.get(url)


def metadata(session, root='', path='', **params):
    url = '/'.join(filter(bool, [SERVER.url, 'metadata', root, path]))
    return session.get(url, params=params)


def move(session, root, from_path, to_path):
    url = '%s/fileops/move' % SERVER.url
    data = {'root': root, 'from_path': from_path, 'to_path': to_path}
    return session.post(url, data=data)


def put(session, root, path, content):
    url = '%s/files/%s/%s' % (SERVER.url, root, path)
    return session.post(url, data=content)


def put_file(session, root, path, filename):
    url = '%s/files/%s/%s' % (SERVER.url, root, path)
    with open(filename, 'r') as f:
        return session.post(url, data=f)


def put_chunked(session, root, path, **kwargs):
    url = '%s/chunked_upload' % SERVER.url
    params = {'offset': 0, 'upload_id': ''}

    while True:
        line = raw_input('... ').rstrip()
        if not line:
            break
        rv = session.put(url, data=line, params=params)
        params['offset'] = rv.json['offset']
        params['upload_id'] = rv.json['upload_id']

    params.pop('offset')
    return commit_chunked_upload(session, root, path, params, kwargs)


def revisions(session, root, path):
    url = '%s/revisions/%s/%s' % (SERVER.url, root, path)
    return session.get(url)


def search(session, root, path, query, **params):
    url = '%s/search/%s/%s' % (SERVER.url, root, path)
    params.update({'query': query})
    return session.get(url, params=params)


def shares(session, root, path):
    url = '%s/shares/%s/%s' % (SERVER.url, root, path)
    return session.post(url)


def shares_remove(session, key):
    url = '%s/shares/%s' % (SERVER.url, key)
    return session.delete(url)


def update_info(session, **kwargs):
    url = '%s/account/info' % SERVER.url
    return session.post(url, data=kwargs)


###############################################################################


root = 'sandbox'
paths = {'usr1': ['']}
#paths = dict(('usr{}'.format(i), ['']) for i in range(11))


def _make_data():
    return os.urandom(random.randint(1, 128))

def _make_target(usr):
    base = random.choice(paths[usr])
    while True:
        newd = str(uuid.uuid4())[:18]
        target = os.path.join(base, newd) if base else newd
        if target not in paths[usr]:
            break
    return target


def _put_chunked(session, target, content, parts=2):
    chunk_size = len(content) / parts
    if chunk_size <= 0:
        chunk_size = len(content)

    count = 0
    params = {}
    while True:
        chunk = content[chunk_size * count:chunk_size * (count + 1)]
        if not chunk:
            break
        rv = checked(chunked_upload, session, chunk, **params)
        params['offset'] = rv.json()['offset']
        params['upload_id'] = rv.json()['upload_id']
        count += 1

    checked(commit_chunked_upload, session, root, target, params['upload_id'])


def checked(fn, *args, **kwargs):
    rv = fn(*args, **kwargs)
    if rv.status_code != requests.codes.ok:
        name = fn.__name__
        print '!! Call failed {}()'.format(name)
        print '\tStatus code: {}'.format(rv.status_code)
        try:
            print '\tJSON: {}'.format(rv.json())
        except ValueError:
            print '\tText: {}'.format(rv.text)
        sys.exit(0)
    return rv


def check_create_folder(session, target):
    rv = metadata(session, root, target)
    if rv.status_code != requests.codes.ok:
        return False
    try:
        if rv.json()['is_dir'] != True:
            print '!! Check failed for folder on {}'.format(target)
            print '  Metadata is_dir is not True'
            return False
    except ValueError:
        return False
    return True


def check_put(session, target, data):
    rv = get(session, root, target)
    if rv.status_code != requests.codes.ok:
        return False
    if rv.content != data:
        print '!! Check failed for file on {}'.format(target)
        print '  In store: {}'.format(rv.content)
        print '  Expected: {}'.format(data)
        return False
    return True


def op_create_folder(session, usr):
    target = _make_target(usr)
    sys.stdout.write('{} MKDIR {}\n'.format(thread.get_ident(), target))
    rv = checked(create_folder, session, root, target)
    if rv.status_code == requests.codes.ok:
        global paths
        paths[usr].append(target)
    return (target, )


def op_put(session, usr):
    data = _make_data()
    target = _make_target(usr)
    sys.stdout.write('{} PUT   {}\n'.format(thread.get_ident(), target))
    checked(put, session, root, target, data)
    return target, data


def op_put_chunked(session, usr):
    data = _make_data()
    target = _make_target(usr)
    sys.stdout.write('{} PUTCH {}\n'.format(thread.get_ident(), target))
    _put_chunked(session, target, data, random.randint(1, 16))
    return target, data


op_create_folder.checker = check_create_folder
op_put.checker = check_put
op_put_chunked.checker = check_put


###############################################################################


log = {}
ops = [op_create_folder, op_put, op_put_chunked]

thread_usr = {}
userlist = ['usr1']


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--threads', default=2, type=int,
                        help='Number of threads')
    parser.add_argument('-o', '--op-per-thread', default=5, type=int,
                        help='Number of operations per thread')
    return parser.parse_args()


def thread_proc(op_count):
    usr = random.choice(userlist)
    tid = threading.current_thread().ident

    global thread_usr
    thread_usr[tid] = usr

    sys.stdout.write('[!] Thread {} logging in as {}\n'.format(tid, usr))
    with requests.Session() as session:
        checked(login, session, usr, usr)
        log[tid] += ((fn, fn(session, usr)) for fn in
                     (random.choice(ops) for _ in range(op_count)))
        checked(logout, session)
    sys.stdout.write('[!] Thread {} logged out\n'.format(tid))


def main():
    args = parse_arguments()
    print '[*] Running {} threads ({} ops per thread)'.format(
        args.threads, args.op_per_thread)

    print '[+] Creating workers\n'
    tid = [threading.Thread(target=thread_proc, args=(args.op_per_thread,))
           for _ in range(args.threads)]
    for t in tid:
        t.start()
        log[t.ident] = []
    [t.join() for t in tid]

    print '\n[+] Running verification phase'
    for tid, operations in log.items():
        session = requests.Session()
        checked(login, session, thread_usr[tid], thread_usr[tid])
        for fn, data in operations:
            if not fn.checker(session, *data):
                print '!! Check failed for {}'.format(fn.__name__)
        checked(logout, session)
    print '[*] All done'


if __name__ == "__main__":
    main()
