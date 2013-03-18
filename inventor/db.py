import sys
import decimal

from psycopg2.pool import ThreadedConnectionPool
from psycopg2 import DatabaseError
import psycopg2
import psycopg2.extras

#{'entity':{'column':psqltype}}
COLUMN_TYPES = {}

class NoSuchItemError(Exception):
    pass

class ThreadedPool(ThreadedConnectionPool):    

    def _connect(self, key=None):
        """Modified from superclass.\n
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

    def clear_dirty(self):
        self.dirty = {}

    def __setitem__(self, key, value):
        if key not in self:
            raise KeyError('{} is not a valid key.'.format(key))
        elif value != self[key]:
            super(FixedDict, self).__setitem__(key, value)
            self.dirty[key] = True

class Entity(object):
    name = 'entity'
    def __init__(self, database, values=None):
        self.database = database
        self.record = None
        self.fill(values)

    def fill(self, values=None):
        self.record = FixedDict(COLUMN_TYPES[self.name].keys(), values)

    def __getitem__(self, key):
        return self.record[key]

    def __setitem__(self, key, value):
        value = self.database.cast_value(self.name,key,value)
        self.record[key] = value        

    def is_dirty(self, key=None):
        """Checks if given key is dirty.
        Returns True if any field has been modified and no key is provided.
        """
        if not key:
            #this double negative is not an error
            return not not self.record.dirty
        return key in self.record.dirty

class Item(Entity):
    name = 'item'

class Database(object):

    def __init__(self):
        self.pool = ThreadedConnectionPool(
            4, 15,
            'dbname=inventor host=deathstar user=steini')
        COLUMN_TYPES.update(self.get_column_types(['item']))

    def _labels_query(self, labels, fields='*', joiner='and'):
        """Generate a query matching given labels.        
        """
        q = 'SELECT DISTINCT {0} FROM item AS i WHERE'
        joiner = joiner.lower()
        clauses = []
        subvals = []
        for label in labels:
            if joiner == 'and':
                clause = '''EXISTS (SELECT 1 FROM item_label AS il 
                         WHERE il.label = %s AND il.entity_id = i.id)'''
            else:
                clause = '(label = %s)'
            clauses.append(clause)
            subvals.append(label)

        clause = (' '+joiner+' ').join(clauses)
        if joiner == 'or':
            clause = '''WHERE id IN (
                    SELECT entity_id FROM item_labels WHERE 
                    ({0}));'''.format(clause)            
        return q.format(fields)+' '+clause,subvals

    def _select_query(self, where='', subvals=(), fields='*'):
        q = 'SELECT {0} FROM item '.format(fields)
        return q+' '+where, subvals

    def execute_query(self, query, subvals=()):
        conn = self.pool.getconn()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(query, subvals)
            conn.commit()
            try:
                result = cur.fetchall()
            except psycopg2.ProgrammingError:
                #should just mean there are no results
                result = [] 
        finally:
            self.pool.putconn(conn)
        return result

    def write_query(self, query, subvals=()):
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
        return [Item(self,row) for row in self.execute_query(query,subvals)]

    def get_item(self, item_id=None, as_dict=False):
        """Returns the Item with given `item_id`.
        If no id is provided, returns a new Item.
        When `as_dict` is True, the item is returned as a plain dict.
        """
        if not item_id:
            r = Item(self)
            if as_dict: return dict(r.record)
            return r

        r = self.execute_query(
            'SELECT * FROM item WHERE id = %s', (item_id,))
        try:
            if as_dict:
                return dict(r[0])
            else:
                return Item(self,r[0])
        except IndexError:
            raise NoSuchItemError('id: '+str(item_id))

    def upsert_item(self, item):
        """Save given item to the database.
        """
        #TODO: Don't save when item is clean.
        cols = COLUMN_TYPES[item.name].keys()
        if item['id']:
            query = 'UPDATE item SET {0} WHERE id = %s'
            clauses = []
            subvals = []
            for f in cols:
                if item.is_dirty(f):
                    clauses.append(f+' = %s')
                    subvals.append(item[f])
            subvals.append(item['id'])
            query = query.format(' , '.join(clauses))
        else:
            query = 'INSERT INTO item ({0}) VALUES ({1})'
            subvals = []
            scols = []
            for f in cols:
                if item.is_dirty(f):
                    subvals.append(item[f])
                    scols.append(f)
            fields = ','.join(scols)
            subholders = ','.join(['%s' for k in scols])
            query = query.format(fields, subholders)
        itemid = self.write_query(query, subvals)
        if item['id']:
            itemid = item['id']
        newitem = self.get_item(itemid, as_dict=True)
        item.fill(newitem)

    def attach_labels(self, item_id, labels):
        """Attach given list of labels to given item_id."""
        if isinstance(item_id, Item):
            item_id = item_id['id']
        q = 'INSERT INTO item_label (label, entity_id) VALUES (%s, %s)'
        for l in labels:
            self.write_query(q, (l,item_id))

    def remove_labels(self, item_id, labels):
        """Remove given list of labels from given item(id)."""
        if isinstance(item_id, Item):
            item_id = item_id['id']
        q = 'DELETE FROM item_label WHERE label = %s AND entity_id = %s'        
        for l in labels:
            self.execute_query(q, (l, item_id))

    def cast_value(self, entity_type, column, value):
        """Attempt to cast given `value` to its proper type 
        based on `COLUMN_TYPES`.
        The resulting type should be the python type which corresponds 
        to the sql type in `COLUMN_TYPES`.
        """
        conn = self.pool.getconn()
        cur = conn.cursor()
        tmap = COLUMN_TYPES[entity_type]

        sqltype = None

        sqltype = tmap[column]

        if isinstance(value, unicode):
            value = value.encode('utf-8')
        elif value is None:
            pass
        elif isinstance(value, bool):
            #special case for booleans (cause pg wants 'true', lower case)
            pass
        else:
            value = str(value)
                        
        res = None
        try:
            res = cur.cast(sqltype, value)
        except (psycopg2.Error, decimal.InvalidOperation):
            msg = '"{}" is not a valid value for column "{}" of entity "{}"'\
                .format(value, column, entity_type)
            raise TypeError(msg), None, sys.exc_info()[2]
        finally:
            self.pool.putconn(conn)
        return res        

    def get_column_types(self, entities):
        """Make the type map for entity tables.
        `entities` should be a list of table/view names 
        from the database (e.g. 'items').
        """
        tmap = {}
        typesubs = {
            'timestamp without time zone' : 'timestamp',
            'character varying' : 'varchar',
            'character' : 'char',
            'boolean' : 'bool',
            'integer' : 'int4',
            }
        q = """SELECT t.table_name,
            c.column_name, c.data_type 
            FROM information_schema.tables AS t 
            INNER JOIN information_schema.columns AS c 
            ON c.table_name = t.table_name 
            WHERE t.table_name = %s"""
    
        oidq = 'SELECT oid FROM pg_type WHERE typname = %s'
     
        for entity in entities:
            data = self.execute_query(q, (entity,))
            tmap[entity] = {}
            for row in data:
                strtype = row['data_type']
                try:
                    strtype = typesubs[strtype]
                except KeyError: pass
                coloidtype = int(self.execute_query(oidq, (strtype,))[0][0])
                tmap[entity][row['column_name']] = coloidtype
        return tmap
