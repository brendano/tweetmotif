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
  d['default_query'] = d['trend_topics'][0]['query'] if d['trend_topics'] else "sandwich"
  c = RequestContext(request, d)
  return HttpResponse(t.render(c))
  
def do_query(request):
  if not "q" in request.REQUEST:
    return HttpResponse("No query")
  else:
    q = util.stringify(myurl.quote(request.REQUEST['q']))
    json = urllib2.urlopen(BACKEND_URL + "/?q=%s&format=json" % q).read()
    return HttpResponse(json)
