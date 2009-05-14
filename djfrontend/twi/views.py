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

PREBAKED_QUERIES = ['sandwich', 'coffee', ':)', ':(', 'aw', 'awwwwww', '@the_real_shaq','@twitter', '"san francisco" weather','tweetmotif']

@response('index.tpl')
def index(request):
  d = {}
  d['trend_topics'] = trends.current_topics()
  d['default_query'] = ''  #d['trend_topics'][0]['name'] if d['trend_topics'] else "sandwich"
  d['prebaked_queries'] = PREBAKED_QUERIES
  # c = RequestContext(request, d)
  return d

def show_results(request, query):
    return HttpResponseRedirect("/#" + query)

@response('about.tpl')
def about(request):
  return {}

########

import query_cache

def do_query(request):
  if not "q" in request.REQUEST:
    return HttpResponse("No query")
  else:
    max_topics = request.REQUEST.get("max_topics", 40)
    json = query_cache.call(q=request.REQUEST['q'], max_topics=max_topics)
    return HttpResponse(json)
