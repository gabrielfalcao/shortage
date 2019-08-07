# -*- coding: utf-8 -*-
import re
import httpretty
from httpretty.core import HTTPrettyRequestEmpty

from acme_shipment_provider.dao import json
from tests.functional.scenarios import api_client
from tests.functional.scenarios import apidoc_title
from tests.functional.scenarios import apidoc_description


@api_client
@apidoc_title("Change shipment status to delivered")
@apidoc_description("""marks a shipment as ``delivered``

The shipment status must be ``in_transit`` for this to work

.. note:: This endpoint does **not** push a status change callback to the tenant api
""")
@httpretty.activate
def test_provider_api_confirm_shipment_handout(context):
    ('POST /acme/provider/v1/shipment/<tracking_code>/confirm_delivered should '
     'change the status to delivered')

    # Background: Intercept all requests to the tenant api to return 200
    httpretty.register_uri(
        httpretty.POST,
        re.compile(".*[.]newstore[.]net.*"),
        status=200
    )

    # And there is a valid shipment in transit
    tracking_code = context.create.shipment(
        offer=context.create.one_shipping_offer(
            provider_rate='ACME_2_DAY_EXPRESS',
        ),
        booking_method='shipping_and_return',
        force_status='in_transit',
    )

    # When I confirm the handout
    endpoint = '/acme/provider/v1/shipment/{}/confirm_delivered'.format(tracking_code)
    response = context.http.post(endpoint)

    # Then it returns 200
    response.status_code.should.equal(200)

    # And the status should be ``delivered``
    response_data = json.loads(response.data)
    response_data.should.have.key('status').being.equal('delivered')

    # And it should NOT have called the tenant api
    httpretty.last_request().should.be.a(HTTPrettyRequestEmpty)
