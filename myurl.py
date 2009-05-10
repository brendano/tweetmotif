# papers over the weird vagaries of urllib2 etc in python <=2.5 (2.6 is cleaner)

import urllib2, socket, timeout_urllib2; timeout_urllib2.sethttptimeout(5.0)
import urllib
from urllib2 import *
url_exceptions = (urllib2.URLError, timeout_urllib2.Error, socket.error)

def quote(s,*a,**k):
  try:
    return urllib.quote(s,*a,**k)
  except KeyError:
    # for some unicode. sigh.
    return s.replace(" ","%20")
