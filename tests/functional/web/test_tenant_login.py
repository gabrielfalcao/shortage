# -*- coding: utf-8 -*-
import re
import httpretty

from freezegun import freeze_time
from httpretty.core import HTTPrettyRequestEmpty

from acme_shipment_provider.dao import json
from tests.functional.scenarios import api_client
from tests.functional.scenarios import apidoc_title
from tests.functional.scenarios import apidoc_description


@api_client
@freeze_time('April 11, 2018 6:00PM')
@apidoc_title("Authenticate against a tenant api")
@apidoc_description("""This endpoint serves as a kind of proxy to authenticate against
**any tenant api of any environment**.

Since the ACME api can be used against multiple tenants this endpoint
makes it easy for the ACME React Application to let a user manage
shipments from multiple tenants.

Required fields:

- ``tenant`` - defaults to dodici
- ``envchar`` - defaults to ``x`` *(sandbox)*
- ``username``
- ``password``

*The _username_ and _password_ are never stored by ACME, but the resulting token is.*

.. seealso:: Developers can easily change this behavior. Just look at
             the implementation of :py:meth:`~acme_shipment_provider.web.provider.controllers.AuthorizationController.login`

""")
@httpretty.activate
def test_provider_api_login(context):
    ('POST /acme/provider/v1/<tenant>/<envchar/login should '
     'return a access token')

    # Background: Intercept all requests to the tenant api to return 200
    httpretty.register_uri(
        httpretty.POST,
        re.compile(".*[.]newstore[.]net.*"),
        status=200,
        body=json.dumps({
            'access_token': 'something big and secret',
            'refresh_token': 'small and secret',
            'token_type': 'Bearer',
            'scope': 'read:current_user update:current_user_metadata delete:current_user_metadata create:current_user_metadata create:current_user_device_credentials delete:current_user_device_credentials update:current_user_identities offline_access',
            'expires_in': 86400,
        })
    )

    # When I request to login
    response = context.http.post(
        '/acme/provider/v1/dodici/x/login',
        content_type='application/json',
        data=json.dumps({
            'username': 'gabrielfalcao',
            'password': 'wont-ever-tell',
        }),
    )

    # Then it returns 200
    response.status_code.should.equal(200)

    # And the response should have the tokens
    response_data = json.loads(response.data)
    response_data.should.have.key('access_token')
    response_data.should.have.key('refresh_token')
    response_data.should.have.key('tenant')
    response_data.should.have.key('envchar')
    response_data.should.have.key('username')
    response_data.should.have.key('authenticated_at').being.equal(1523469600)
    response_data.should.have.key('expires_at').being.equal(1523556000)
    response_data.should.have.key('expires_in').being.equal(86400)

    response_data.should_not.have.key('password')

    # And the tenant API should have been requested
    tenant_api_request = httpretty.last_request()

    tenant_api_request.method.should.equal('POST')
    tenant_api_request.path.should.equal('/v0/token')
    tenant_api_request.parsed_body.should.equal({
        'username': 'gabrielfalcao',
        'grant_type': 'password',
        'password': 'wont-ever-tell',
    })
    tenant_api_request.headers.should.have.key('Request-Id')
    tenant_api_request.headers.should.have.key('Host').being.equal('dodici.x.newstore.net')


@api_client
@apidoc_title("login requires username")
@apidoc_description("""returns 400""")
@httpretty.activate
def test_provider_api_login_missing_username(context):
    ('POST /acme/provider/v1/<tenant>/<envchar/login should '
     'return 400 when missing username')

    # Background: Prevent real http requests to tenant api
    httpretty.register_uri(
        httpretty.POST,
        re.compile(".*[.]newstore[.]net.*"),
        status=200,
    )

    # Given I request to login without a username
    response = context.http.post(
        '/acme/provider/v1/dodici/x/login',
        content_type='application/json',
        data=json.dumps({
            'password': 'wont-ever-tell',
        }),
    )

    # Then it returns 400
    response.status_code.should.equal(400)

    # And the response should have the tokens
    response_data = json.loads(response.data)
    response_data.should.equal({
        'message': 'missing username'
    })

    # And the tenant API should not have been called
    httpretty.last_request().should.be.a(HTTPrettyRequestEmpty)


@api_client
@apidoc_title("login requires password")
@apidoc_description("""returns 400""")
@httpretty.activate
def test_provider_api_login_missing_password(context):
    ('POST /acme/provider/v1/<tenant>/<envchar/login should '
     'return 400 when missing password')

    # Background: Prevent real http requests to tenant api
    httpretty.register_uri(
        httpretty.POST,
        re.compile(".*[.]newstore[.]net.*"),
        status=200,
    )

    # Given I request to login without a password
    response = context.http.post(
        '/acme/provider/v1/dodici/x/login',
        content_type='application/json',
        data=json.dumps({
            'username': 'person',
        }),
    )

    # Then it returns 400
    response.status_code.should.equal(400)

    # And the response should have the tokens
    response_data = json.loads(response.data)
    response_data.should.equal({
        'message': 'missing password'
    })

    # And the tenant API should not have been called
    httpretty.last_request().should.be.a(HTTPrettyRequestEmpty)
