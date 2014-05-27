#!/bin/sh
docker run --rm --link datastore_db:db datastore/api python /datastore/models/bin/create_database.py /datastore/api/conf/config_docker.yaml
docker run --rm --link datastore_db:db --name datastore_api -P datastore/api
