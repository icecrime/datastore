FROM ubuntu:precise

MAINTAINER arnaud.porterie@gmail.com

RUN apt-get update

# Install postgres
# TODO --no-check-certificate is really ugly
RUN apt-get install -y wget
RUN wget --no-check-certificate --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ precise-pgdg main" >> /etc/apt/sources.list.d/pgdg.list
RUN apt-get update
RUN apt-get install -y postgresql-9.3

# Create user and database: should match the database information found in the
# app configuration: /datastore/api/config_docker.yaml
USER postgres
RUN /etc/init.d/postgresql start && \
    psql --command "CREATE USER kuracistino WITH SUPERUSER PASSWORD 'kuracistino';" && \
    createdb -O kuracistino kuracistino

# Allow remote connections
RUN echo "host all  all    0.0.0.0/0  md5" >> /etc/postgresql/9.3/main/pg_hba.conf
RUN echo "listen_addresses='*'" >> /etc/postgresql/9.3/main/postgresql.conf

# Run postgresql. Note that we do not EXPOSE anything: the API will access the
# database through a docker --link
VOLUME  ["/etc/postgresql", "/var/log/postgresql", "/var/lib/postgresql"]
CMD ["/usr/lib/postgresql/9.3/bin/postgres", "-D", "/var/lib/postgresql/9.3/main", "-c", "config_file=/etc/postgresql/9.3/main/postgresql.conf"]
