FROM ubuntu:precise

MAINTAINER arnaud.porterie@gmail.com

RUN apt-get update

# Install required Python elements
RUN apt-get install -y python python-dev python-setuptools python-software-properties
RUN easy_install pip
RUN pip install uwsgi

# Install web server
RUN add-apt-repository ppa:nginx/stable
RUN apt-get update 
RUN apt-get install -y nginx supervisor

# Add and install application
ADD . /datastore/
RUN pip install /datastore/api/
RUN pip install /datastore/models/

# We use a Docker specific configuration file for the database info
ENV DATASTORE_API_CONFIG_FILE config_docker.yaml

# Install postgres requirements. Note that psycopg2 is not installed by the
# /datastore/models package because the app is database agnostic.
RUN apt-get install -y libpq-dev
RUN pip install psycopg2

# Configure nginx
RUN echo "daemon off;" >> /etc/nginx/nginx.conf
RUN ln -s /datastore/deploy/nginx-app.conf /etc/nginx/sites-enabled/
RUN ln -s /datastore/deploy/supervisor-app.conf /etc/supervisor/conf.d/
RUN rm /etc/nginx/sites-enabled/default

# Initialize database model (requires the db container to be running: maybe
# that's not the ideal pattern)
#RUN python /datastore/models/bin/create_database.py /datastore/api/conf/config_docker.yaml

# Stored user files live on a durable volume
VOLUME ["/var/lib/datastore/"]
RUN chown -R www-data:www-data /var/lib/datastore

# Run uwsgi and nginx through supervisord
EXPOSE 80
CMD ["supervisord", "-n"]
