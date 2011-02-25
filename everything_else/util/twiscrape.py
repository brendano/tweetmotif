#!/usr/bin/env python2.5
import simplejson
import urllib2,sys,pprint,cgi,time,re
from datetime import datetime,timedelta
import socket; socket.setdefaulttimeout(2) # http://www.voidspace.org.uk/python/articles/urllib2.shtml

import codecs; sys.stdout = codecs.open('/dev/stdout','w',encoding='utf8',buffering=0)

query = " ".join(sys.argv[1:])
query_terms = sys.argv[1:]
min_datetime = datetime.now() + timedelta(days=2)
need_date_restriction = False
seen_ids = set()

def fetch(url):
  res = None
  for i in range(3):
    if res is not None: break
    try:
      res = urllib2.urlopen(url)
    except (urllib2.URLError, urllib2.HTTPError):
      time.sleep(0.1)
      pass
  return res

BAD_WS = re.compile(r'[\r\n\t]')

while True:

  if need_date_restriction:
    query2 = query + " until:" + min_datetime.strftime("%Y-%m-%d")
  else: 
    query2 = query
  #url = "http://search.twitter.com/search.json?q=%s&rpp=100" % (urllib2.quote(query2),)
  url = "http://search.twitter.com/search.json?q=%s&rpp=100&lang=en" % (urllib2.quote(query2),)
  print>>sys.stderr, "*** ",url

  for page in range(1,16):
    json = fetch(url + "&page=%d" % page)
    if json is None:
      if url_failures_in_a_row > 3:
        print>>sys.stderr, "too many url failures in a row, so exiting completely"
        sys.exit(0)
      print>>sys.stderr,"many HTTP failures, so continuing to next url"
      url_failures_in_a_row += 1
      continue
    url_failures_in_a_row = 0
    j = simplejson.load(json)
    if not j['results']: break
    for r in j['results']:
      if r['id'] in seen_ids: 
        #print>>sys.stderr, "dup ",r['id']   # lots!
        continue
      seen_ids.add(r['id'])
      d = time.strptime(r['created_at'].replace(" +0000",""), "%a, %d %b %Y %H:%M:%S")
      row = (
          str(r['id']),
          time.strftime("%Y-%m-%dT%H:%M:%S",d),
          r['from_user'],
          BAD_WS.sub(' ',r['text']),
      )
      print "\t".join(row)
      min_datetime = min(min_datetime,  datetime(*d[:7]))

  need_date_restriction = True
  min_datetime = min_datetime - timedelta(days=1)
