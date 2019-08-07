# -*- coding: utf-8 -*-

from tests.functional.scenarios import with_file_dao
from tests.functional.scenarios import file_tree
from acme_shipment_provider.dao import ActiveRecord


@with_file_dao
def test_delete(context):
    ("ActiveRecord.delete(key) should delete an existing file record")

    # Given a namespaced dao
    dao = context.dao.of('offers')

    # And a new ActiveRecord
    record = ActiveRecord(dao)
    record.update({
        'offer_id': '308f2df8-84d3-4100-b091-19467db73eed',
        'city': 'New York',
        'address': '123 Main St.',
    })
    record.save(key='offer_id')

    # When I delete it
    record.delete(key='offer_id')

    # Then no records should exist
    file_tree(context.path).should.equal([
        'offers',
        'offers/offer_id',
    ])
