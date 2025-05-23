FROM python:3.7-alpine

RUN apk add --update \
    python3-dev \
    py3-yaml \
    ncurses \
    uwsgi \
    build-base \
    openssl-dev \
    bash \
    libffi-dev \
    yaml-dev \
  && pip3 install -U pip setuptools --no-cache-dir \
  && pip3 install poetry virtualenv \
  && rm -rf /var/cache/apk/*

WORKDIR /srv/shortage

ADD . /srv/shortage/
RUN python3 setup.py install

VOLUME ["/srv/data"]
ENV SHORTAGE_PORT 3000
ENV SMS_STORAGE_PATH /srv/data

EXPOSE 3000

# remove credentials
RUN rm -f /srv/shortage/Makefile
RUN rm -f /srv/shortage/.env
RUN rm -rf /srv/shortage/.git

RUN echo 'export PS1="\033[1;34m\w\\033[1;33m \$\033[0m \[$(tput sgr0)\]"' >> $HOME/.bashrc

ENV SHORTAGE_VERSION 4

CMD shortage web --host=0.0.0.0 --port=3000
