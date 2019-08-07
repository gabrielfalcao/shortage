# -*- coding: utf-8 -*-
import random
import shutil
import httpretty
import acme_shipment_provider
from pathlib import Path
from sure import scenario
from datetime import timedelta

from acme_shipment_provider import aws
from acme_shipment_provider.util import DateEngine
from acme_shipment_provider.web.schemas import json
from acme_shipment_provider import application
from acme_shipment_provider.dao import FileStorage
from acme_shipment_provider.dao import S3Storage
from acme_shipment_provider.helpers import fake
from acme_shipment_provider.web.adapter.controllers import OffersController
from acme_shipment_provider.web.adapter.controllers import ShipmentController

from tests.functional.httpdomain_client import HttpDomainFlaskClient
from tests.functional.httpdomain_client import apidoc_title  # noqa
from tests.functional.httpdomain_client import apidoc_description  # noqa


datetime = DateEngine()

dao_path = Path(__file__).parent.joinpath('_state')
documentation_path = Path(acme_shipment_provider.__file__).parent.parent.joinpath('docs/source/tested-endpoints')


class Synthesize(object):
    """Generates fake data in-memory

    This class does not perform I/O. Look at the FixtureFactory class for helper methods that write data to the DAO.
    """

    @classmethod
    def external_order_id(cls):
        """:returns: a string with a fake order number for Giovana Dodici (GD)
        """
        return 'GD{}'.format("".join([str(random.randint(0, 9)) for _ in range(9)]))

    @classmethod
    def package(cls, width=100, height=100, depth=100, length_unit='cm', weight=2.5, weight_unit='kb'):
        """
        :returns: a dict with packaging information (dimensions and weight)
        """
        result = {
            "dimensions": {
                "width": width,
                "height": height,
                "depth": depth,
                "unit": length_unit,
            },
            "weight": {
                "amount": weight,
                "unit": weight_unit,
            }
        }
        return result

    @classmethod
    def adapter_address(cls, **kw):
        """
        :returns: a dict first_name, last_name and all the other address fields. All data points to Alaska.
        """
        data = fake.address_dict()
        data.update(kw)
        return data

    @classmethod
    def adapter_request(cls, ready_by=None, **kw):
        """
        :returns: a dict with sender_address, shipping_address and ready_by
        """
        request_data = {
            "sender_address": cls.adapter_address(country_code='US'),
            "shipping_address": cls.adapter_address(country_code='US'),
            "ready_by": ready_by or DateEngine.prettify(datetime.now() + timedelta(days=1)),
        }
        request_data.update(kw)
        return request_data

    @classmethod
    def adapter_request_json(cls, *args, **kw):
        """shortcut to adapter_request() that also serializes the data in json
        """
        return json.dumps(cls.adapter_request(*args, **kw))

    @classmethod
    def adapter_booking_request(cls, rate, **kw):
        """
        :returns: a dict with request data for booking a shipment
        """
        request_data = {
            "offer": kw.pop('offer', None),
            "rate": rate,
            "carrier_code": "ACME",
            "external_order_id": "some offer id",
            "booking_method": "only_shipping",
            "sender_address": cls.adapter_address(country_code='US'),
            "shipping_address": cls.adapter_address(country_code='US'),
            "tenant": 'dodici',
            "envchar": 'x',
            "items": [
                {
                    "price": {
                        "currency": "USD",
                        "amount": 42,
                    },
                    "identifier": {
                        "EAN": "978020137962"
                    }
                },
                {
                    "weight": {
                        "amount": 750,
                        "unit": "g"
                    },
                    "identifier": {
                        "SKU": "dc12456"
                    },
                    "dimensions": {
                        "unit": "cm",
                        "width": 200,
                        "length": 200
                    }
                }
            ]
        }
        request_data.update(kw)
        return request_data

    @classmethod
    def adapter_booking_request_json(cls, *args, **kw):
        """shortcut to adapter_booking_request() that also serializes the data in json
        """
        return json.dumps(cls.adapter_booking_request(*args, **kw))


