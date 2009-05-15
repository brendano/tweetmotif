import simplejson
import util
from copy import copy
import urllib2,urllib,sys,pprint,cgi,time
from datetime import datetime,timedelta
from collections import defaultdict

#import socket
import socket
# socket.setdefaulttimeout(1) # http://www.voidspace.org.uk/python/articles/urllib2.shtml
import timeout_urllib2; timeout_urllib2.sethttptimeout(4.0)
import myurl

def fetch(url, printer=None, retries=1):
  for i in range(retries):
    try:
      return urllib2.urlopen(url)
    #except (urllib2.HTTPError, urllib2.URLError), e:
    #except urllib2.URLError, e:
    except (urllib2.URLError, timeout_urllib2.Error, socket.error), e:
      if printer: printer("RETRY after %s %s" % (type(e), e))
      pass
  return urllib2.urlopen(url)

SEARCH_URL = "http://search.twitter.com/search.json?lang=en"
#SEARCH_URL = "http://search.twitter.com/search.json?"
#SEARCH_URL = "http://anyall.org/nph-kazamo/" + SEARCH_URL
#SEARCH_URL = "http://localhost:8500/" + SEARCH_URL

def serial_search(q, pages=10, rpp=100):
  pages = range(1,pages+1) # pages=range(1,16)
  for page in pages:
    page_results = list(search_page(q,page,rpp))
    for r in page_results: yield r
    #if page_results==[]: break

def parallel_search(q, pages=10, rpp=100):
  from threading import Thread
  #pages = range(1,pages+1) # pages=range(1,16)
  task_results = [[]] * pages
  def task(page):
    def _task():
      task_results[page-1] = search_page(q,page=page,rpp=rpp)
    return _task
  threads = [Thread(target=task(page)) for page in range(1,pages+1)]
  #print task_results
  #print threads
  for t in threads: t.start()
  for t in threads: t.join()
  #print [len(t) for t in task_results ]
  results = util.flatten(task_results)
  results.sort(key=lambda tweet: tweet['id'], reverse=True)
  return results

def search_page(q, page, rpp):
  url = SEARCH_URL + "&" + myurl.urlencode(dict(q=q, rpp=rpp, page=page))
  def _print(s):
    print ("SEARCH page %2d: " % page), s
  _print(url)
  try:
    json_fp = fetch(url, _print)
    if 'status' in json_fp.headers.dict: _print(json_fp.headers.dict['status'])
    j = simplejson.load(json_fp)
  except urllib2.HTTPError, e:
    if e.code == 404:
      _print("FAILURE on HTTP error %s STATUS %s" % (e, e.code))
      return []
    else:
      raise e
  except (urllib2.URLError, timeout_urllib2.Error, socket.error), e:
    _print("FAILURE on %s %s" % (type(e), e))
    return []
  #_print("max id",j['max_id']," num results", len(j['results']))
  results = []
  for i,r in enumerate(j['results']):
    tweet_json2py(r)
    results.append(r)
  return results

def tweet_json2py(json_tweet):
  d = time.strptime(json_tweet['created_at'].replace(" +0000",""), "%a, %d %b %Y %H:%M:%S")
  json_tweet['created_at'] = datetime(*d[:7])


import bigrams
from twokenize import Url_RE

def cleaned_results(q, pages=10,rpp=100, key_fn=None, save=None, load=None):
  if not load:
    tweet_iter = parallel_search(q,pages=pages,rpp=rpp)
  else:
    print "LOADING TWEETS FROM %s" % load
    tweet_iter = load_tweets(load)
  if save:
    print "SAVING TWEETS TO %s" % save
    tweet_iter = save_tweets(tweet_iter, filename=save)
  tweet_iter = english_filter(tweet_iter)
  tweet_iter = hard_dedupe_tweets(tweet_iter, key_fn=key_fn)
  return tweet_iter

import cPickle as pickle

def load_tweets(filename):
  tweets = pickle.load(open(filename))
  return tweets

def save_tweets(tweet_iter, filename):
  tweets = list(tweet_iter)
  f = open(filename, 'w')
  pickle.dump(tweets, f)
  f.close()
  return tweets

def english_filter(tweet_iter):
  return (tw for tw in tweet_iter if tw.get('iso_language_code') == 'en')
#   for tw in tweet_iter:
#     if tw.get('iso_language_code') != 'en':
#       #print "dropping non-english tweet, lang %s  id %s"  % (tw.get('iso_language_code'), tw['id'])
#       continue
#     yield tw

def hard_dedupe_tweets(tweet_iter, key_fn):
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
        #print "rejecting dupe", tweet['id']
        continue
      seen_hashes.add(hash)

    yield tweet

def text_identity(tweet):
  return tweet['text']

def text_identity_url_norm(tweet):
  return Url_RE.sub('[URL]', tweet['text'])

def user_and_text_identity(tweet):
  # Safest, should be default
  return (tweet['text'], tweet['from_user'])

def user_and_text_identity_url_norm(tweet):
  return Url_RE.sub('[URL]', tweet['text']) + ':' + tweet['from_user']

###

if __name__=='__main__':
  q = sys.argv[1]
  pages = 10
  tweet_iter = serial_search(q)
  #tweet_iter = dedupe_tweets(tweet_iter, user_and_text_identity_url_norm)
  #tweet_iter = dedupe_tweets(tweet_iter, text_identity_url_norm)
  for tweet in tweet_iter:
    del tweet['created_at']
    #print simplejson.dumps(tweet)
  
