from __future__ import division
import marshal, urllib2, base64, binascii, struct, os, sys
from collections import defaultdict
import fileinput
import simplejson
import util
import tchelpers

sys.path.insert(0, "platform/%s" % sys.platform)
# linux only
os.environ['LD_LIBRARY_PATH'] = "platform/%s:%s" % (sys.platform, os.environ.get('LD_LIBRARY_PATH'))

class LMCommon:
  def compare_with_bg_model(self, bg_model, n, min_count=1,
                            smoothing_algorithm='mle'):
    ngrams_with_ratios = [
      (self.likelihood_ratio(ngram, bg_model, smoothing_algorithm), ngram)
      for ngram in self.ngrams_by_type[n]
    ]
    ngrams_with_ratios.sort(reverse=True)
    for ratio, ngram in ngrams_with_ratios:
      if self.counts[ngram] < min_count:
        continue
      yield ratio, ngram

  def likelihood_ratio(self, ngram, bg_model, smoothing_algorithm='mle'):
    # This is where experimentation can happen:
    # * change probability estimate
    # * change ratio computation

    fn = getattr(bg_model, smoothing_algorithm)
    bg_prob_estimate = fn(ngram)
    if bg_prob_estimate == 0:
      return 0
    else:
      fn = getattr(self, smoothing_algorithm)
      self_prob_estimate = fn(ngram)
      return self_prob_estimate/bg_prob_estimate

  def mle(self, ngram):
    big_n = self.info["big_n"]
    count = self.counts[ngram]
    return count/big_n

  def laplace(self, ngram):
    n = len(ngram)
    big_n = self.info["big_n"] + self.ngram_type_count(n)
    count = self.counts[ngram] + 1
    return count/big_n

  def lidstone(self, ngram, delta=0.5):
    n = len(ngram)
    big_n = self.info["big_n"] + (delta * self.ngram_type_count(n))
    count = self.counts[ngram] + delta
    return count/big_n

  def pseudocounted_ratio(self, num,denom, a=0.1):
    return (num+a) / (denom+a)

class LocalLM(LMCommon):
  def __init__(self):
    self.counts = defaultdict(int)
    self.info = {'big_n':0}
    self.ngrams_by_type = [None, set(), set(), set()]

  def add(self, ngram):
    if not self.counts.has_key(ngram):
      self.ngrams_by_type[len(ngram)].add(ngram)
    self.counts[ngram] += 1

  def ngram_type_count(self, n):
    return len(self.ngrams_by_type[n])

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

class TokyoLM(LMCommon):
  def __init__(self, filename="background_model.tc", readonly=True):
    os.system("mkdir -p %s" % filename)
    flag = 'r' if readonly else 'c'
    self.counts = TokyoNgramProxy(tchelpers.open("%s/ngram_counts.hdb" % filename, flag))
    self.info = KVIntProxy(tchelpers.open_tc("%s/info.hdb" % filename, flag))

  def sync(self):
    self.counts.sync()
    self.info.sync()
  def close(self):
    self.counts.close()
    self.info.close()

  def add(self, ngram):
    ngram_as_string = "_".join(ngram)
    if not self.counts.has_key(ngram_as_string):
      self.info[{ 1:'unigram_type_count', 2:'bigram_type_count',
                  3:'trigram_type_count'}[len(ngram)]] += 1
    self.counts.addint(ngram_as_string,1)

  def ngram_type_count(self, n):
    return self.info[{ 1:'unigram_type_count', 2:'bigram_type_count',
                       3:'trigram_type_count'}[n]]

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
  #iter = occasional(iter, lambda: model.sync())
  bigrams.collect_statistics_into_model(iter, model)
  model.sync()
  return model

if __name__=='__main__':
  #model = make_memcache_model("data/the_en_tweets")
  #model.save_info()

  make_tokyo_model("data/all_background")

  #print "pickle"
  #for x in util.counter([1]): model.save_pickle()


###################################

  #coll_ngrams_and_mle_prob_ratio = map(lambda (b,p): (b, pseudocounted_ratio(p, bkgnd_ngram_counts[b]/bkgnd_N)), coll_ngrams_and_counts)  # pseudocount smoothing is crappy because causes ties.  how about good-turing or kneser-ney?



  #ngrams = [ngram for ngram,count in coll_ngrams_and_counts]
  #counts = [count for ngram,count in coll_ngrams_and_counts]
  #mle_probs = [c/coll_N for c in counts]
  #mle_prob_ratio = [compute_ratio(mle_probs[i], bkgnd_ngram_counts[ngrams[i]]) for i in range(len(ngrams))]
  #inds = range(len(ngrams))
  #inds.sort(key=lambda i: mle_prob_ratio[i], reverse=True)
  #for i in inds:
  #  if counts[i] < min_count: continue
  #  yield mle_prob_ratio[i], ngrams[i]

