from pprint import pprint
from datetime import timedelta, datetime
import query_cache, trends, util, myurl
import sys,os,time
import cPickle as pickle
os.environ['DJANGO_SETTINGS_MODULE'] = 'djfrontend'
import djfrontend.twi.views

def regex_or(*items):
  r = '|'.join(items)
  r = '(' + r + ')'
  return r
from sane_re import *

max_topics_values = [10,40]

def refresh_some_queries(queries):
  def key(url): return 'last_update_' + url
  urls = [query_cache.make_url(q,mt) for q in queries for mt in max_topics_values]
  not_there = [url for url in urls if key(url) not in query_cache.the_cache.tt]
  
  print "adding unseen queries:"
  pprint(not_there)
  for url in not_there:
    query_cache.url_call.force_refresh(url)

  there_pairs = [(url, pickle.loads(query_cache.the_cache.tt[key(url)])) for url in urls if key(url) in query_cache.the_cache.tt]
  there_pairs = [(u,datetime.now() - d) for (u,d) in there_pairs]
  there_pairs = [(u,delt) for u,delt in there_pairs if delt > timedelta(seconds=10)]
  there_pairs.sort(key= lambda (url, delt): delt, reverse=True)
  there_pairs = there_pairs[:2]
  print "refreshing old queries:"
  pprint(there_pairs)
  for url,date in there_pairs:
    query_cache.url_call.force_refresh(url)


def trends_refresh():
  trends.pull()
  queries = [x['simple_query'] for x in trends.current_topics()]
  refresh_some_queries(queries)
  
def prebake_refresh():
  refresh_some_queries(djfrontend.twi.views.PREBAKED_QUERIES)

def loop_forever():
  i = -1
  while True:
    i = (i+1)
    try:
      if i%100 == 0: print "DATE %s  ITER %s" % (datetime.now(), i)
      if i%10 == 0:
        print "prebake refresh"
        prebake_refresh()
      trends_refresh()
    except Exception, e:
      raise e
      print "exception %s %s" % (type(e), e)
    time.sleep(5)




if __name__=='__main__':
  util.fix_stdio()
  loop_forever()
