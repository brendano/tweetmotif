import sys,os,urllib2
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader, RequestContext
import simplejson
import re
from django.shortcuts import render_to_response
import trends, myurl, util
import timeout_urllib2; timeout_urllib2.sethttptimeout(20.0)


_IPHONE_UA = re.compile(r'Mobile.*Safari')
def is_iphone(request):
    return True
    return _IPHONE_UA.search(request.META['HTTP_USER_AGENT']) is not None

def response(template,*args):
    def _process_view(view_func):
        def _handle_request(request,*args,**kwargs):
            context = view_func(request,*args,**kwargs)
            if context is None: context = dict()
            if isinstance(context,dict):
                path = is_iphone(request) and 'iphone' or 'web'
                return render_to_response('%s/%s' % (path,template),RequestContext(request,dict=context))
            else:
                return context #this is probably a redirect

        return _handle_request
    return _process_view


BACKEND_URL = "http://localhost:8080" if sys.platform=='darwin' else "http://localhost/twitterthemes/backend"

@response('index.tpl')
def index(request):
  d = {}
  d['trend_topics'] = trends.current_topics()
  d['default_query'] = ''  #d['trend_topics'][0]['name'] if d['trend_topics'] else "sandwich"
  for x in d['trend_topics']:
    # twitter's x['query'] is too complex, often with boolean OR's.  ugly.  silly to optimize recall so let's do only one form.
    x['simple_query'] = ('"%s"' % x['name']) if len(x['name'].split())>1 else x['name']
  d['prebaked_queries'] = ['sandwich', 'coffee', ':)', ':(', 'aw', 'awwwwww', 'school', 'jobs']
  c = RequestContext(request, d)
  return d
      

def show_results(request, query):
    return HttpResponseRedirect("/#" + query)

def do_query(request):
  if not "q" in request.REQUEST:
    return HttpResponse("No query")
  else:
    q = util.stringify(myurl.quote(request.REQUEST['q']))
    max_topics = request.REQUEST.get("max_topics", 40)
    json = urllib2.urlopen(BACKEND_URL + "/?q=%s&max_topics=%s&format=json" % (q, max_topics)).read()
    return HttpResponse(json)



