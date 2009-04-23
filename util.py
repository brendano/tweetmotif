"some python utilties - anyall.org/util.py"

from __future__ import division
import sys, time, math, itertools, csv, codecs, re, operator
#import numpy
from StringIO import StringIO

__author__ = "brendan o'connor (anyall.org)"
__version__ = "Apr 09 or so"

#########  Make UTF-8 hurt less

# My rant about pre-py3k encoding handling
# They like to say, always use unicode internally, then decode/encode at I/O boundaries
# That's good once you've accomplished it, but it's impractical without the following shims
# Since Python has inconsistent policies for what encoding an arbitrary stream will be.

def fix_stdio():
  """ forces utf8 at I/O boundaries, since it's ascii by default when using
  pipes .. ugh ..  Never call this multple times in the same process; horrible
  things sometimes seem to happen."""
  sys.stdout = codecs.open('/dev/stdout','w',encoding='utf8',buffering=0)
  sys.stdout = ShutUpAboutBrokenPipe(sys.stdout)
  sys.stdin  = codecs.open('/dev/stdin','r',encoding='utf8')
  sys.stderr = codecs.open('/dev/stderr','w',encoding='utf8',buffering=0)

def unicodify(s, encoding='utf8'):
  """ because {str,unicode}.{encode,decode} is anti-polymorphic, but sometimes
  you can't control which you have. """
  if isinstance(s,unicode): return s
  return s.decode(encoding)

def stringify(s, encoding='utf8'):
  if isinstance(s,str): return s
  return s.encode(encoding)

class ShutUpAboutBrokenPipe:
  """i like to press ctrl-c; why is python yelling at me?"""
  def __init__(self, fp):
    self.fp = fp
  def write(self,*a,**k):
    try:
      self.fp.write(*a,**k)
    except IOError, e:
      if e.errno == 32:  # broken pipe
        sys.exit(0)
      raise e


##########  CSV and TSV

def read_csv(filename, **k):
  f = open(filename)
  r = list(csv.DictReader(f, **k))
  f.close()
  return r

def write_csv(data, filename, cols=None):
  """ data is a list of dicts. python's DictWriter is too timid to automatically determine an ordering, so we'll do it.
This function is supposed to work like R's write.table()"""
  if not cols:
    cols = sorted(data[0].keys())
  import csv
  f = open(filename,"w")
  w = csv.DictWriter(f, cols)
  w.writerow( dict((c,c) for c in cols) )
  for row in data:
    w.writerow( row )
  f.close()

def tsv_reader(f):
  "honest-to-goodness tsv with no quoting nor embedded tabs nor newlines"
  return csv.DictReader(f, dialect=None, delimiter='\t', quoting=csv.QUOTE_NONE)

def read_tsv(filename, **k):
  "honest-to-goodness tsv with no quoting nor embedded tabs nor newlines"
  f = open(filename)
  r = list(tsv_reader(f, **k))
  f.close()
  return r

def write_tsv(data, filename):
  raise NotImplementedError("not sure whether to make this autoguess columns or not or what")


##########  Misc

def fancy_sub(s, pat, repl_fn=lambda m: ">> %s <<" % m.group()):
  """ like ruby String.gsub() when passing in a block """
  ret = StringIO()
  last = 0
  for m in re.finditer(pat,s):
    ret.write(s[last:m.start()])
    ret.write(repl_fn(m))
    last = m.end()
  if last < len(s):
    ret.write(s[last:])
  return ret.getvalue()

def fullgroupby(seq, key):
  """groups items by key; seq's ordering doesn't matter.  unlike itertools.groupby and unlike unix uniq, but like sql group by."""
  dec = [ (key(x),x) for x in seq ]
  dec.sort()
  return ( (g, [x for k,x in vals])  for g,vals  in  
      itertools.groupby(dec, lambda (k,x): k))

def dgroupby(seq,key):
  return dict(fullgroupby(seq,key))

def na_rm(seq):
  return [x for x in seq if x is not None]

class Struct(dict):
  def __getattr__(self, a):
    return self[a]
  def __setattr__(self, a, v):
    self[a] = v

class DefaultMapping:
  """like collections.defaultdict but proxies over an arbitrary mapping (e.g. shelve instance)"""
  def __init__(self, d, default_factory):
    self.d = d
    self.default_factory = default_factory
  def __getitem__(self,k):
    if k not in self.d:
      self.d[k] = self.default_factory()
    return self.d[k]
  def __getattr__(self,a):
    return getattr(self.d,a)
    
def product(seq, default=1):
  if len(seq)==0: return default
  return reduce(operator.mul, seq)
  

class DataFrame(list):
  " simplest implementation: list of hashes plus syntactic sugar "

  def __getitem__(self, i):
    if type(i) == str:
      return numpy.array([x[i] for x in self])
    else:
      return list.__getitem__(self, i)
      
  def __getattr__(self, attr):
    return self[attr]

  @property
  def cols(self):
    return sorted(self[0].keys())
    
  def p(self):
    """print as table to console"""
    cols = self.cols
    print "\t".join(cols)
    for r in self:
      print "\t".join(str(r[c]) for c in cols)
      
  def html(self, browser=True):
    """print as html table, open in browser"""
    pass


######### jacked from anyall.org/counter.py


