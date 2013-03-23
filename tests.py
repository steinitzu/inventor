import unittest as unittest
from decimal import Decimal

from inventor import db

class DBTest(unittest.TestCase):

    def setUp(self):
        self.db = db.Database(user='steini', database='inventortest')
        item = db.Item(self.db)
        item['name'] = 'testiboy'
        self.db.upsert_entity(item)
        self.item = item

    def tearDown(self):
        self.db.query('DELETE FROM item WHERE 1 = 1;')

    def test_create_item(self):
        item = db.Item(self.db)
        item['name'] = 'testiboy'
        self.db.upsert_entity(item)
        assert(isinstance(item['id'], int))

    def test_update_item(self):
        self.item['part_numbers'] = 'lolwatup'
        self.db.upsert_entity(self.item)
        item = self.db.get_entity(self.item['id'])
        assert(item['part_numbers'] == 'lolwatup')

    def test_wrong_type(self):
        with self.assertRaises(TypeError):
            self.item['sale_price'] = 'lolwatup'
        self.item['sale_price'] = 50
        assert(isinstance(self.item['sale_price'], Decimal))

    def test_attach_label(self):
        self.db.attach_labels(self.item['id'], ['blubber'], entity='item')
        q = db.LabelQuery('blubber', entity='item')
        items = self.db.entities(query=q, entity='item')
        assert(items.next()['id'] == self.item['id'])

    def test_remove_label(self):
        self.db.attach_labels(self.item['id'], ['blubber'], entity='item')
        self.db.remove_labels(self.item['id'], ['blubber'], entity='item')
        q = db.LabelQuery('blubber', entity='item')
        items = self.db.entities(query=q, entity='item')
        assert(not items.rows)
        

    

unittest.main()
