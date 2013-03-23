import logging

from flask import Flask
from flask.ext import restful

from . import db

log = logging.getLogger('inventor')



database = db.Database(user='steini')
app = Flask(__name__)
api = restful.Api(app)

class Item(restful.Resource):
    def get(self, entity_id=None):
        log.debug('Getting item with id: %s', entity_id)
        e = database.get_entity(entity_id=entity_id, entity='item')
        return e.record

class Items(restful.Resource):
    def get(self, pattern=None):
        """Get items matching substringquery.
        """
        if not pattern:
            items = database.entities(entity='item')
        else:
            query = db.AnySubStringQuery(pattern, entity='item')
            items = database.entities(query=query, entity='item')
        return [i.record for i in items]

api.add_resource(Item, '/item')
api.add_resource(Item, '/item/<int:entity_id>')
api.add_resource(Items, '/items')
api.add_resource(Items, '/items/<string:patterno>')

def main():
    app.run(debug=True)

if __name__ == '__main__':
    main()
        
