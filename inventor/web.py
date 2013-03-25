"""The inventory web client."""

import logging

from flask import Flask, request, g
from flask.ext import restful

from . import config
from . import db

log = logging.getLogger('inventor')

app = Flask(__name__)
api = restful.Api(app)

_db = None

def get_db():
    global _db
    if _db: return _db
    v = config['database']
    args = {}
    for key in v.keys():
        args[key] = v[key].get()
    log.debug(args)
    return db.Database(**args)

@app.before_request
def before_request():
    g.db = get_db()    

class Item(restful.Resource):
    def get(self, entity_id=None):
        log.debug('Getting item with id: %s', entity_id)
        try:
            e = g.db.get_entity(entity_id=entity_id, entity='item')
        except db.NoSuchEntityError as e:
            restful.abort(404, message='No item with id: '+str(entity_id))
        else:
            return e.record

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



api.add_resource(Item, '/item')
api.add_resource(Item, '/item/<int:entity_id>')
api.add_resource(Items, '/items')


def main():
    config.read()
    app.run()

if __name__ == '__main__':
    main()
        
