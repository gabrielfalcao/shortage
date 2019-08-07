# -*- coding: utf-8 -*-
from freezegun import freeze_time
from acme_shipment_provider.dao import json
from tests.functional.scenarios import api_client
from tests.functional.scenarios import apidoc_title
from tests.functional.scenarios import apidoc_description


def sorted_shipments(items):
    sort_func = lambda shipment: shipment['tracking_code']
    return sorted(items, key=sort_func, reverse=True)


@freeze_time('April 11, 2018 6:00PM')
@api_client
@apidoc_title("Retrieve all shipments")
@apidoc_description("""
From all tenants and environments
""")
def test_provider_api_list_shipments(context):
    ('GET /acme/provider/v1/shipments should return all shipments')
    # Given that there are 2 shipments from the same tenant and envchar
    created = [
        context.create.shipment(tenant='dodici', envchar='x', only_tracking_code=False),
        context.create.shipment(tenant='dodici', envchar='x', only_tracking_code=False),

        # And 2 shipments from a different tenants but same envchar
        context.create.shipment(tenant='adidas', envchar='x', only_tracking_code=False),
        context.create.shipment(tenant='decathlon', envchar='x', only_tracking_code=False),

        # And finally 2 shipments from same tenant but different envchars
        context.create.shipment(tenant='dodici', envchar='v', only_tracking_code=False),
        context.create.shipment(tenant='dodici', envchar='s', only_tracking_code=False),
    ]
    # When I request to list all shipments
    response = context.http.get('/acme/provider/v1/shipments')

    # Then it returns 200
    response.status_code.should.equal(200)

    # And all 6 shipments are returned
    shipments = json.loads(response.data)
    shipments.should.have.length_of(6)

    shp1, shp2 = shipments[:2]

    shp1.should.have.key('tracking_code')
    shp2.should.have.key('tracking_code')
    shp1.should.have.key('order').being.equal(shp1['request_data']['external_order_id'])
    shp2.should.have.key('order').being.equal(shp2['request_data']['external_order_id'])
    created.should.have.length_of(6)


@freeze_time('April 11, 2018 6:00PM')
@api_client
@apidoc_title("From a single tenant/environment")
@apidoc_description("""Simple append the **tenant** and **envchar**
to the :ref:`retrieve all shipments <test_provider_api_list_shipments>`
endpoint.""")
def test_provider_api_filter_shipments_by_tenant_and_envchar(context):
    ('GET /acme/provider/v1/shipments/dodici/x should filter by tenant and environment')

    # Given that there are 2 shipments from the same tenant and envchar
    created = [
        context.create.shipment(tenant='dodici', envchar='x', only_tracking_code=False),
        context.create.shipment(tenant='dodici', envchar='x', only_tracking_code=False),

        # And 2 shipments from a different tenants but same envchar
        context.create.shipment(tenant='adidas', envchar='x', only_tracking_code=False),
        context.create.shipment(tenant='decathlon', envchar='x', only_tracking_code=False),

        # And finally 2 shipments from same tenant but different envchars
        context.create.shipment(tenant='dodici', envchar='v', only_tracking_code=False),
        context.create.shipment(tenant='dodici', envchar='s', only_tracking_code=False),
    ]
    # When I request to filter shipments
    response = context.http.get('/acme/provider/v1/shipments/dodici/x')

    # Then it returns 200
    response.status_code.should.equal(200)

    # And only 2 shipments are returned
    shipments = json.loads(response.data)
    shipments.should.have.length_of(2)

    shp1, shp2 = shipments

    shp1.should.have.key('tracking_code')
    shp2.should.have.key('tracking_code')
    shp1.should.have.key('order').being.equal(shp1['request_data']['external_order_id'])
    shp2.should.have.key('order').being.equal(shp2['request_data']['external_order_id'])
    created.should.have.length_of(6)
