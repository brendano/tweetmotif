import simplejson
import urllib2,urllib,sys,pprint,cgi,time
from datetime import datetime,timedelta

import socket; socket.setdefaulttimeout(2) # http://www.voidspace.org.uk/python/articles/urllib2.shtml
#import timeout_urllib2; timeout_urllib2.sethttptimeout(2.0)

def fetch(url):
  for i in range(2):
    try: return urllib2.urlopen(url)
    except (urllib2.HTTPError, urllib2.URLError), e:
      print type(e), e
      pass
  return urllib2.urlopen(url)

SEARCH_URL = "http://search.twitter.com/search.json?lang=en"
SEARCH_URL = "http://anyall.org/nph-kazamo/" + SEARCH_URL

def yield_results(q, pages=10, rpp=100):
  url = SEARCH_URL + "&" + urllib.urlencode(dict(q=q, rpp=rpp))
  pages = range(1,pages+1) # pages=range(1,16)
  for page in pages:
    url2 = url + "&page=%d" % page
    print>>sys.stderr, "\nSEARCH %s " % url2,
    json = fetch(url2)
    j = simplejson.load(json)   # should i/o protect
    if not j['results']: break
    for i,r in enumerate(j['results']):
      d = time.strptime(r['created_at'].replace(" +0000",""), "%a, %d %b %Y %H:%M:%S")
      r['created_at'] = datetime(*d[:7])
      print>>sys.stderr, ("%s" % i),
      yield r


import bigrams
from twokenize import URL_RE

def deduped_results(q, pages=10,rpp=100, hash_fn=None):
  seen_ids = set()
  seen_hashes = set()

  for tweet in yield_results(q,pages=pages,rpp=rpp):
    # Skip identical tweets by message ID
    if tweet['id'] in seen_ids: continue
    seen_ids.add(tweet['id'])

    bigrams.analyze_tweet(tweet)

    # Check other kinds of equality
    if hash_fn:
      hash = hash_fn(tweet)
      if hash in seen_hashes:
        print "rejecting dupe", tweet
        continue
      seen_hashes.add(hash)

    yield tweet

def text_identity(tweet):
  return tweet['text']

def text_identity_url_norm(tweet):
  return URL_RE.subn('[URL]', tweet['text'])[0]

def user_and_text_identity(tweet):
  # Safest, should be default
  return tweet['text'] + ':' + tweet['from_user']

def user_and_text_identity_url_norm(tweet):
  return URL_RE.subn('[URL]', tweet['text'])[0] + ':' + tweet['from_user']
