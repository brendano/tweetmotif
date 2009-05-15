import sys,os,urllib2,urllib
import myurl,util
import resource_cache
from datetime import timedelta

BACKEND_URL = "http://localhost:8080" if sys.platform=='darwin' else "http://localhost/backend"

the_cache = resource_cache.TyrantCache(port=2444, ttl=timedelta(seconds=60))

@the_cache.wrap
def url_call(url):
  json = urllib2.urlopen(url).read()
  return json

def make_url(q, max_topics):
  q = urllib.quote( util.stringify(q) )
  return BACKEND_URL + "/?q=%s&max_topics=%s&format=json" % ((q), util.stringify(max_topics))
  
def call(*args,**kwargs):
  url = make_url(*args, **kwargs)
  return url_call(url)

