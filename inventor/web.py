"""The inventory web client."""

import logging
import os

from flask import Flask, request, g
from flask.ext import restful
from flask import render_template
from flask import make_response

from . import config
from . import db

log = logging.getLogger('inventor')

app = Flask(__name__, template_folder='static')
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

@api.representation('text/html')
def output_html(data, code, headers=None):
    resp = make_response(data, code)
    resp.headers.extend(headers or {})
    return resp

class Item(restful.Resource):
    def get(self, entity_id=None):
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
        return render_template('index.html')

api.add_resource(Item, '/item')
api.add_resource(Item, '/item/<int:entity_id>')
api.add_resource(Items, '/items')
api.add_resource(Index, '/')


def main():
    config.read()
    app.run()

if __name__ == '__main__':
    main()
        