class Counter:
  """ 
  Count iterations and measure speed with ETA's.  Similar to "pv".

  Usage:

      from counter import counter

      # wrap any iterator
      for x in counter(range(20)):
        time.sleep(.1)

      for x in counter(x for x in range(20)):
        time.sleep(.1)

      # generator doesn't know its length; but you can fill in
      for x in counter((x for x in range(20)), max=20)):
        time.sleep(.1)

      # name it
      for x in counter(range(20), name="trial"):
        time.sleep(.1)

      # manual, non-wrapper usage.  API is: start, next, end
      counter.start()
      for x in range(0,50):
        time.sleep(.1)
        counter.next()
      counter.end()

      # if you know the max, can not bother with end
      counter.start(max=50)
      for x in range(0,50):
        time.sleep(.1)
        counter.next()
  """

  def __init__(self):
    self.out = sys.stderr
    self.need_restart = True
  
  def start(self, bla=None, name="iter", max=None):
    if type(bla)==str: name=bla
    if type(bla)==int: max=bla
    self.count = 0
    self.name = name
    self.max = max
    self.last_size = None
    self.start_time = self.when_last_line = time.time()
    self.need_restart = False
    self.show_line("Starting ")
  
  def next(self):
    if self.need_restart:  self.start()
    
    self.count += 1
    since_last = time.time() - self.when_last_line
    if since_last < 0.05:  return
    self.show_progress_line("%s %d" % (self.name, self.count))
    if self.max and self.count >= self.max: self.end()
  
  def end(self):
    if self.need_restart: return  # idempotent..
    elapsed = time.time() - self.start_time
    self.show_line("Done at %s %d, %s total  %s" % (
        self.name,
        self.count, smart_time_fmt(elapsed), self.rate_str(self.count/elapsed),))
    self.out.write("\n")
    self.out.flush()
    self.need_restart = True
  
  def __call__(self, iterator, *args, **kwds):
    if 'max' not in kwds and hasattr(iterator, '__len__'):
      kwds['max'] = len(iterator)
    self.start(*args, **kwds)
    for x in iterator:
      self.next()
      yield x
    self.end()
    
    
  # privates below
  
  def rate_str(self, rate):
    if rate <= 0:  return "(rate N/A)"
    rate_strs = []
    rate_strs.append("%s %s/sec" % (smart_fmt(rate), self.name))
    if rate < 1: rate_strs.append("%s %s/min" % (smart_fmt(rate*60), self.name))
    if rate < 1/60: rate_strs.append("%s %s/hr" % (smart_fmt(rate*60*60), self.name))
    return "(%s)" %  (", ".join(rate_strs))
    
  def show_progress_line(self, s):
    if self.max:
      s += " of %d" % self.max
    
    rate = self.count / (time.time() - self.start_time)
    s += " " + self.rate_str(rate)
    
    if self.max and rate > 0:
      projection = (self.max - self.count) / rate
      s += "  %s remaining" % smart_time_fmt(projection)
    s += " "
    self.show_line(s.capitalize())

  def show_line(self, s):
    if self.last_size:
      self.out.write("\b" * self.last_size)
      self.out.flush()
    self.out.write(s)
    self.out.flush()
    
    self.last_size = len(s)
    self.when_last_line = time.time()

counter = Counter()
  

def smart_fmt(x, space=False):
  # too complex probably
  def fmt1():
    d = int((math.log10(abs(x))))
    if x >= 1:
      shelf = 3 * (d//3)
    else:
      shelf = 3 * (d//3)
    if shelf>9: shelf=9
    if shelf<-6: shelf=-6
    num_dec = max(0,  2 - abs( abs(d)-abs(shelf)))
    if x<1:  num_dec+=1
    fmt = "%." +str(num_dec)+ "f"
    post_sym = {-6:"micro", -3:"milli", 0:"", 3:"k", 6:"M", 9:"G"}
    return (fmt % (x / 10**shelf), post_sym[shelf])
  
  s,sym = fmt1()
  if sym != "": s += " "+sym
  if space and not s.endswith(" "): s += " "
  return s
  
    # if x < 1e-6: return "%.1f micro" % (x*1e6)
    # if x < 1e-3: return "%.1f milli" % (x*1e3)
    # if x < 1:    return "%.3f" % x
    # if x < 10:   return "%.2f" % x
    # if x < 100:  return "%.1f" % x
    # if x < 1000: return "%d" % x
    # if x < 10*1000:  return "%.2f k" % (x/1e3)
    # if x < 1e10: return "%.1f M" % (x/1e6)
    # if x < 1e13: return "%.1f G" % (x/1e9)
    # else: return "%s" % x
  # s = fmt1()

def smart_time_fmt(secs):
  if secs < 60:
    return "%ds" % secs
  if secs < 60*60:
    return "%dm:%.2ds" % ((secs//60) % 60, secs % 60)
  else:
    return "%d:%.2d:%.2d" % (secs//(60*60), (secs//60) % 60, secs % 60)
  
## counter test
if 0:  #__name__=='__main__':
  import time,random
  print "Slow count, manual API"
  counter.start(10)
  for x in range(0,10):
    time.sleep(0 + random.random() * 2)
    #time.sleep(0.4)
    counter.next()
  counter.end()
  print "Fast count, iterator wrapper API"
  for x in counter(range(100)):
    time.sleep(0.1)

