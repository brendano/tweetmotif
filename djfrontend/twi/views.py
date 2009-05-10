import sys,os,urllib2
from django.http import HttpResponse
from django.template import loader, RequestContext
import simplejson

import trends, myurl, util
import timeout_urllib2; timeout_urllib2.sethttptimeout(10.0)

BACKEND_URL = "http://localhost:8080" if sys.platform=='darwin' else "http://localhost/twitterthemes/backend"
def index(request):
  t = loader.get_template("index.tpl")
  d = {}
  d['trend_topics'] = trends.current_topics()
  d['default_query'] = d['trend_topics'][0]['name'] if d['trend_topics'] else "sandwich"
  for x in d['trend_topics']:
    # twitter's x['query'] is too complex, often with boolean OR's.  ugly.  silly to optimize recall so let's do only one form.
    x['simple_query'] = ('"%s"' % x['name']) if len(x['name'].split())>1 else x['name']
  d['prebaked_queries'] = ['sandwich', 'coffee', ':)', ':(', 'aw', 'awwwwww', 'school', 'jobs']
  c = RequestContext(request, d)
  return HttpResponse(t.render(c))
  
def do_query(request):
  if not "q" in request.REQUEST:
    return HttpResponse("No query")
  else:
    q = util.stringify(myurl.quote(request.REQUEST['q']))
    json = urllib2.urlopen(BACKEND_URL + "/?q=%s&format=json" % q).read()
    return HttpResponse(json)
