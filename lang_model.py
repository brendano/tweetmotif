#from memcache import Client
from cmemcached import Client
#from cmemcache import Client
import marshal, urllib2, base64, os, sys
import simplejson
from collections import defaultdict
import util

sys.path.insert(0, "platform/%s" % sys.platform)

class LocalLM:
  def __init__(self):
    self.counts = {'unigram': defaultdict(int), 'bigram':defaultdict(int)}
    self.info = {'big_n':0}
  def add(self, type, ngram):
    self.counts[type][ngram] += 1
  def save_pickle(self, filename="lang_model.pickle"):
    import cPickle as pickle
    self.save_whole_thing(filename,pickle.dump)

  def save_whole_thing(self, filename, dump_fn):
    f = open(filename,'w')
    dump_fn(self,f)
    f.close()

  @staticmethod
  def load_pickle(filename="background_model.pickle"):
    import cPickle as pickle
    return pickle.load(open(filename))


class BDBShelveLM:
  " retrieval doesnt work "
  def __init__(self, filename="background_model.all_counts.s", readonly=False):
    import util,shelve
    self.counts = {}
    if not readonly:
      self.all_counts = util.DefaultMapping(shelve.open(filename,'c'), int)
    else:
      self.all_counts = shelve.open(filename, 'r')
    self.counts = {
      'unigram': self.all_counts,
      'bigram':  self.all_counts, }
    self.info = {'big_n':0}
  def add(self, type, ngram):
    #k = mc_keymaker((type,ngram))
    k = "_".join(ngram)
    self.counts[type][k] += 1

def open_tc(filename,flag='c'):
  import pytc
  db = pytc.BDB()
  if flag=='c':
    bflag = pytc.BDBOCREAT|pytc.BDBOWRITER|pytc.BDBOREADER
  elif flag=='r':
    bflag = pytc.BDBOREADER
  else: raise Exception("need flag")
  db.open(filename, bflag)
  return db

class TokyoLM:
  def __init__(self, filename="background_model.tc", readonly=True):
    os.system("mkdir -p %s" % filename)
    flag = 'r' if readonly else 'c'
    self.counts = {
        'unigram': KVNgramProxy(open_tc("%s/unigram.db" % filename, flag)),
        'bigram':  KVNgramProxy(open_tc("%s/bigram.db"  % filename, flag)),}
    self.info = KVIntProxy(open_tc("%s/info.db" % filename, flag))

  def sync(self):
    for name,db in self.counts.iteritems(): db.sync()
    self.info.sync()
  def close(self):
    for name,db in self.counts.iteritems(): db.close()
    self.info.close()

  def add(self, type, ngram):
    self.counts[type][ngram] += 1
    #counts = self.counts[type]
    #key = "_".join(ngram)
    #if key not in counts:
    #  counts[key] = '0'
    #counts[key] = str(1 + int(counts[key]))

class KVIntProxy:
  def __init__(self, wrapped_dict):
    self.d = wrapped_dict
  def __getitem__(self,k):
    k=str(k)
    if k not in self.d: self.d[k] = '0'
    return int(self.d[k])
  def __setitem__(self,k,v):
    self.d[k] = str(v)
  def __getattr__(self,name): return getattr(self.d,name)

class KVNgramProxy:
  def __init__(self,d): self.d=d
  def __getitem__(self,k): 
    kj = ('_'.join(k))
    if isinstance(kj, unicode):
      kj = kj.encode('utf-8')
    if kj not in self.d: return 0   #self.d[kj] = '0'
    return int(self.d[kj])
  def __setitem__(self,k,v):
    self.d["_".join(k)] = str(v)


#class KVPrefixProxy:
#  def __init__(self, wrapped_dict, prefix=None):
#    if prefix is None:
#      self.prefix = ""
#    else:
#      self.prefix = "**%s:" % prefix
#    self.wrapped_dict = wrapped_dict
#  def __getitem__(self,k):
#    return self.wrapped_dict[self.prefix+k]
#  def __setitem__(self,k,v):
#    self.wrapped_dict[self.prefix+k] = v

#import binascii
#mc_keymaker = lambda x: binascii.b2a_base64(repr(x))[:-1]
#mc_keymaker = lambda x: binascii.b2a_base64(marshal.dumps(x))[:-1]
#mc_keymaker = lambda x: urllib2.quote(marshal.dumps(x))
#mc_keymaker = lambda x: base64.b64encode(marshal.dumps(x))
#mc_keymaker = lambda x: base64.b64encode(repr(x))
#memcache_keymaker = marshal.dumps


class MemcacheLM:
  def __init__(self, dont_load_info=False):
    location = ['127.0.0.1:11211']
    #location = ['127.0.0.1:21201']
    #location = ['127.0.0.1:13000']
    self.mc = Client(location)
    if dont_load_info:
      self.info = {'big_n':0}
    else:
      self.load_info()
    self.counts = {
        'unigram': MemcacheDictInterface(self.mc,'unigram'),
        'bigram': MemcacheDictInterface(self.mc,'bigram'), }
    
  def add(self, type, ngram):
    # ignore type.
    key = "_".join(ngram)
    #key = (type,ngram)
    #key = mc_keymaker((type,ngram))
    c = self.mc.get(key)
    if c is None: self.mc.set(key,0)
    self.mc.incr(key)

  def load_info(self, filename='background_model.info.json'):
    self.info = simplejson.loads(open(filename).read())

  def save_info(self, filename='background_model.info.json'):
    f = open(filename,'w')
    simplejson.dump(self.info, f)
    f.close()

class MemcacheDictInterface:
  def __init__(self,mc,type):
    self.type = type
    self.mc = mc
  def __getitem__(self, ngram):
    key = "_".join(ngram)
    val = self.mc.get(key)
    return val or 0



def make_memcache_model(text_filename):
  print "loading %s into memcached" % text_filename
  import bigrams
  model = MemcacheLM(dont_load_info=True)
  bigrams.collect_statistics_into_model(text_filename, model)
  return model

def make_tokyo_model(text_filename):
  import bigrams
  model = TokyoLM(readonly=False)
  bigrams.collect_statistics_into_model(text_filename, model)
  #model.sync()
  return model

  #model = LocalLM()
  #model = BDBLM()

if __name__=='__main__':
  #model = make_memcache_model("data/the_en_tweets")
  #model.save_info()

  make_tokyo_model("data/the_en_tweets")
  #print "pickle"
  #for x in util.counter([1]): model.save_pickle()

  #model = make_exper_model("data/the_en_tweets")
  ##model = make_exper_model("data/tiny")

  print "done."


###################################
class BDBLM:
## BROKEN
  def __init__(self, filename="background_model.counts.bdb"):
    import bsddb3
    self.all_counts = bsddb3.btopen(filename, 'c')
    #self.all_counts.open(filename, pytc.BDBOCREAT|pytc.BDBOWRITER|pytc.BDBOREADER)
    self.info = {'big_n':0}
    self.counts = {'unigram':self.all_counts, 'bigram':self.all_counts}
  def add(self, type, ngram):
    key = "_".join(ngram)
    if key not in self.all_counts:
      self.all_counts[key] = '0'
    self.all_counts[key] = str(1 + int(self.all_counts[key]))

