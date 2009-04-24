import simplejson
import urllib2,urllib,sys,pprint,cgi,time
from datetime import datetime,timedelta

import socket
socket.setdefaulttimeout(2) # http://www.voidspace.org.uk/python/articles/urllib2.shtml

def fetch(url):
  for i in range(2):
    try: return urllib2.urlopen(url)
    except (urllib2.HTTPError,urllib2.URLError), e:
      print e
      pass
  return urllib2.urlopen(url)

SEARCH_URL = "http://search.twitter.com/search.json?lang=en"
#SEARCH_URL = "http://anyall.org/nph-kazamo/" + SEARCH_URL

def yield_results(q, pages=10, rpp=100, hash_fn=None):
  url = SEARCH_URL + "&" + urllib.urlencode(dict(q=q, rpp=rpp))
  pages = range(1,pages+1) # pages=range(1,16)
  seen_ids = set()
  seen_hashes = set()
  for page in pages:
    url2 = url + "&page=%d" % page
    print>>sys.stderr, "\nSEARCH %s " % url2,
    json = fetch(url2)
    j = simplejson.load(json)
    if not j['results']: break
    for i,r in enumerate(j['results']):
      # Skip identical tweets by message ID
      if r['id'] in seen_ids: continue
      seen_ids.add(r['id'])
      # Check other kinds of equality
      if hash_fn:
        hash = hash_fn(r)
        if hash in seen_hashes: continue
        seen_hashes.add(hash)
      d = time.strptime(r['created_at'].replace(" +0000",""), "%a, %d %b %Y %H:%M:%S")
      r['created_at'] = datetime(*d[:7])
      print>>sys.stderr, ("%s" % i),
      yield r

def tweet_identity(result):
  return result['text']

def tweet_identity_url_norm(result):
  return re.compile(twokenize.URL_S).subn('[URL]', result['text'])[0]

def user_and_tweet_identity(result):
  # Safest, should be default
  return result['text'] + ':' + result['from_user']

def user_and_tweet_identity_url_norm(result):
  return re.compile(twokenize.URL_S).subn('[URL]', result['text'])[0] + ':' + result['from_user']
