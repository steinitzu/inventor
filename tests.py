import unittest as unittest

from inventor import db

class TestDB(unittest.TestCase):

    def setUp(self):
        self.db = db.Database()

    def create_item(self):
        item = db.Item()
        item['name'] = 'testiboy'
        self.db.upsert_item(item)
        assert(isinstance(item['id'], int))

unittest.main()
