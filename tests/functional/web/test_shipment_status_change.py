# -*- coding: utf-8 -*-
import re
import httpretty
from sure import anything
from httpretty.core import HTTPrettyRequestEmpty

from acme_shipment_provider.dao import json
from tests.functional.scenarios import api_client
from tests.functional.scenarios import apidoc_title
from tests.functional.scenarios import apidoc_description


@api_client
@apidoc_title("When ``tracking_code`` doesn't exist")
@apidoc_description("when the tracking_code was not found in the system")
def test_provider_api_shipment_status_change_missing_tracking_code(context):
    ('POST /acme/provider/v1/dodici/x/shipment/<tracking_code>/status should return 404 when the requested tracking_code does not exist')

    # Given that I try to cancel with an inexistent shipment
    response = context.http.post(
        '/acme/provider/v1/dodici/x/shipment/UNKNOWN_TRACKING_CODE/status',
        data=json.dumps({
            'status': 'in_transit',
            'reason': 'testing 404',
        })
    )

    # Then it returns 404
    response.status_code.should.equal(404)


@api_client
@apidoc_title("Change the status of a shipment and notify tenant API")
@apidoc_description("""notice the required fields: ``status`` and ``reason``

where status must be one of:

- **assigned**
- **canceled**
- **delivered**
- **in_transit**
- **out_for_delivery**
- **returned**

""")
@httpretty.activate
def test_provider_api_shipment_status_change_ok(context):
    ('POST /acme/provider/v1/dodici/x/shipment/<tracking_code>/status should '
     'change the status and send a callback push to the api')

    # Background: Intercept all requests to the tenant api to return 418
    httpretty.register_uri(
        httpretty.POST,
        re.compile(".*[.]newstore[.]net.*"),
        status=418,
        body=json.dumps({
            'message': 'dodici is a teapot'
        })
    )

    # And there is a valid assigned shipment
    tracking_code = context.create.shipment(
        offer=context.create.one_shipping_offer(
            provider_rate='ACME_2_DAY_EXPRESS',
        ),
        booking_method='shipping_and_return',
    )

    # When I request to chcange status
    endpoint = '/acme/provider/v1/dodici/x/shipment/{}/status'.format(tracking_code)
    response = context.http.post(
        endpoint,
        headers={
            'Authorization': 'Bearer myAuth0Token',
        },
        data=json.dumps({
            'status': 'in_transit',
            'reason': 'testing tenant notification of shipment status change',
        })
    )

    # Then it returns 418
    response.status_code.should.equal(418)

    # And the resopnse should match the schema
    response_data = json.loads(response.data)
    response_data.should.equal({'message': 'dodici is a teapot'})
    # And it should have called the tenant api
    tenant_api_request = httpretty.last_request()

    tenant_api_request.method.should.equal('POST')
    tenant_api_request.path.should.equal('/v0/d/shipments/{}/delivery_status'.format(tracking_code))
    tenant_api_request.parsed_body.should.equal({
        'status': 'in_transit',
        'updated_at': anything,
        'reason': 'testing tenant notification of shipment status change'
    })


@api_client
@apidoc_title("When Authorization header is missing")
@apidoc_description("""cannot change status of a shipment without a valid access token""")
@httpretty.activate
def test_provider_api_shipment_status_change_missing_token(context):
    ('POST /acme/provider/v1/dodici/x/shipment/<tracking_code>/status '
     'should return 400 if token is missing')

    # Background: Intercept all requests to the tenant api to return 200
    httpretty.register_uri(
        httpretty.POST,
        re.compile(".*[.]newstore[.]net.*"),
        status=200,
    )

    # And there is a valid assigned shipment
    tracking_code = context.create.shipment(
        offer=context.create.one_shipping_offer(
            provider_rate='ACME_2_DAY_EXPRESS',
        ),
        booking_method='shipping_and_return',
    )

    # When I try to change status without passing a token
    endpoint = '/acme/provider/v1/dodici/x/shipment/{}/status'.format(tracking_code)
    response = context.http.post(
        endpoint,
        headers={},
        data=json.dumps({
            'status': 'in_transit',
            'reason': 'testing tenant notification of shipment status change',
        })
    )

    # Then it returns 400
    response.status_code.should.equal(400)

    # And the resopnse should match the schema
    response_data = json.loads(response.data)
    response_data.should.equal({
        'message': 'auth0 bearers access token missing from Authorization header'
    })
    # And it should have called the tenant api
    httpretty.last_request().should.be.a(HTTPrettyRequestEmpty)
