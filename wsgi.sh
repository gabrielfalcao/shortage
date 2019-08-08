#!/usr/bin/env bash

set -ex

$(which uwsgi) \
        --ini /srv/shortage/uwsgi.conf \
        --module "shortage.wsgi:server" \
        --need-app \
        --http-socket :"$SHORTAGE_PORT" \
        --master
