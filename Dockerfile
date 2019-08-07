FROM python:3.7-buster

RUN apt-get update \
  && apt-get --yes --no-install-recommends install \
    python3-dev python3-pip uwsgi libffi-dev libzmq5-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/shortage

ADD . /srv/shortage/

RUN pip3 install -U setuptools, pip
RUN pip3 install -r /srv/shortage/requirements.txt

RUN python3 setup.py install

ENV WORKERS 1

ENV SHORTAGE_PORT 3000
EXPOSE 3000

# remove credentials
RUN rm -f /srv/shortage/Makefile
RUN rm -rf /srv/shortage/.git

CMD shortage web --host=0.0.0.0 --port=3000
