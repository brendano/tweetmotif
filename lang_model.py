import memcache
import marshal
import simplejson
from collections import defaultdict

class LocalLanguageModel:
  def __init__(self):
    self.counts = {'unigram': defaultdict(int), 'bigram':defaultdict(int)}
    self.info = {'big_n':0}
  def add(self, type, ngram):
    self.counts[type][ngram] += 1

class MemcacheLanguageModel:
  def __init__(self, info='background_model_info.json'):
    self.mc = memcache.Client(location, debug=0)
    self.info = simplejson.loads(open(info).read())

  def add(self, type, ngram):
    raise NotImplementedError

  def save_info(self, filename='background_model_info.json'):
    f = open(filename,'w')
    simplejson.dump(self.info, f)
    f.close()

class MemcacheDictInterface:
  def __init__(self,mc,type):
    self.type=type
    self.mc=mc
  def __getitem__(self, k):
    inner_key = (self.type, k)
    return self.mc.get(marshal.dumps(inner_key))



