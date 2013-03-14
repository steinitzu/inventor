from psycopg2.pool import ThreadedConnectionPool
from psycopg2 import DatabaseError
import psycopg2
import psycopg2.extras


ITEM_FIELDS = (
    'id', 'created_at', 'modified_at', 
    'name', 'part_numbers', 'location', 'sale_price',
    'quantity', 'unit', 'condition', 'info', 'picture_path')
ITEM_FIELDS_WRITEABLE = (
    'name', 'part_numbers', 'location', 'sale_price',
    'quantity', 'unit', 'condition', 'info', 'picture_path')

class NoSuchItemError(Exception):
    pass

class ThreadedPool(ThreadedConnectionPool):    

    def _connect(self, key=None):
        """
        Modified from superclass.\n
        New connections are unicode connections.
        """
        conn = psycopg2.connect(*self._args, **self._kwargs)
        conn.set_client_encoding('UTF-8')
        psycopg2.extensions.register_type(psycopg2.extensions.UNICODE, conn)
        psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY, conn)
        if key is not None:
            self._used[key] = conn
            self._rused[id(conn)] = key
        else:
            self._pool.append(conn)
        return conn

class FixedDict(dict):
    """A dict where keys can not be added after creation and keys are marked 
    as 'dirty' when their values are changed.
    Accepts a list of `keys` and an optional `values` which should 
    be a dict compatible object.
    Any key not in `values` will be implicitly added and given a `None` value.
    """
    def __init__(self, keys, values=None):
        values = values or {}
        super(FixedDict, self).__init__(values)
        seti = super(FixedDict, self).__setitem__
        for key in keys:
            if not key in self:
                seti(key, None)
        self.dirty = {}

    def __setitem__(self, key, value):
        if key not in self:
            raise KeyError('{} is not a valid key.'.format(key))
        elif value != self[key]:
            super(FixedDict, self).__setitem__(key, value)
            self.dirty[key] = True

class Item(object):
    
    def __init__(self, values=None):
        self.fill(values)

    def fill(self, values=None):
        self.record = FixedDict(ITEM_FIELDS, values)

    def __getitem__(self, key):
        return self.record[key]

    def __setitem__(self, key, value):
        self.record[key] = value

    def is_dirty(self, key=None):
        """Checks if given key is dirty.
        Returns True if any field has been modified if no key is provided.
        """
        if not key:
            return not not self.record.dirty
        return key in self.record.dirty
        

class Database(object):

    def __init__(self):
        self.pool = ThreadedConnectionPool(
            4, 15,
            'dbname=inventor host=deathstar user=steini')

    def _labels_query(self, labels, fields='*', joiner='and'):
        """Generate a query matching given labels.        
        """
        q = 'SELECT DISTINCT {0} FROM items AS i WHERE'
        joiner = joiner.lower()
        clauses = []
        subvals = []
        for label in labels:
            if joiner == 'and':
                clause = '''EXISTS (SELECT 1 FROM item_labels AS il 
                         WHERE il.label = %s AND il.entity_id = i.id)'''
            else:
                clause = '(label = %s)'
            clauses.append(clause)
            subvals.append(label)

        clause = (' '+joiner+' ').join(clauses)
        if joiner == 'or':
            clause = '''WHERE id IN (
                    SELECT entity_id FROM labels WHERE 
                    ({0}));'''.format(clause)            
        return q.format(fields)+' '+clause,subvals

    def _select_query(self, where='', subvals=(), fields='*'):
        q = 'SELECT {0} FROM items '.format(fields)
        return q+' '+where, subvals

    def execute_query(self, query, subvals):
        conn = self.pool.getconn()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(query, subvals)
            conn.commit()
            result = cur.fetchall()
        finally:
            self.pool.putconn(conn)
        return result

    def write_query(self, query, subvals):
        """Run a query and return last modified id.
        """
        conn = self.pool.getconn()
        query+=' RETURNING id'
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(query, subvals)
            conn.commit()
            result = cur.fetchone()[0]
        finally:
            self.pool.putconn(conn)
        return result        

    def items(self, labels=None, where='', subvals=(), fields='*', joiner='and'):
        if labels:
            query,subvals = self._labels_query(labels, fields, joiner)
        else:
            query,subvals = self._select_query(where, subvals, fields)
        return [Item(row) for row in self.execute_query(query,subvals)]

    def get_item(self, item_id, as_row=False):
        r = self.execute_query(
            'SELECT * FROM items WHERE id = %s', (item_id,))        
        try:
            if as_row:
                return r[0]
            else:
                return Item(r[0])
        except IndexError:
            raise NoSuchItemError('id: '+str(item_id))

    def upsert_item(self, item):
        """Save given item to the database.
        """
        #TODO: Don't save when item is clean.
        if item['id']:
            query = 'UPDATE items SET {0} WHERE id = %s'
            clauses = []
            subvals = []
            for f in ITEM_FIELDS_WRITEABLE:
                if item.is_dirty(f):
                    clauses.append(f+' = %s')
                    subvals.append(item[f])
            subvals.append(item.id)
            query = query.format(' , '.join(clauses))
        else:
            query = 'INSERT INTO items ({0}) VALUES ({1})'
            fields = ','.join(ITEM_FIELDS_WRITEABLE)
            subholders = ','.join(['%s' for k in ITEM_FIELDS_WRITEABLE])
            subvals = []
            for f in ITEM_FIELDS_WRITEABLE:
                subvals.append(item[f])
            query = query.format(fields, subholders)
        itemid = self.write_query(query, subvals)
        if item['id']:
            itemid = item['id']
        newitem = self.get_item(itemid, as_row=True)
        item.fill(newitem)

    def attach_labels(self, item_id, labels):
        """Attach given list of labels to given item_id."""
        if isinstance(item_id, Item):
            item_id = item_id['id']
        q = 'INSERT INTO item_labels (label, entity_id) VALUES (%s, %s)'
        for l in labels:
            self.write_query(q, (l,item_id))

    def remove_labels(self, item_id, labels):
        """Remove given list of labels from given item(id)."""
        if isinstance(item_id, Item):
            item_id = item_id['id']
        q = 'DELETE FROM item_labels WHERE label = %s AND entity_id = %s'        
        for l in labels:
            self.execute_query(q, (l, item_id))
