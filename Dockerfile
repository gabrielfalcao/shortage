FROM python:3.7-alpine

RUN apk add --update \
    python3-dev \
    uwsgi \
    build-base \
    libffi-dev \
  && pip install virtualenv \
  && rm -rf /var/cache/apk/*

WORKDIR /srv/shortage

RUN pip3 install -U setuptools pip

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

CMD shortage web --host=0.0.0.0 --port=3000
