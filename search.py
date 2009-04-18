import simplejson
import urllib2,sys,pprint,cgi,time
from datetime import datetime,timedelta

#import codecs; sys.stdout = codecs.open('/dev/stdout','w',encoding='utf8',buffering=0)

#min_datetime = datetime.now() + timedelta(days=2)
#
#query = " ".join(sys.argv[1:])
#query_terms = sys.argv[1:]
#
#need_date_restriction = False

def fetch(url):
  for i in range(2):
    try: return urllib2.urlopen(url)
    except urllib2.HTTPError: pass
  return urllib2.urlopen(url)

#SEARCH_URL = "http://search.twitter.com/search.json?q=%s&rpp=100"
SEARCH_URL = "http://anyall.org/nph-kazamo/http://search.twitter.com/search.json?q=%s&rpp=100"

def yield_results(q, pages=10):   # pages=range(1,16)
  url = SEARCH_URL % urllib2.quote(q)
  pages = range(1,pages)
  for page in pages:
  #for page in [1]:
    #print>>sys.stderr, "page %d" % page
    json = fetch(url + "&page=%d" % page)
    j = simplejson.load(json)
    if not j['results']: break
    for r in j['results']:
      d = time.strptime(r['created_at'].replace(" +0000",""), "%a, %d %b %Y %H:%M:%S")
      #print time.strftime("%Y-%m-%dT%H:%M:%S",d) + "\t" + r['text'].replace("\n"," ")
      r['created_at'] = datetime(*d[:7])
      yield r
      #yield {'created_at':datetime(*d[:7]), 'text':r['text']}
      #yield {'created_at':time.strftime("%Y-%m-%dT%H:%M:%S",d), 'text':r['text']}
      #min_datetime = min(min_datetime,  datetime(*d[:7]))


#while True:
#
#  if need_date_restriction:
#    query2 = query + " until:" + min_datetime.strftime("%Y-%m-%d")
#  else: 
#    query2 = query
#  url = "http://search.twitter.com/search.json?q=%s&rpp=100" % (urllib2.quote(query2),)
#  print>>sys.stderr, "*** ",url
#
#  for page in range(1,16):
#  #for page in [1]:
#    #print>>sys.stderr, "page %d" % page
#    json = fetch(url + "&page=%d" % page)
#    j = simplejson.load(json)
#    if not j['results']: break
#    for r in j['results']:
#      d = time.strptime(r['created_at'].replace(" +0000",""), "%a, %d %b %Y %H:%M:%S")
#      print time.strftime("%Y-%m-%dT%H:%M:%S",d) + "\t" + r['text'].replace("\n"," ")
#      min_datetime = min(min_datetime,  datetime(*d[:7]))
#  
#  need_date_restriction = True
#  min_datetime = min_datetime - timedelta(days=1)
