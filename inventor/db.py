import sys
import decimal
import os

from psycopg2.pool import ThreadedConnectionPool
from psycopg2 import DatabaseError
import psycopg2
import psycopg2.extras

from .util import FixedDict

#{'entity':{'column':psqltype}} (generated in Database on __init__)
COLUMN_TYPES = {}
# {'entity_name':['columns'...]} or {'universal':['columns'...]}
READ_ONLY_COLUMNS = {}

DB_FORMAT_STR = '%s'

class NoSuchEntityError(Exception):
    pass

class ColumnNotWriteable(Exception):
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

class Entity(object):
    """An Entity is a data structure which represents a 
    database table. Each instance is a single row.
    """
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
        roc = READ_ONLY_COLUMNS
        if key in roc['universal'] or key in roc[self.name]:
            raise ColumnNotWriteable(key)
        value = self.database.cast_value(self.name,key,value)
        self.record[key] = value

    def is_dirty(self, key=None):
        """Checks if given key is dirty.
        Returns True if any field has been modified and no key is provided.
        """
        return self.record.is_dirty(key=key)

class Item(Entity):
    name = 'item'

# TODO: Register classes on creation and add here (plugin stuff)
ENTITY_CLASSES = {'item':Item}

# Query class idea tolen from beets by Adrian Sampson #
class Query(object):

    def clause(self):
        """Return the WHERE clause for given query and subvals iterable.
        """
        raise NotImplementedError()

class FieldQuery(Query):
    def __init__(self, field, pattern):
        self.field = field
        self.pattern = pattern

class MatchQuery(FieldQuery):
    """Looks for exact matches in given field."""
    
    def clause(self):        
        return '{} = {}'.format(
            self.field, DB_FORMAT_STR), (self.pattern,)

class SubStringQuery(FieldQuery):

    def clause(self):
        return '{} LIKE %{}%'.format(
            self.field, DB_FORMAT_STR), (self.pattern,)

class SubStringQueryCaseLess(FieldQuery):

    def clause(self):
        return '{} ILIKE %{}%'.format(
            self.field, DB_FORMAT_STR), (self.pattern,)

class LabelQuery(Query):
    def __init__(self, label, entity='item'):
        self.label = label
        self.entity = entity

    def clause(self):
        c = '''EXISTS (SELECT 1 FROM {}_label AS il 
            WHERE il.label = {} AND il.entity_id = entity.id)'''.format(
            self.entity, DB_FORMAT_STR)
        return c, (self.label,)


class MultiQuery(Query):
    """Makes one query out of many field queries."""
    
    def __init__(self, subqueries=()):
        self.subqueries = [i for i in subqueries]

    def clause_with_joiner(self, joiner='or'):

        clauses = []
        subvals = []
        joiner = joiner.lower()
        for subq in self.subqueries:
            clause, subs = subq.clause()
            clauses.append('('+clause+')')
            subvals += subs
        clause = (' '+joiner+' ').join(clauses)
        return clause, subvals

    def clause(self):
        return self.clause_with_joiner('or')
#

class ResultIterator(object):
    entity_cls = {'item' : Item}
    def __init__(self, db, rows, entity='item', offset=0):
        self.rows = rows
        self.entity = self.entity_cls[entity]
        self.offset = offset
        self.db = db

    def __iter__(self):
        return self

    def next(self):
        try:
            row = self.rows[self.offset]
        except:
            raise StopIteration
        ent = self.entity(self.db, row)
        self.offset+=1
        return ent    

