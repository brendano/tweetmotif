import sys,os,urllib2
# add the twi root
dir = os.path.abspath(os.path.dirname(__file__))
dir = os.path.join(dir, '..','..')
sys.path.insert(0, dir)
os.chdir(dir)  # makes module loading for pickle easier .. alternative is to fix twi/*.py to not assume chdir-ness.  django seems ok with this tho
import common

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
    s = urllib2.urlopen("http://localhost:8080/?q=%s&format=pickle" % urllib2.quote(request.REQUEST['q'])).read()
    topic_res = pickle.loads(s)
    topic_info = dict(
      (t.label,
       {
         'label' : t.label,
         'tweet_ids' : t.tweet_ids,
         'groups' : [{'head_html':g.head_html, 'rest_htmls':g.rest_htmls} for g in t.groups]
       })
        for t in topic_res.topics)
    topic_list = [t.label for t in topic_res.topics]
    results = {"topic_list":topic_list, "topic_info": topic_info}
    # pickle.dump(topic_res, open("results.full",'w'))
    # pickle.dump(results, open("results.trim",'w'))
    return HttpResponse(simplejson.dumps(results))
