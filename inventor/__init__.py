from datetime import datetime, date
from decimal import Decimal
import json
import logging

from . import confit

config = confit.Configuration('inventor', __name__, False)

log = logging.getLogger('inventor')
formatter = logging.Formatter('%(levelname)s:%(module)s.%(funcName)s: %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
log.addHandler(handler)

log.setLevel(logging.DEBUG)

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
