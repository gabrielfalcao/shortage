# -*- coding: utf-8 -*-
from moto import mock_s3
from tests.functional.scenarios import with_s3_dao
from tests.functional.scenarios import s3_tree


@mock_s3
@with_s3_dao
def test_s3_store_save(context):
    ("S3Storage.persist(item, key) should create a "
     "s3 named under namespace/key/value")

    # Given a namespaced dao
    dao = context.dao.of('offers')

    # And a new ActiveRecord
    uuid1 = '308f2df8-84d3-4100-b091-19467db73eed'
    record = dao.new(offer_id='fortytwo', uuid=uuid1)
    record['address'] = '123 Main St.'
    record.update({
        'city': 'New York'
    })

    # When I persist the ActiveRecord
    persisted = dao.persist(record, 'offer_id')

    # Then a s3-tree should have been created based on the key/value
    dao.list_all().should.equal([
        record
    ])
    # And it should have returned the persisted record
    record.should.equal(persisted)
    s3_tree().should.equal([
        'acme-dao-prefix/offers/offer_id/757ba69fd154ee1ebdf54b3e3fd0a26de3e02db2',
    ])


@mock_s3
@with_s3_dao
def test_store_list_all(context):
    ("S3Storage.list_all() "
     "should return an created")
    dao = context.dao
    dao.list_all('offers').should.have.length_of(0)

    record = dao.of('offers').new()
    record.update({
        'offer_id': '308f2df8-84d3-4100-b091-19467db73eed',
        'city': 'New York',
        'address': '123 Main St.',
    })

    record.save(key='offer_id')
    all_offers = dao.list_all('offers')
    all_offers.should_not.be.empty
    all_offers[0].should.equal(record)


@mock_s3
@with_s3_dao
def test_store_retrieve_by_key(context):
    ("S3Storage.retrive_by(offer_id='fortytwo') "
     "should return an ActiveRecord")

    dao = context.dao

    record = dao.of('offers').new()
    record.update({
        'offer_id': 'i-am-a-unique-id',
        'city': 'New York',
        'address': '123 Main St.',
    })

    record.save(key='offer_id')

    s3_tree().should.equal([
        'acme-dao-prefix/offers/offer_id/95513cb8dd373b33e6d3d72ec44950b660d89792',
    ])
    result = dao.of('offers').retrieve_by(offer_id='i-am-a-unique-id')
    result.should.equal(record)
