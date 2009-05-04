# Create your views here.

import sys,urllib2
# sys.path.insert(0, "/Users/mkrieger/src/twi")
import cPickle as pickle
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
    s=urllib2.urlopen("http://localhost:8080/?q=%s&format=pickle" % urllib2.quote(request.REQUEST['q'])).read()
    topic_results=pickle.loads(s)
    bigass_topic_dict = dict((t['label'], dict(
      label=t['label'], 
      nice_tweets=t['nice_tweets'], 
      tweet_ids=t['tweet_ids'],
    )) for t in topic_results)    
    topic_list = [x['label'] for x in topic_results]
    return HttpResponse(simplejson.dumps({"topic_list":topic_list, "topic_info": bigass_topic_dict}))