class Database(object):

    def __init__(self, 
                 host='localhost', database='inventor', user='', password=''):
        args = {}
        if host != 'localhost':
            args['host'] = host
        if password:
            args['password'] = password
        args['database'] = database
        args['user'] = user

        self.pool = ThreadedPool(4, 15, **args)            

        #update the database schema (database must exist)
        schema = open(os.path.join(os.path.dirname(__file__), 
                                   'schema.sql')).read()
        self.query(schema)
        self._init_data()

        COLUMN_TYPES.update(self.get_column_types(['item']))
        READ_ONLY_COLUMNS.update(self.get_read_only_columns())

    def _init_data(self):
        """Put some base data in the database, if not exists."""

        q = """INSERT INTO read_only(table_name,column_name) 
               VALUES ('universal','id') ;
            INSERT INTO read_only(table_name,column_name) 
               VALUES ('universal','created_at');
            INSERT INTO read_only(table_name,column_name) 
               VALUES ('universal','modified_at');"""
        try:
            self.query(q)
        except psycopg2.IntegrityError:
            pass #uniques already exists

    def query(self, query, subvals=()):
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

    def script(self, script, vars):
        """Execute an sql script."""
        conn = self.pool.getconn()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.executemany(script, vars)
            conn.commit()
        finally:
            self.pool.putconn(conn)

    def mutate(self, query, subvals=()):
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

    def entities(self, labels=None, query=None, entity='item', order='id desc'):
        normalq = '''SELECT * FROM {} AS entity'''.format(entity)
        labelqueries = []
        queries = []

        if labels:
            labelqueries = [LabelQuery(l, entity) for l in labels]
        if isinstance(query, Query):
            queries.append(query)
        elif isinstance(query, list) or isinstance(query, tuple):
            [queries.append(q) for q in query]
        else:
            raise NotImplementedError(
                'String queries and whatnot unimplemented')
        qs = queries+labelqueries
        q = MultiQuery(qs)
        clause, subvals = q.clause()
        if not clause:
            query = normalq+' ORDER BY'+order
        else:
            query = normalq+' WHERE {} ORDER BY {}'.format(clause, order)
        return ResultIterator(self, self.query(query,subvals), entity=entity)        


    def get_entity(self, entity_id=None, as_dict=False, entity='item'):
        """Returns the Entity with given `entity_id`.
        If no id is provided, returns a new Entity.
        When `as_dict` is True, the entity is returned as a plain dict.
        """
        strentity = entity
        entity = ENTITY_CLASSES[entity]
        if not entity_id:
            r = entity(self)
            if as_dict: return dict(r.record)
            return r

        q = MatchQuery('id', entity_id)
        r = self.entities(query=q, entity=strentity)
        try:
            if as_dict:
                return dict(r.rows[0])
            else:
                return r.next()
        except (IndexError, StopIteration):
            raise NoSuchEntityError('type: {} id: {} '.format(
                    strentity, entity_id))

    def upsert_entity(self, obj, entity='item'):
        """Save given entity to the database.
        """
        #TODO: Don't save when entity is clean.
        cols = COLUMN_TYPES[obj.name].keys()
        if obj['id']:
            query = 'UPDATE {} SET {} WHERE id = %s'
            clauses = []
            subvals = []
            for f in cols:
                if obj.is_dirty(f):
                    clauses.append(f+' = %s')
                    subvals.append(obj[f])
            subvals.append(obj['id'])
            query = query.format(entity, ' , '.join(clauses))
        else:
            query = 'INSERT INTO {} ({}) VALUES ({})'
            subvals = []
            scols = []
            for f in cols:
                if obj.is_dirty(f):
                    subvals.append(obj[f])
                    scols.append(f)
            fields = ','.join(scols)
            subholders = ','.join(['%s' for k in scols])
            query = query.format(entity, fields, subholders)
        entityid = self.mutate(query, subvals)
        if obj['id']:
            entityid = obj['id']
        newobj = self.get_entity(entityid, as_dict=True)
        obj.fill(newobj)

    def attach_labels(self, entity_id, labels, entity='item'):
        """Attach given list of labels to given entity_id."""
        if isinstance(entity_id, Item):
            entity_id = entity_id['id']
        q = '''INSERT INTO {}_label (label, entity_id) 
             VALUES (%s, %s)'''.format(entity)
        for l in labels:
            self.mutate(q, (l,entity_id))

    def remove_labels(self, entity_id, labels, entity='item'):
        """Remove given list of labels from given item(id)."""
        if isinstance(entity_id, Item):
            entity_id = entity_id['id']
        q = '''DELETE FROM {}_label 
            WHERE label = %s AND entity_id = %s'''.format(entity)
        for l in labels:
            self.mutate(q, (l, entity_id))

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
            data = self.query(q, (entity,))
            tmap[entity] = {}
            for row in data:
                strtype = row['data_type']
                try:
                    strtype = typesubs[strtype]
                except KeyError: pass
                coloidtype = int(self.query(oidq, (strtype,))[0][0])
                tmap[entity][row['column_name']] = coloidtype
        return tmap

    def get_read_only_columns(self):
        """Get the read only columns as a dict.
        {table_name:[columns]}
        will always have a universal key for columns which are always 
        read only regardless of the table.
        """
        q = 'SELECT * FROM read_only'
        d = {}
        for key in ENTITY_CLASSES:
            d[key] = []
        for row in self.query(q):
            key = row['table_name']
            if not d.has_key(key):
                d[key] = []
            d[key].append(row['column_name'])
        return d

