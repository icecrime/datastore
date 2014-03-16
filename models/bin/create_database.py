import argparse

import yaml

from datastore import models


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='Filedepot configuration file')
    return parser.parse_args()


def main():
    args = parse_arguments()
    with open(args.config) as config_file:
        models.create_database(yaml.load(config_file)['database'])


if __name__ == "__main__":
    main()
