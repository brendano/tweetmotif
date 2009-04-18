import memcache
import marshal, urllib2, base64
import simplejson
from collections import defaultdict
import util

class LocalLM:
  def __init__(self):
    self.counts = {'unigram': defaultdict(int), 'bigram':defaultdict(int)}
    self.info = {'big_n':0}
  def add(self, type, ngram):
    self.counts[type][ngram] += 1


import binascii
mc_keymaker = lambda x: binascii.b2a_base64(repr(x))[:-1]
#mc_keymaker = lambda x: binascii.b2a_base64(marshal.dumps(x))[:-1]
#mc_keymaker = lambda x: urllib2.quote(marshal.dumps(x))
#mc_keymaker = lambda x: base64.b64encode(marshal.dumps(x))
#mc_keymaker = lambda x: base64.b64encode(repr(x))
#memcache_keymaker = marshal.dumps

class MemcacheLM:
  def __init__(self, dont_load_info=False):
    location = ['127.0.0.1:11211']
    self.mc = memcache.Client(location)
    if dont_load_info:
      self.info = {'big_n':0}
    else:
      self.load_info()
    self.counts = {
        'unigram': MemcacheDictInterface(self.mc,'unigram'),
        'bigram': MemcacheDictInterface(self.mc,'bigram'), }
    
  def add(self, type, ngram):
    key = (type,ngram)
    key = mc_keymaker((type,ngram))
    c = self.mc.get(key)
    if c is None: self.mc.set(key,0)
    self.mc.incr(key)

  def load_info(self, filename='background_model_info.json'):
    self.info = simplejson.loads(open(filename).read())

  def save_info(self, filename='background_model_info.json'):
    f = open(filename,'w')
    simplejson.dump(self.info, f)
    f.close()

class MemcacheDictInterface:
  def __init__(self,mc,type):
    self.type = type
    self.mc = mc
  def __getitem__(self, k):
    key = mc_keymaker((self.type, k))
    val = self.mc.get(key)
    return val or 0



def make_memcache_model(text_filename):
  import bigrams
  model = MemcacheLM(dont_load_info=True)
  bigrams.collect_statistics_into_model(text_filename, model)
  return model

if __name__=='__main__':
  print "loading background model into memcached"
  model = make_memcache_model("data/the_en_tweets")
  #model = make_memcache_model("data/tiny")
  model.save_info()
  print "done."
