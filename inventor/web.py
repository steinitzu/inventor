from __future__ import division

import logging
import os
import re
import math

from flask import Flask, request, g, redirect, url_for
from flask.ext import restful
from flask import make_response
from werkzeug import SharedDataMiddleware, secure_filename
from flask import send_from_directory

from . import config
from . import database

"""The inventory web client."""


log = logging.getLogger('inventor')


ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
# Regexp to check for a valid field name (only alnum and underscores)
FIELD_REGEXP = re.compile(r'^[A-Za-z0-9_]*$')

app = Flask(__name__, template_folder='static')

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'upload')
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

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

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

    def delete(self, entity_id=None):
        entity_id = entity_id or args.get('entity_id')
        return g.db.delete_entity(entity_id=entity_id, entity='item')

class ItemImage(restful.Resource):

    def _read(self, path):
        return open(path).read()

    def _return(self, filename):
        d = app.config['UPLOAD_FOLDER']
        exists = os.path.exists(os.path.join(d, filename))
        if not exists:
            return send_from_directory(d, 'placeholder.png')
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    def get(self, entity_id=None):
        ph = 'placeholder.png'
        args = request.args
        log.debug(args)
        entity_id = entity_id or args.get('entity_id')
        if not entity_id:
            return self._return(ph)
        log.debug('Getting item with id: %s', entity_id)
        log.debug('MIMETYPE: %s', request.mimetype)
        try:
            e = g.db.get_entity(entity_id=entity_id, entity='item')
        except database.NoSuchEntityError as e:
            return self._return(ph)
            restful.abort(404, message='No item with id: '+str(entity_id))
        pp = e['picture_path']
        log.debug('pp %s', pp)
        if not pp:
            return self._return(ph)
        return self._return(pp)

    def post(self):
        args = request.args
        log.debug('rargs: %s', args)
        entity_id = args['entity_id']
        e = g.db.get_entity(entity_id=entity_id, entity='item')        
        files = request.files
        log.debug('Request files: %s', files)
        log.debug('Request data: %s', request.data)
        file_ = files.values()[0]
        #file_ = request.files['file']        
        if file_ and allowed_file(file_.filename):
            filename = secure_filename(file_.filename)
            ext = os.path.splitext(filename)[1]
            filename = '{}{}'.format(entity_id, ext)
            file_.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            e['picture_path']=filename
            g.db.upsert_entity(e)
            return self.get(entity_id=entity_id)                      

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
        siblings = args.get('siblings') or []
        log.debug('Getting labels for %s id %s', entity, entity_id)
        if siblings:
            siblings = siblings.split(',')
            return g.db.sibling_labels(labels=siblings, entity='item')        
        return g.db.labels(entity_id, substring=substring, entity=entity)

    def post(self):
        """JSON string list should be provided as 
        request data and will be attached to given entity_id.
        """
        args = request.args
        entity_id = args.get('entity_id')
        entity = args.get('entity') or 'item'
        labels = args.get('labels') or ''
        labels = labels.split(',')
        log.debug('setting labels [%s] for %s with id: %s', 
                  labels,
                  entity, 
                  entity_id);
        g.db.attach_labels(entity_id, labels, entity)

    def delete(self):
        """Delete labels from entity.
        """
        args = request.args
        entity_id = args.get('entity_id')
        entity = args.get('entity') or 'item'
        labels = args.get('labels') or ''
        labels = labels.split(',')
        log.debug('request jason: %s', request.json)
        log.debug('Removing labels [%s] from %s with id: %s',
                  labels,
                  entity,
                  entity_id);
        g.db.remove_labels(entity_id, labels, entity)

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
api.add_resource(ItemImage, '/item_image')
api.add_resource(ItemImage, '/item_image/<int:entity_id>')

def main():
    config.read()
    app.debug = True
    app.run(host='0.0.0.0')

if __name__ == '__main__':
    main()