class FixtureFactory(object):
    """Data factory that writes directly in the DAO, useful to test API
    endpoints that retrieve or modify existing data.
    """
    def __init__(self, context):
        self.context = context

    def many_shipping_offers(self, provider_name='traditional', **kw):
        """
        :returns: a list of offer data from the data-storage layer
        """
        with self.context.application.test_request_context():
            return self.context.controller(OffersController).generate_offers(
                provider_name,
                Synthesize.adapter_request(**kw),
            )

    def one_shipping_offer(self, **kw):
        """shortcut to ``many_shipping_offers()`` but returns only the first offer
        """
        if not kw:
            kw['provider_rate'] = 'ACME_2_DAY_EXPRESS'

        offers = self.many_shipping_offers(**kw)
        if not offers:
            msg = 'could not create offers with given params: {}'
            raise AssertionError(msg.format(kw))

        return offers[0]['offer']

    def shipment(self, force_status=None, only_tracking_code=True, provider_name='traditional', tenant='dodici', envchar='x', **request_data):
        """
        :returns: shipment data from the data-storage layer
        """
        request_data['tenant'] = tenant
        request_data['envchar'] = envchar
        if not request_data.get('offer'):
            request_data['offer'] = self.one_shipping_offer()

        if not request_data.get('external_order_id'):
            request_data['external_order_id'] = Synthesize.external_order_id()

        if not request_data.get('booking_method'):
            request_data['booking_method'] = 'shipping_and_return'

        with self.context.application.test_request_context():
            shipment = self.context.controller(ShipmentController).book_shipment(
                provider_name,
                request_data
            )
            if force_status and isinstance(force_status, (bytes, str)):
                shipment['status'] = force_status
                shipment = shipment.save(key='tracking_code')

        if not shipment:
            msg = 'could not book shipment with given params: {}'
            raise AssertionError(msg.format(request_data))

        if only_tracking_code:
            return shipment['tracking_code']

        return dict(shipment)


def create_controller(ControllerClass):
    """
    :param ControllerClass: a subclass of :py:class:`~acme_shipment_provider.web.controllers.Controller`
    :returns: an instance of the given controller, bound to the global ``application``
    """
    return ControllerClass(application)


def relative_path(path):
    """returns a version of the path that is relative to the test dao path"""
    return str(path.absolute().relative_to(dao_path))


def file_tree(path, pattern='**/*'):
    """returns a list of all (sub)children in a file-system directory
    """
    return list(sorted(map(relative_path, path.glob('**/*'))))


def s3_tree():
    """returns a list of all (sub)children in an S3 bucket
    """
    bucket = aws.bucket()
    return [o.key for o in bucket.objects.all()]


def prepare_app_client(context):
    """setup function for all HTTP endpoint tests

    Sets up a HttpDomainFlaskClient to generate documentation based on
    requests and responses.
    """
    httpretty.reset()
    context.application = application
    context.http = HttpDomainFlaskClient.from_app(
        application,
        documentation_path=documentation_path
    )
    context.dao = application.dao
    context.controller = create_controller
    context.create = FixtureFactory(context)
    if context.dao.path.is_dir():
        shutil.rmtree(context.dao.path, ignore_errors=True)


api_client = scenario(prepare_app_client)


def prepare_file_dao(context):
    """setup function for all file-system DAO tests.
    Removes any existing directory in the dao_path
    """
    context.path = dao_path
    if dao_path.is_dir():
        shutil.rmtree(dao_path, ignore_errors=True)

    context.dao = FileStorage(root_path=dao_path)


def prepare_s3_dao(context):
    """setup function for all file-system DAO tests.
    Creates a bucket before hand.

    .. warning:: all S3 DAO tests **MUST** run under a
    :py:func:`moto.mock_s3` decorator so we never hit actual AWS
    services.
    """
    context.path = dao_path
    if dao_path.is_dir():
        shutil.rmtree(dao_path, ignore_errors=True)

    context.dao = S3Storage()
    # create bucket
    response = context.dao.bucket.create()
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200, 'failed to create bucket for s3 dao'


def cleanup_s3_dao(context):
    """noop for now"""


def ensure_test_aws_credentials(context):
    """writes credentials to ``~/.aws``.  Even though :py:mod:`moto`
    intercepts real calls to AWS, :py:mod:`boto` still checks for
    credentials in the disk, so this ensures everything works before running tests.
    """
    aws.update_and_write_config_to_home()


with_file_dao = scenario([prepare_file_dao])

with_s3_dao = scenario([ensure_test_aws_credentials, prepare_s3_dao], [cleanup_s3_dao])
