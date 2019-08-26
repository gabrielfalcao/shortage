# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import io
import json
import re
import traceback

from pathlib import Path
from jinja2 import Template
from flask.testing import FlaskClient


def apidoc_title(title):
    """Decorator to define an explicit title for the generated endpoint documentation.
    """

    def dec(func):
        func.__title__ = title
        return func

    return dec


def apidoc_description(description):
    """Decorator to define an explicit description body for the generated endpoint documentation.
    """

    def dec(func):
        func.__description__ = description
        return func

    return dec


def try_json(body, indent=2):
    """pretty data formatting function.

    Tries to parse the data as JSON and prettifies it. Used for
    generating nice JSON payloads in the documentation.


    .. note:: If you need to generate documentation for endpoints that
       return other formats (e.g.: xml, yaml) here the place to prettify
       your request and response bodies.

    """
    if isinstance(body, bytes):
        body = body.decode("utf-8")

    try:
        json_body = json.loads(body)
    except Exception:
        return body

    return str(json.dumps(json_body, indent=indent))


def pretty_header_name(name):
    """Normalize headers from ``header-name`` to ``Header-Name``
    """
    return str("-".join([s.capitalize() for s in name.split("_")]))


def headers_to_rst(headers):
    return str(
        "\n".join(
            [
                "{}: {}".format(pretty_header_name(k), v)
                for k, v in headers.items()
            ]
        )
    )


def extract_test_case_frame_from_stack():
    candidates = [
        s for s in traceback.extract_stack() if s.name.startswith("test_")
    ]
    test_case_frame = candidates[0]
    return test_case_frame


def extract_current_test_case_from_stack():
    test_case_frame = extract_test_case_frame_from_stack()

    source_code = io.open(test_case_frame.filename).read()
    scope = {}
    exec(source_code, scope)
    test_case = scope[test_case_frame.name]
    return test_case


def extract_description_from_current_test_case():
    test_case = extract_current_test_case_from_stack()
    return getattr(test_case, "__description__", test_case.__doc__)


def extract_title_from_current_test_case():
    test_case = extract_current_test_case_from_stack()
    return getattr(test_case, "__title__", test_case.__doc__)


def extract_name_of_current_test_case():
    test_case = extract_current_test_case_from_stack()
    return test_case.__name__


def response_to_dict(response):
    body = response.data

    result = {
        "headers": headers_to_rst(response.headers),
        "body": try_json(body),
        "status": response.status,
        "status_code": response.status_code,
    }
    return result


def environ_to_request(environ, body=None):
    request = dict(
        host=environ.get("HTTP_HOST"),
        path=environ.get("PATH_INFO"),
        method=environ.get("REQUEST_METHOD"),
        port=environ.get("SERVER_PORT", 80),
        http_version=environ.get("SERVER_PROTOCOL"),
        headers={},
    )
    headers = dict(
        [
            (k.replace("HTTP_", "", 1), v)
            for k, v in environ.items()
            if k.startswith("HTTP_")
        ]
    )
    fd = environ.pop("wsgi.input")
    body = try_json(body or fd.read())

    request["headers"] = headers_to_rst(headers)
    request["body"] = body
    return request


class HttpDomainFlaskClient(FlaskClient):
    def __init__(self, *args, **kw):
        self.documentation_path = kw.pop("documentation_path")
        super(HttpDomainFlaskClient, self).__init__(*args, **kw)

    def should_generate_docs(self):
        return bool(os.getenv("ACME_GENERATE_DOCS"))

    def url_to_filename(self, url):
        return "{}.rst".format(re.sub(r"\W+", "-", url).strip("-"))

    def url_to_path(self, url):
        filename = self.url_to_filename(url)
        target = Path(self.documentation_path)
        if not target.is_dir():
            target.mkdir(parents=True)

        return target.joinpath(filename)

    def open(self, *args, **kw):
        as_tuple = kw.get("as_tuple", False)
        kw["as_tuple"] = True

        body = kw.get("data")
        environ, response = super(HttpDomainFlaskClient, self).open(
            *args, **kw
        )

        if response.headers.get("Content-Type") != "application/json":
            return response

        if self.should_generate_docs():
            self.persist_documentation(environ, body, response)

        if as_tuple:
            return environ, response
        return response

    def generate_endpoint_documentation(self, environ, body, response):
        request = environ_to_request(environ, body)

        test_name = extract_name_of_current_test_case()
        title = extract_title_from_current_test_case()
        description = extract_description_from_current_test_case()

        context = {
            "test_name": test_name,
            "request": request,
            "response": response_to_dict(response),
            "title": "\n".join([title, "-" * len(title.strip())]),
            "description": description,
        }

        return ENDPOINT_TEMPLATE.render(**context).strip()

    def persist_documentation(self, environ, body, response):
        documentation = self.generate_endpoint_documentation(
            environ, body, response
        )
        frame = extract_test_case_frame_from_stack()
        path = self.url_to_path(frame.name)
        return path.write_text(documentation)

    @classmethod
    def from_app(cls, app, documentation_path, **kwargs):
        return cls(
            app,
            app.response_class,
            documentation_path=documentation_path,
            **kwargs
        )


ENDPOINT_TEMPLATE = Template(
    """
{% if title %}{{ title }}{% endif %}

.. _{{ test_name }}:

.. http:{{ request.method.lower() }}:: {{ request.path }}

   {{ description|indent(3) }}

   **Example request**:

   .. sourcecode:: http

      POST {{ request.path }} HTTP/1.1
      Host: {{ request.host }}
      {{ request.headers|indent(6) }}

      {{ request.body|indent(6) }}


   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 {{ response.status }} HTTP/1.1
      {{ response.headers|indent(6) }}

      {{ response.body|indent(6) }}
"""
)
