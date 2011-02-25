# papers over the weird vagaries of urllib2 etc in python <=2.5 (2.6 is cleaner)

import urllib2, socket, timeout_urllib2; timeout_urllib2.sethttptimeout(5.0)
import urllib
from urllib2 import *
url_exceptions = (urllib2.URLError, timeout_urllib2.Error, socket.error)

import util

def urlencode(dct):
  dct = dict( (k, util.stringify(v)) for k,v in dct.iteritems())
  return urllib.urlencode(dct)
  