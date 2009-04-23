from pprint import pprint
from copy import copy
import util
import re
import sys
import fileinput
import simplejson
import cgi
import search
import linkedcorpus
import lang_model
import bigrams
import ranking
import twokenize
import highlighter

def page_header():
  return """
  <meta http-equiv="Content-Type" content="text/html;charset=utf-8">
  <style>
  ul { font-size:8pt }
  .topic_hl { font-weight:bold; color: darkblue; }
  a.t { color: black }
  a.m { color: darkblue }
  </style>
  <h1>best explore tool ever</h1>
  """

def safehtml(x):
  return cgi.escape(str(x))

def form_area(opts):
  ret = """<form method=get>
    query <input name=q value="%s">
    for 100*<input name=pages value="%s" size=2> tweets;
    split ug vs bg?  <input name=split value="%s" size=2>
    <input type=submit>
  </form>
  """ % (safehtml(opts.q), safehtml(opts.pages), safehtml(opts.split))
  return ret


def prebaked_iter(filename):
  for line in fileinput.input(filename):
    yield simplejson.loads(line)

def do_search(lc, q=None, prebaked=None, pages=5):
  assert q or prebaked
  if prebaked: tweet_iter = prebaked_iter(prebaked)
  elif q: tweet_iter = search.yield_results(q,pages)

  for i,r in enumerate(tweet_iter):
    print>>sys.stderr, ("%s" % i),
    lc.add_tweet(r)

URL_RE = re.compile("(%s)" % twokenize.URL_S)

def nice_tweet(tweet, topic_ngram):
  link = "http://twitter.com/%s/status/%s" % (tweet['from_user'],tweet['id'])
  s = ""
  s += "<span class=text>"
  text = highlighter.highlight(tweet['toks'], {topic_ngram: ("<span class='topic_hl'>","</span>")})
  text = URL_RE.subn(r'<a class="t" href="\1">\1</a>', text)[0]
  s += text
  s += "</span>"
  s += " "
  #s += "<a class='m' href='%s'>msg</a>" % link
  s += "<a class='m' href='%s'>%s</a>" % (link,tweet['from_user'])
  return s

def opt(name, type=None, default=None):
  o = util.Struct(name=name, type=type, default=default)
  if type is None:
    if default is not None:
      o.type = __builtins__.type(default)
    else: 
      o.type = str #raise Exception("need type for %s" % name)
  if o.type==bool: o.type=int
  return o

def type_clean(val,type):
  if type==bool: return bool(int(val))
  return type(val)

def options(environ, *optlist):
  vars = cgi.parse_qs(environ['QUERY_STRING'])
  opts = util.Struct()
  for opt in optlist:
    val = vars.get(opt.name)
    val = val[0] if val else None
    if val is None and opt.default is not None:
      val = copy(opt.default)
    elif val is None:
      raise Exception("option not given: %s" % opt.name)
    val = type_clean(val, opt.type)
    opts[opt.name] = val
  return opts

  
def my_app(environ, start_response):
  status = '200 OK'
  response_headers = [('Content-type','text/html')]
  start_response(status, response_headers)

  yield page_header()

  opts = options(environ,
      opt('q',str, default=''),
      opt('pages',int, default=2),
      opt('prebaked',str,default=''),
      opt('split',default=0),
      )

  yield form_area(opts)
  
  lc = linkedcorpus.LinkedCorpus()

  if not opts.prebaked and not opts.q:
    return

  do_search(lc, q=opts.q, prebaked=opts.prebaked, pages=opts.pages)

  def show_topic(topic):
    s = "<b>%s</b> &nbsp; <small>(%s)</small>" % (topic.label, len(topic.tweets))
    yield s
    yield "<ul>"
    for i,tweet in enumerate(topic.tweets):
      if i > 20: break
      yield "<li>"
      yield nice_tweet(tweet, topic.ngram)
    yield "</ul>"

  if opts.split:
    def show_results(type):
      for topic in ranking.rank_and_filter1(lc, background_model, opts.q, type=type):
        for s in show_topic(topic): yield s
    yield "<table><tr><th>unigrams <th>bigrams"
    yield "<tr>"
    yield "<td valign=top>"
    for s in show_results('unigram'): yield s
    yield "</td>"
    yield "<td valign=top>"
    for s in show_results('bigram'): yield s
    yield "</td>"
    yield "</table>"

  else:
    for topic in ranking.rank_and_filter3(lc, background_model, opts.q):
      for s in show_topic(topic): yield s



def app_stringify(iter):
  for x in iter:
    yield util.stringify(x, 'utf8', 'xmlcharrefreplace')

if __name__=='__main__':
  #background_model = lang_model.MemcacheLM()
  background_model = lang_model.TokyoLM()

  from wsgiref.simple_server import make_server, demo_app
  #httpd = make_server('', 8000, demo_app)
  httpd = make_server('', 8000, lambda e,s: app_stringify(my_app(e,s)))
  print "Serving HTTP on port 8000..."
  httpd.serve_forever()

