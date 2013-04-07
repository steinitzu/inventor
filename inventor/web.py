from __future__ import division

import logging
import os
import re
import math

from flask import Flask, request, g
from flask.ext import restful
from flask import make_response
from werkzeug import SharedDataMiddleware

from . import config
from . import database

"""The inventory web client."""


log = logging.getLogger('inventor')

UPLOAD_FOLDER = '/path/to/the/uploads'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
# Regexp to check for a valid field name (only alnum and underscores)
FIELD_REGEXP = re.compile(r'^[A-Za-z0-9_]*$')

app = Flask(__name__, template_folder='static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config[''] = UPLOAD_FOLDER
api = restful.Api(app)
_db = None

def get_db():
    global _db
    if _db: return _db
    v = config['database']
    args = {}
    for key in v.keys():
        args[key] = v[key].get()
    return database.Database(**args)

@app.before_request
def before_request():
    g.db = get_db()    

class Item(restful.Resource):
    def get(self, entity_id=None):
        args = request.args
        log.debug(args)
        entity_id = entity_id or args.get('entity_id')
        log.debug('Getting item with id: %s', entity_id)
        log.debug('MIMETYPE: %s', request.mimetype)
        try:
            e = g.db.get_entity(entity_id=entity_id, entity='item')
        except database.NoSuchEntityError as e:
            restful.abort(404, message='No item with id: '+str(entity_id))
        else:
            return e.record

    def post(self):
        data = request.json
        log.debug(data)
        item = g.db.get_entity(data['id'], entity='item')
        status = 200 if item['id'] else 201
        item.update(data)
        g.db.upsert_entity(item)
        return item['id'], status

class Items(restful.Resource):
    def get(self):
        """Get items matching substringquery.
        """
        args = request.args
        labels = args.get('labels')
        pattern = args.get('pattern')
        labels = labels.split(',') if labels else None
        page = args.get('page') or 1

        orderkey = args.get('orderkey') or 'id'
        if not re.match(FIELD_REGEXP, orderkey):
            orderkey = 'id'
        order = args.get('order')
        if not order == 'asc' or order == 'desc':
            order = 'asc'

        order = orderkey+' '+order
        
        log.debug('Getting items with labels: %s', labels)

        kwargs = dict(query=pattern,
                      labels=labels,
                      entity='item',
                      page=int(page),
                      order=order)
        items = g.db.entities(**kwargs)
        kwargs['page'] = None
        itemcount = g.db.count_entities(**kwargs)
        if itemcount == 0:
            pagecount = 1
        else:
            limit = config['view']['pagelimit'].as_number()
            pagecount = int(math.ceil(itemcount/limit))
        return {'entities':[i.record for i in items],
                'pagecount':pagecount}

class Labels(restful.Resource):
    def get(self):
        """Get all labels matching entity and entity_id.
        If no id is provided, all saved labels for that entity are returned.
        """
        args = request.args
        entity_id = args.get('entity_id')
        entity = args.get('entity') or 'item'
        substring = args.get('substring')
        log.debug('Getting labels for %s id %s', entity, entity_id)
        return g.db.labels(entity_id, substring=substring, entity=entity)

    def post(self):
        """JSON string list should be provided as 
        request data and will be attached to given entity_id.
        """
        args = request.args
        entity_id = args.get('entity_id')
        entity = args.get('entity') or 'item'
        labels = request.json
        log.debug('setting labels [%s] for %s with id: %s', 
                  labels,
                  entity, 
                  entity_id);
        g.db.attach_labels(entity_id, labels, entity)

class Index(restful.Resource):
    def _read(self, path):
        return open(path).read()

    def get(self):
        p = os.path.join(app.static_folder, 'index.html')
        data = self._read(p)
        resp = make_response(data, 200)
        resp.mimetype = 'text/html'
        return resp

api.add_resource(Item, '/item')
api.add_resource(Item, '/item/<int:entity_id>')
api.add_resource(Items, '/items')
api.add_resource(Index, '/')
api.add_resource(Labels, '/labels')

def main():
    config.read()
    app.debug = True
    app.run(host='0.0.0.0')

if __name__ == '__main__':
    main()
