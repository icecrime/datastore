#!/usr/bin/env python
import argparse
import base64
import os


config_path = os.environ['DATASTORE_API_CONFIG_PATH'] = '../api/conf/'

from datastore.api.encryption import enc_scrypt


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='Kuracistino config file')
    parser.add_argument('-i', '--iterations', help='Number of iterations',
                        default=100, type=int)
    return parser.parse_args()


def main():
    args = parse_arguments()
    if args.iterations <= 0:
        print 'Iteration count must be strictly positive'
        return

    print '[+] Generating random password'
    random_pass = base64.b64encode(os.urandom(64))
    random_hash, salt = enc_scrypt.hash_password(random_pass)

    print '[+] Running test loop ({} iterations)'.format(args.iterations)
    failures = 0
    for i in range(args.iterations):
        res = enc_scrypt.verify_password(random_hash, salt, random_pass)
        if not res:
            failures += 1

    print 'Done with {}/{} failures'.format(failures, args.iterations)


if __name__ == "__main__":
    main()
