import sys,os,urllib2
import myurl
import resource_cache
from datetime import timedelta

BACKEND_URL = "http://localhost:8080" if sys.platform=='darwin' else "http://tweetmotif.com/backend"

the_cache = resource_cache.TyrantCache(port=2444, ttl=timedelta(seconds=60))

#@the_cache.wrap
def url_call(url):
  json = urllib2.urlopen(url).read()
  return json

def call(q, max_topics):
  url = BACKEND_URL + "/?q=%s&max_topics=%s&format=json" % (q, max_topics)
  return url_call(url)
  
    

# def refresh_query(q):
