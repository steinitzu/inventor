from flask import Flask, url_for

from . import db

app = None
database = None

def initialize():
    """Start the application.
    """
    global app
    app = Flask(__name__)
    global database
    database db.Database()

@app.route('/search/<query>')
def search(query):
    items = db.items(query=query)
    return template(items) #pseudocode
