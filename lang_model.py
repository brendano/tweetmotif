import marshal, urllib2, base64, binascii, struct, os, sys
import simplejson
from collections import defaultdict
import util
import fileinput

sys.path.insert(0, "platform/%s" % sys.platform)
# linux only
os.environ['LD_LIBRARY_PATH'] = "platform/%s:%s" % (sys.platform, os.environ.get('LD_LIBRARY_PATH'))

class LocalLM:
  def __init__(self):
    self.counts = {'unigram': defaultdict(int), 'bigram':defaultdict(int)}
    self.info = {'big_n':0}
  def add(self, type, ngram):
    self.counts[type][ngram] += 1
  def save_pickle(self, filename="background_model.pickle"):
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

def open_tc(filename,flag='c'):
  import pytc
  db = pytc.HDB()
  if flag=='c':
    bflag = pytc.HDBOCREAT|pytc.HDBOWRITER|pytc.HDBOREADER|pytc.HDBONOLCK
  elif flag=='r':
    bflag = pytc.HDBOREADER|pytc.HDBONOLCK
  else: raise Exception("need flag")
  db.open(filename, bflag)
  return db

class TokyoLM:
  def __init__(self, filename="background_model.tc", readonly=True):
    os.system("mkdir -p %s" % filename)
    flag = 'r' if readonly else 'c'
    self.counts = {
        'unigram': TokyoNgramProxy(open_tc("%s/unigram.hdb" % filename, flag)),
        'bigram':  TokyoNgramProxy(open_tc("%s/bigram.hdb"  % filename, flag)),}
    self.info = KVIntProxy(open_tc("%s/info.hdb" % filename, flag))

  def sync(self):
    for name,db in self.counts.iteritems(): db.sync()
    self.info.sync()
  def close(self):
    for name,db in self.counts.iteritems(): db.close()
    self.info.close()

  def add(self, type, ngram):
    #self.counts[type][ngram] += 1
    self.counts[type].addint("_".join(ngram),1)

class TokyoNgramProxy:
  # tokyo has a counting primitive, tc.addint() that works in 4-byte long ints.
  # if you want to read it, need a decoding layer
  def __init__(self, tc):
    self.d = tc
  def __getitem__(self,k):
    kj = '_'.join(k)
    if isinstance(kj, unicode): kj = kj.encode('utf-8')
    if kj not in self.d: return 0
    return struct.unpack('I', self.d[kj])[0]
  def __setitem__(self,k,v):
    raise NotImplementedError
  def __getattr__(self,name):
    return getattr(self.d,name)

class KVIntProxy:
  # for ascii decimal representation of integers
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
  # for ascii decimal representation of integers
  def __init__(self,d): self.d=d
  def __getitem__(self,k): 
    kj = '_'.join(k)
    if isinstance(kj, unicode): kj = kj.encode('utf-8')
    if kj not in self.d: return 0
    return int(self.d[kj])
  def __setitem__(self,k,v):
    self.d["_".join(k)] = str(v)
  def __getattr__(self,name): return getattr(self.d,name)

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


class TTLM:
  def __init__(self):
    import tokyotyrant
    self.tt = tokyotyrant.TT('localhost',11211)
    self.info={'big_n':0}
    #self.counts = {'unigram':self.tt, 'bigram':self.tt}
  def add(self,type,ngram):
    key = "_".join(ngram)
    self.tt.addint(key,1)
    #c = self.tt.get(key)
    #if c is None: self.tt.set(key,'0'

def occasional(iter, fn, every=1000):
  for i,item in enumerate(iter):
    yield item
    if (i+1) % every == 0:
      fn()

def make_tokyo_model(text_filename):
  import bigrams
  model = TokyoLM(readonly=False)
  #model = BDBLM()
  #model = LocalLM()
  iter = fileinput.input(text_filename)
  iter = occasional(iter, lambda: model.sync())
  bigrams.collect_statistics_into_model(iter, model)
  model.sync()
  return model

if __name__=='__main__':
  #model = make_memcache_model("data/the_en_tweets")
  #model.save_info()

  make_tokyo_model("data/the_a_en_tweets")

  #print "pickle"
  #for x in util.counter([1]): model.save_pickle()


###################################
