import simplejson
from copy import copy
import urllib2,urllib,sys,pprint,cgi,time
from datetime import datetime,timedelta
from collections import defaultdict

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
#SEARCH_URL = "http://anyall.org/nph-kazamo/" + SEARCH_URL

def yield_results(q, pages=10, rpp=100):
  url = SEARCH_URL + "&" + urllib.urlencode(dict(q=q, rpp=rpp))
  pages = range(1,pages+1) # pages=range(1,16)
  for page in pages:
    url2 = url + "&page=%d" % page
    print "SEARCH %s " % url2
    json = fetch(url2)
    j = simplejson.load(json)   # should i/o protect
    if not j['results']: break
    for i,r in enumerate(j['results']):
      d = time.strptime(r['created_at'].replace(" +0000",""), "%a, %d %b %Y %H:%M:%S")
      r['created_at'] = datetime(*d[:7])
      #print>>sys.stderr, ("%s" % i),
      yield r


import bigrams
from twokenize import Url_RE

def cleaned_results(q, pages=10,rpp=100, key_fn=None):
  tweet_iter = yield_results(q,pages=pages,rpp=rpp)
  tweet_iter = dedupe_tweets(tweet_iter, key_fn=key_fn)
  #tweet_iter = group_multitweets(tweet_iter)
  return tweet_iter

def dedupe_tweets(tweet_iter, key_fn):
  seen_ids = set()
  seen_hashes = set()
  for tweet in tweet_iter:
    # Skip identical tweets by message ID
    if tweet['id'] in seen_ids: continue
    seen_ids.add(tweet['id'])

    bigrams.analyze_tweet(tweet)

    # Check other kinds of equality
    if key_fn:
      hash = key_fn(tweet)
      if hash in seen_hashes:
        print "rejecting dupe", tweet['id']
        continue
      seen_hashes.add(hash)

    yield tweet

def text_identity(tweet):
  return tweet['text']

def text_identity_url_norm(tweet):
  return Url_RE.sub('[URL]', tweet['text'])

def user_and_text_identity(tweet):
  # Safest, should be default
  return tweet['text'] + ':' + tweet['from_user']

def user_and_text_identity_url_norm(tweet):
  return Url_RE.sub('[URL]', tweet['text']) + ':' + tweet['from_user']


def group_multitweets(tweet_iter, key_fn=lambda tw: tw['text'], preserve=('text','toks',)):
  # TODO make generic merge_tweets(tw1,tw2) so can easily change the key_fn here
  index = defaultdict(list)
  for tweet in tweet_iter:
    index[key_fn(tweet)].append(tweet)
  multitweets = {}
  for key,tweets in index.iteritems():
    if len(tweets)==1: continue
    multitweet = copy(tweets[0])
    orig_keys = multitweet.keys()
    multikeys = set(orig_keys) - set(preserve)
    for k in multikeys:
      del multitweet[k]
      multitweet['multi_' + k] = [tw[k] for tw in tweets]
    multitweet['orig_tweets'] = tweets
    multitweet['id'] = " ".join([str(tw['id']) for tw in tweets])
    multitweet['multi'] = True
    multitweets[key] = (multitweet,)
    print "multitweet", multitweet['id']
  index.update(multitweets)
  for k,tweets_singleton in index.iteritems():
    assert len(tweets_singleton)==1
    yield tweets_singleton[0]


if __name__=='__main__':
  q = sys.argv[1]
  pages = 10
  tweet_iter = yield_results(q)
  #tweet_iter = dedupe_tweets(tweet_iter, user_and_text_identity_url_norm)
  tweet_iter = dedupe_tweets(tweet_iter, text_identity_url_norm)
  for tweet in tweet_iter:
    del tweet['created_at']
    #print simplejson.dumps(tweet)
  
