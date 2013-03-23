from datetime import datetime, date
from decimal import Decimal
import json


#monkey patch the json encoder


def newdefault(self, obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat() #this is redundant
    elif isinstance(obj, Decimal):
        return str(obj)
    # elif obj is None:
    #     #None converted to empty string cause otherwise js
    #     #will convert the None to null which results in a string
    #     #with the value "null" being returned back making a mess of things
    #     return ''
    raise TypeError(
        'Object of type %s with value %s is not JSON serializable' %
        (type(obj), obj))


setattr(json.JSONEncoder, 'default', newdefault)
