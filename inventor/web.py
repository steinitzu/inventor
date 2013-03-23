from flask import Flask
from flask.ext import restful

from . import db



database = db.Database(user='steini')
app = Flask(__name__)
api = restful.Api(app)

class Item(restful.Resource):
    def get(self, entity_id=None):
        e = database.get_entity(entity_id=entity_id, entity='item')
        return e.record

api.add_resource(Item, '/item')
api.add_resource(Item, '/item/<int:entity_id>')

def main():
    app.run(debug=True)

if __name__ == '__main__':
    main()
        
