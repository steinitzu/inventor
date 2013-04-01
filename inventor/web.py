"""The inventory web client."""

import logging
import os

from flask import Flask, request, g
from flask.ext import restful
from flask import make_response
from werkzeug import SharedDataMiddleware

from . import config
from . import db

log = logging.getLogger('inventor')

UPLOAD_FOLDER = '/path/to/the/uploads'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

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
    return db.Database(**args)

@app.before_request
def before_request():
    g.db = get_db()    

class Item(restful.Resource):
    def get(self, entity_id=None):
        log.debug('Getting item with id: %s', entity_id)
        log.debug('MIMETYPE: %s', request.mimetype)
        try:
            e = g.db.get_entity(entity_id=entity_id, entity='item')
        except db.NoSuchEntityError as e:
            restful.abort(404, message='No item with id: '+str(entity_id))
        else:
            return e.record

    def put(self):
        data = request.form['data']
        log.debug(data)
        return data, 201

class Items(restful.Resource):
    def get(self):
        """Get items matching substringquery.
        """
        args = request.args
        labels = args.get('labels')
        pattern = args.get('pattern')
        labels = labels.split(',') if labels else None
        items = g.db.entities(
            query=pattern,
            labels=labels,
            entity='item')
        return [i.record for i in items]


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

def main():
    config.read()
    app.debug = True
    app.run()

if __name__ == '__main__':
    main()
