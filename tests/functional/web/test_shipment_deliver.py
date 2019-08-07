# -*- coding: utf-8 -*-
import re
import httpretty
from httpretty.core import HTTPrettyRequestEmpty

from acme_shipment_provider.dao import json
from tests.functional.scenarios import api_client
from tests.functional.scenarios import apidoc_title
from tests.functional.scenarios import apidoc_description


@api_client
@apidoc_title("Change shipment status to in_transit")
@apidoc_description("""marks a shipment as ``in_transit``

The shipment status must be ``assigned`` for this to work

.. warning:: This endpoint does **not** push a status change callback to the tenant api
""")
@httpretty.activate
def test_provider_api_set_in_transit(context):
    ('POST /acme/provider/v1/shipment/<tracking_code>/deliver should '
     'change the status to in_transit')

    # Background: Intercept all requests to the tenant api to return 200
    httpretty.register_uri(
        httpretty.POST,
        re.compile(".*[.]newstore[.]net.*"),
        status=200
    )

    # And there is a valid shipment assigned
    tracking_code = context.create.shipment(
        offer=context.create.one_shipping_offer(
            provider_rate='ACME_2_DAY_EXPRESS',
        ),
        booking_method='shipping_and_return',
        force_status='assigned',
    )

    # When I request to deliver
    endpoint = '/acme/provider/v1/shipment/{}/deliver'.format(tracking_code)
    response = context.http.post(endpoint)

    # Then it returns 200
    response.status_code.should.equal(200)

    # And the status should be ``delivered``
    response_data = json.loads(response.data)
    response_data.should.have.key('status').being.equal('in_transit')

    # And it should NOT have called the tenant api
    httpretty.last_request().should.be.a(HTTPrettyRequestEmpty)
