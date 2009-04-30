import struct,sys,os

sys.path.insert(0, "platform/%s" % sys.platform)
# linux only
os.environ['LD_LIBRARY_PATH'] = "platform/%s:%s" % (sys.platform, os.environ.get('LD_LIBRARY_PATH'))

def unpack_int(s):
  return struct.unpack('I',s)[0]
def pack_int(s):
  return struct.pack('I',s)

class IntKeyWrapper:
  def __init__(self, tc):
    self.tc = tc
  def __getitem__(self, k):
    return self.tc[pack_int(k)]
  def __setitem__(self, k, v):
    self.tc[pack_int(k)] = v
  def __contains__(self, k):
    return pack_int(k) in self.tc
  def __getattr__(self, name):
    return getattr(self.tc, name)



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

open = open_tc
