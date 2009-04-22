#mc_keymaker = lambda x: binascii.b2a_base64(repr(x))[:-1]
#mc_keymaker = lambda x: binascii.b2a_base64(marshal.dumps(x))[:-1]
#mc_keymaker = lambda x: urllib2.quote(marshal.dumps(x))
#mc_keymaker = lambda x: base64.b64encode(marshal.dumps(x))
#mc_keymaker = lambda x: base64.b64encode(repr(x))
#memcache_keymaker = marshal.dumps


class MemcacheLM:
  def __init__(self, dont_load_info=False):
    #from memcache import Client
    from cmemcached import Client
    #from cmemcache import Client
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
    key = binascii.b2a_base64(key)[:-1]
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

class RedisLM:
  def __init__(self, dont_load_info=False):
    #location = ['127.0.0.1:11211']
    #location = ['127.0.0.1:21201']
    #location = ['127.0.0.1:13000']
    sys.path.insert(0,"/users/brendano/sw/redis-0.091/client-libraries/python/")
    import redis
    self.mc = redis.Redis('localhost',6379)
    self.info = {'big_n':0}
    
  def add(self, type, ngram):
    # ignore type.
    key = "_".join(ngram)
    key = binascii.b2a_base64(key)[:-1]
    #key = (type,ngram)
    #key = mc_keymaker((type,ngram))
    c = self.mc.get(key)
    if c is None: self.mc.set(key,0)
    self.mc.incr(key)

class MemcacheDictInterface:
  def __init__(self,mc,type):
    self.type = type
    self.mc = mc
  def __getitem__(self, ngram):
    key = "_".join(ngram)
    val = self.mc.get(key)
    return val or 0


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

class BDBLM:
## BROKEN
  def __init__(self, filename="background_model.counts.bdb"):
    import bsddb3
    self.all_counts = bsddb3.hashopen(filename, 'c')
    #self.all_counts.open(filename, pytc.BDBOCREAT|pytc.BDBOWRITER|pytc.BDBOREADER)
    self.info = {'big_n':0}
    self.counts = {'unigram':self.all_counts, 'bigram':self.all_counts}
  def add(self, type, ngram):
    key = "_".join(ngram)
    if key not in self.all_counts:
      self.all_counts[key] = '0'
    self.all_counts[key] = str(1 + int(self.all_counts[key]))
  def sync(self):
    pass
    #for name,db in self.counts.iteritems(): db.sync()
    #self.info.sync()


def make_weird_model(text_filename):
  print "loading %s into memcached" % text_filename
  import bigrams
  #model = MemcacheLM(dont_load_info=True)
  #model = TTLM()
  model = RedisLM()
  bigrams.collect_statistics_into_model(fileinput.input(text_filename), model)
  return model

