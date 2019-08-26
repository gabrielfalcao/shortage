# -*- coding: utf-8 -*-
import json
from sure import anything
from tests.functional.scenarios import api_client
from tests.functional.scenarios import apidoc_title
from tests.functional.scenarios import apidoc_description


@api_client
@apidoc_title("Health-Check")
@apidoc_description(
    """Used as *ping path* in the `Elastic Load Balancer configuration
<https://docs.aws.amazon.com/elasticloadbalancing/latest/classic/elb-healthchecks.html#health-check-configuration>`_."""
)
def test_api_health_check(context):
    ("GET /health should return 200")

    # Given that I try to get an inexisting shipping label
    response = context.http.get("/health")

    # Then it returns 200
    response.status_code.should.equal(200)
    # And the content type is json
    response.headers["Content-Type"].should.equal("application/json")
    # And should show an object count
    data = json.loads(response.data)

    data.should.equal({"name": "ACME Shipment Provider", "version": anything})
