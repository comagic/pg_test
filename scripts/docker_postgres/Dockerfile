FROM postgres:latest

MAINTAINER Sergey Kraynev version: 0.1

RUN apt-get update && apt-get install -y postgis \
    git make postgresql-server-dev-9.6 flex bison postgresql-plpython-9.6

RUN git clone https://github.com/postgrespro/jsquery.git /tmp/extensions/jsquery
RUN cd /tmp/extensions/jsquery && make USE_PGXS=1 && make USE_PGXS=1 install

RUN git clone https://github.com/comagic/plexor.git /tmp/extensions/plexor
# fix for issue https://github.com/comagic/plexor/pull/3/files
RUN sed -i 's/#PG_CPPFLAGS = -std=c89/#PG_CPPFLAGS = -std=c89\nPG_CPPFLAGS += -I$(PQINC)/g' /tmp/extensions/plexor/makefile
RUN cd /tmp/extensions/plexor && make && make install

# create extensions
COPY build_extensions.sh /docker-entrypoint-initdb.d/
# create roles
COPY prepare_roles.sql /docker-entrypoint-initdb.d/
