import sys,os,urllib2
from django.http import HttpResponse
from django.template import loader, RequestContext
import simplejson

def index(request):
  """docstring for index"""
  t = loader.get_template("index.tpl")
  c = RequestContext(request, {})
  return HttpResponse(t.render(c))
  
def do_query(request):
  """docstring for do_query"""
  if not "q" in request.REQUEST:
    return HttpResponse("No query")
  else:
    json = urllib2.urlopen("http://localhost:8080/?q=%s&format=json" % urllib2.quote(request.REQUEST['q'])).read()
    return HttpResponse(json)