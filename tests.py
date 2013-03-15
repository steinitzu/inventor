import unittest as unittest

from inventor import db

class DBTest(unittest.TestCase):

    def setUp(self):
        self.db = db.Database()
        item = db.Item()
        item['name'] = 'testiboy'
        self.db.upsert_item(item)
        self.item = item

    def tearDown(self):
        self.db.execute_query('DELETE FROM item WHERE id = %s',
                              (self.item['id'],))
    def test_create_item(self):
        item = db.Item()
        item['name'] = 'testiboy'
        self.db.upsert_item(item)
        assert(isinstance(item['id'], int))

    def test_update_item(self):
        self.item['part_numbers'] = 'lolwatup'
        self.db.upsert_item(self.item)
        item = self.db.get_item(self.item['id'])
        assert(item['part_numbers'] == 'lolwatup')

    

unittest.main()
