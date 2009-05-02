import wsgiref
import urllib2
import os,sys
import timeout_urllib2; timeout_urllib2.sethttptimeout(4.0)
from sane_re import *

import tchelpers

os.system("mkdir -p httpcache.tc")
data_by_url = tchelpers.open("httpcache.tc/data_by_url.tch")
last_updaate = tchelpers.open("httpcache.tc/last_update.tch")


def application(environ, start_response):
  response_headers = [('Content-type', 'text/plain')]
  #start_response(status, response_headers)

  url = wsgiref.util.request_uri(environ)
  print url
  url = _S(url)['/(http.*)', 1]
  url = url.replace('http%3A//','http://')
  print url
  if url in data_by_url:
    print "CACHE HIT"
    data = data_by_url[url]
  else:
    try:
      print "URL FETCH"
      f = urllib2.urlopen(url)
      data = f.read()
      data_by_url[url] = data
    except (urllib2.URLError, timeout_urllib2.Error, socket.error), e:
      print type(e),e
      if hasattr(e,'headers'):
        status = e.headers.status
      else:
        status = '500 Internal Server Error'
      start_response(status, response_headers)
      yield ['{"results":[], "error":true}']
      return

  start_response("200 OK", response_headers)
  yield data
  return

  yield "<hr>"

  yield "<table>"
  for k in sorted(environ.keys()):
    yield "<tr><td>" + k
    yield "<td>" + str(environ[k])
    #yield "<br>"
  yield "</table>"

if __name__=='__main__':
  import util; util.fix_stdio()
  from wsgiref.simple_server import make_server, demo_app
  httpd = make_server('', 8500, application)
  httpd.serve_forever()
