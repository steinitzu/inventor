
class FixedDict(dict):
    """A dict where keys can not be added after creation (unless `extendable` is True).
    Keys are also marked as dirty when their values are changed.
    Accepts a list of `keys` and an optional `values` which should 
    be a dict compatible object.
    Any key not in `values` will be implicitly added and given a `None` value.
    """
    def __init__(self, keys=(), values=None, extendable=False):
        self.extendable = extendable
        values = values or {}
        self.dirty = {}
        super(FixedDict, self).__init__(values)
        seti = super(FixedDict, self).__setitem__
        for key in keys:
            if not key in self:
                seti(key, None)
        self.clear_dirty()

    def clear_dirty(self):
        self.dirty = {}
        for key in self.iterkeys():
            self.dirty[key] = False

    def is_dirty(self, key=None):
        """Checks if given `key` is dirty and returns bool respectively.
        When no key is provided, True is returned if any key is dirty.
        """
        if not key:
            return not not self.dirty
        return key in self.dirty and self.dirty[key]

    def __setitem__(self, key, value):
        if key not in self and not self.extendable:
            raise KeyError('{} is not a valid key.'.format(key))
        elif key in self and self[key] == value:
            return
        else:
            super(FixedDict, self).__setitem__(key, value)
            self.dirty[key] = True


def isiterable(val):
    """Return True if value is iterable but not a string.
    """
    if hasattr(val, '__iter__') and not isinstance(val, basestring):
        return True
    else: 
        return False
