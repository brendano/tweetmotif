" wraps any fetchable resource with a tokyo tyrant cache "
import cPickle as pickle
from datetime import datetime,timedelta

import pytyrant

class TyrantCache:

  def __init__(self, host='localhost', port=1978, ttl=timedelta(seconds=5)):
    self.tt = pytyrant.PyTyrant.open(host, port)
    assert isinstance(ttl, timedelta)
    self.ttl = ttl

  def get(self, key, default=None):
    dkey = 'data_%s' % key
    return self.tt[dkey]

  def set(self, key, value):
    dkey = 'data_%s' % key
    lkey = 'last_update_%s' % key
    self.tt[dkey] = value
    self.tt[lkey] = pickle.dumps(datetime.now())

  def is_expired(self, key):
    # uhoh, racey?
    lkey = 'last_update_%s' % key
    if lkey not in self.tt: return True
    delt = datetime.now() - self.last_update(key)
    return delt > self.ttl
  
  def last_update(self, key):
    lkey = 'last_update_%s' % key
    return pickle.loads(self.tt[lkey])

  def wrap(cache, fetcher):
    # decorator
    def _getter(key):
      if cache.is_expired(key):
        _print("CACHE MISS %s" % key)
        val = fetcher(key)
        cache.set(key, val)
      else:
        _print("CACHE HIT %s" % key)
      return cache.get(key)
    return _getter
    

def _print(s): print s
