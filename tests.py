import unittest as unittest
from decimal import Decimal
import random
import string
import json
import logging

import inventor
from inventor import database, web
from inventor.database import ColumnNotWriteable

log = logging.getLogger('inventor')
log.setLevel(logging.CRITICAL)

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
        vars = (_randstring(),
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
    cls =database.ENTITY_CLASSES[e]

    es = [cls(dbb) for i in range(count)]
    for entity in es:
        _fill_entity(entity)
    return es

def fill_db(dbb, count=10, e='item'):
    es = get_entities(dbb, count, e)
    for e in es:
        dbb.upsert_entity(e)

def _make_labels(db, items, count=20):
    """Attach random labels to given list of items.
    Returns a dict {item_id : [labels...]}
    """
    labels = [_randstring() for i in range(count)]
    
    id_label = {}
    for item in items:
        id_label[item['id']] = []
    for label in labels:
        item = items[_randint(0,len(items)-1)]
        db.attach_labels(item, [label], entity='item')
        id_label[item['id']].append(label.lower())
    return id_label


class DBTest(unittest.TestCase):

    def setUp(self):
        self.db =database.Database(user='steini', dbname='inventortest')
        self.items = get_entities(self.db)


        # TODO: drop self.item
        item =database.Item(self.db)
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
        
        id_label = _make_labels(self.db, self.items)

        for key,value in id_label.iteritems():
            if not value: continue
            items = self.db.entities(labels=value, entity='item')
            assert(len(items.rows) == 1)
            assert(items.next()['id'] == key)

    def test_remove_label(self):
        self.db.attach_labels(self.item['id'], ['blubber'], entity='item')
        self.db.remove_labels(self.item['id'], ['blubber'], entity='item')
        q =database.LabelQuery('blubber', entity='item')
        items = self.db.entities(query=q, entity='item')
        assert(not items.rows)

    def test_get_labels(self):
        """Attaches random labels and tries retrieving them from 
        db for each item."""
        for item in self.items:
            self.db.upsert_entity(item)
        idlabel = _make_labels(self.db, self.items)
        for i,labels in idlabel.iteritems():
            dblabels = self.db.labels(i, 'item')
            assert(sorted(dblabels) == sorted(labels))

class RestTest(unittest.TestCase):

    def setUp(self):
        config = inventor.config
        config['database']['user'] = 'steini'
        config['database']['dbname'] = 'inventortest'

        self.app = web.app.test_client()
        self.db = web.get_db()        

        self.items = get_entities(self.db)
        for i in self.items:
            self.db.upsert_entity(i)

    def _decode(self, data):
        return json.JSONDecoder().decode(data)

    def tearDown(self):
        self.db.query('DELETE FROM item WHERE 1 = 1;')
        self.db.query('DELETE FROM item_label WHERE 1 = 1;')

    def test_get_item_by_id(self):
        rv = self.app.get('/item/{}'.format(self.items[0]['id']))
        d = self._decode(rv.data)
        od = self.items[0].record
        assert((d['id'],d['name'],d['info']) == (od['id'],od['name'],od['info']))

    def test_get_items(self):
        rv = self.app.get('/items')
        d = self._decode(rv.data)
        assert(len(d) == len(self.items))        

    def test_get_items_by_label(self):
        self.db.attach_labels(self.items[0], ['shit', 'piss', 'cunt'])
        rv = self.app.get('/items?labels=shit,piss,cunt')
        d = self._decode(rv.data)
        od = self.items[0].record
        assert((d[0]['id'],d[0]['name'],d[0]['info']) == 
               (od['id'],od['name'],od['info']))
        assert(len(d) == 1)

    def test_get_items_by_pattern(self):
        """Get items by substring."""
        item = self.items[0]
        pattern = item['name']
        rv = self.app.get('/items?pattern={}'.format(pattern))
        d = self._decode(rv.data)
        od = item.record
        assert((d[0]['id'],d[0]['name'],d[0]['info']) == 
               (od['id'],od['name'],od['info']))
        assert(len(d) == 1)

    def test_get_items_by_pattern_and_label(self):
        item = self.items[0]
        labels = ['shit', 'piss', 'cunt']
        self.db.attach_labels(item, labels)
        self.db.attach_labels(self.items[1], labels)
        pattern = item['name']
        rv = self.app.get('/items?pattern={}&labels={}'.format(
                pattern, ','.join(labels)))
        d = self._decode(rv.data)
        od = item.record
        assert((d[0]['id'],d[0]['name'],d[0]['info']) == (od['id'],od['name'],od['info']))
        assert(len(d) == 1)

    def test_put_new_item(self):
        item = get_entities(self.db, 1)[0]
        log.debug(item.record)
        data = self.app.put('/item')
        log.debug(data)
    
if __name__ == '__main__':
    unittest.main()
