import struct,sys,os

#plat = 'darwin' if sys.platform=='darwin' else os.popen("uname -m").read().lower().strip()
#sys.path.insert(0, os.path.join(os.path.dirname(__file__),"platform/%s" % plat))

#import pytc
import tc as pytc  ## http://github.com/rsms/tc

def unpack_int(s):
  return struct.unpack('I',s)[0]
def pack_int(s):
  return struct.pack('I',s)

class IntKeyWrapper:
  # TC doesn't like binary representation of certain integers as keys??
  def __init__(self, tc):
    self.tc = tc
  def __getitem__(self, k):
    return self.tc[repr(k)]
  def __setitem__(self, k, v):
    try:
      self.tc[repr(k)] = v
    except pytc.Error, e: 
      print repr(k), repr(v)
      raise e #print e
  def __contains__(self, k):
    return repr(k) in self.tc
  def __getattr__(self, name):
    return getattr(self.tc, name)


# confused over what tc really wants
#import threading
#tc_threadlocal = threading.local()
import util
tc_threadlocal = util.Struct()
tc_threadlocal.dbs = {}
def has_db(filename):
  global tc_threadlocal
  if not hasattr(tc_threadlocal,'dbs'):
    tc_threadlocal.dbs = {}
  return filename in tc_threadlocal.dbs
def get_db(filename):
  global tc_threadlocal
  assert has_db(filename)
  return tc_threadlocal.dbs[filename]
def set_db(filename,db):
  tc_threadlocal.dbs[filename] = db

def open_tc(filename,flag='c'):
  if has_db(filename):
    return get_db(filename)
  db = pytc.HDB()
  if flag=='c':
    bflag = pytc.HDBOCREAT|pytc.HDBOWRITER|pytc.HDBOREADER|pytc.HDBONOLCK
  elif flag=='r':
    bflag = pytc.HDBOREADER|pytc.HDBONOLCK
  else: raise Exception("need flag")
  db.open(filename, bflag)
  set_db(filename,db)
  return db

open = open_tc
