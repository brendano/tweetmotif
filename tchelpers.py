import struct,sys,os

sys.path.insert(0, os.path.join(os.path.dirname(__file__),"platform/%s" % sys.platform))
# linux only, mac is DYLD_
os.environ['LD_LIBRARY_PATH'] = "platform/%s:%s" % (sys.platform, os.environ.get('LD_LIBRARY_PATH'))

import pytc

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



def open_tc(filename,flag='c'):
  db = pytc.HDB()
  if flag=='c':
    bflag = pytc.HDBOCREAT|pytc.HDBOWRITER|pytc.HDBOREADER|pytc.HDBONOLCK
  elif flag=='r':
    bflag = pytc.HDBOREADER|pytc.HDBONOLCK
  else: raise Exception("need flag")
  db.open(filename, bflag)
  return db

open = open_tc
