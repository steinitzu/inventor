import unittest as unittest
from decimal import Decimal
import random
import string

from inventor import db
from inventor.db import ColumnNotWriteable

RANDOMS = []

def _randstring(length=15):
    s = ''
    while True:
        s = ''.join(
            random.choice(string.letters+string.digits) for x in range(length))
        if s in RANDOMS:
            continue
        else:
            break
    return s

def _randint(min=0, max=500):
    return random.randint(0,max)

def _randdecimal(max=500):
    a = _randint(max=max)
    b = _randint(max=99)
    return Decimal(str(a)+'.'+str(b))


def _fill_entity(entity):
    for key in entity.keys():
        vars = (_randstring(_randint(min=10,max=30)),
                _randint(),
                _randdecimal())
        for v in vars:
            try:
                entity[key] = v
            except ColumnNotWriteable:
                break
            except TypeError:
                continue
            else:
                break

def get_entities(dbb, count=10, e='item'):
    """Get some entities with random data."""
    cls = db.ENTITY_CLASSES[e]

    es = [cls(dbb) for i in range(10)]
    for entity in es:
        _fill_entity(entity)
    return es


class DBTest(unittest.TestCase):

    def setUp(self):
        self.db = db.Database(user='steini', database='inventortest')
        self.items = get_entities(self.db)


        # TODO: drop self.item
        item = db.Item(self.db)
        item['name'] = 'testiboy'
        self.db.upsert_entity(item)
        self.item = item

    def tearDown(self):
        self.db.query('DELETE FROM item WHERE 1 = 1;')
        self.db.query('DELETE FROM item_label WHERE 1 = 1;')

    def test_insert_item(self):
        for item in self.items:
            self.db.upsert_entity(item)
            newitem = self.db.get_entity(item['id'], entity='item')
            assert(newitem.record == item.record)

    def test_update_item(self):
        for item in self.items:
            self.db.upsert_entity(item)
            item['name'] = _randstring()
            oldmtime = item['modified_at']
            self.db.upsert_entity(item)
            assert(oldmtime < item['modified_at'])

    def test_wrong_type(self):
        with self.assertRaises(TypeError):
            self.items[0]['sale_price'] = _randstring()
        self.items[0]['sale_price'] = _randint()
        assert(isinstance(self.items[0]['sale_price'], Decimal))    

    def test_attach_search_label(self):
        """Test setting and searching by labels."""
        for item in self.items:
            self.db.upsert_entity(item)
        labels = [_randstring() for i in range(20)]
        
        id_label = {}
        for item in self.items:
            id_label[item['id']] = []

        for label in labels:
            item = self.items[_randint(0,len(self.items)-1)]
            self.db.attach_labels(item, [label], entity='item')
            id_label[item['id']].append(label.lower())

        for key,value in id_label.iteritems():
            if not value: continue
            items = self.db.entities(labels=value, entity='item')
            assert(len(items.rows) == 1)
            assert(items.next()['id'] == key)


    def test_remove_label(self):
        self.db.attach_labels(self.item['id'], ['blubber'], entity='item')
        self.db.remove_labels(self.item['id'], ['blubber'], entity='item')
        q = db.LabelQuery('blubber', entity='item')
        items = self.db.entities(query=q, entity='item')
        assert(not items.rows)
        

    
if __name__ == '__main__':
    unittest.main()
