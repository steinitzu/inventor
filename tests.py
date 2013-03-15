import unittest as unittest
from decimal import Decimal

from inventor import db

class DBTest(unittest.TestCase):

    def setUp(self):
        self.db = db.Database()
        item = db.Item(self.db)
        item['name'] = 'testiboy'
        self.db.upsert_item(item)
        self.item = item

    def tearDown(self):
        self.db.execute_query('DELETE FROM item WHERE id = %s',
                              (self.item['id'],))
    def test_create_item(self):
        item = db.Item(self.db)
        item['name'] = 'testiboy'
        self.db.upsert_item(item)
        assert(isinstance(item['id'], int))

    def test_update_item(self):
        self.item['part_numbers'] = 'lolwatup'
        self.db.upsert_item(self.item)
        item = self.db.get_item(self.item['id'])
        assert(item['part_numbers'] == 'lolwatup')

    def test_wrong_type(self):
        with self.assertRaises(TypeError):
            self.item['created_at'] = 'fudge'
        with self.assertRaises(TypeError):
            self.item['sale_price'] = 'lolwatup'
        self.item['sale_price'] = 50
        assert(isinstance(self.item['sale_price'], Decimal))
        

    

unittest.main()
