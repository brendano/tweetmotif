from pprint import pprint
import sys
import fileinput
import simplejson
import cgi
import search
import linkedcorpus
import lang_model
import bigrams
import ranking
import highlighter

def page_header():
  return """
  <style>
  ul { font-size:8pt }
  .topic_hl { font-weight:bold; color: darkblue; }
  </style>
  <h1>why is it trend????</h1>
  """

def form_area(q):
  if q is None: q = ""
  return """<form method=get>query <input name=q value="%s"></form>
  """ % (cgi.escape(q))

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

def nice_tweet(tweet, topic_ngram):
  link = "http://twitter.com/%s/status/%s" % (tweet['from_user'],tweet['id'])
  s = ""
  s += "<span class=text>"
  s += highlighter.highlight(tweet['toks'], {topic_ngram: ("<span class='topic_hl'>","</span>")})
  s += "</span>"
  s += " "
  s += "<a href='%s'>msg</a>" % link
  return s

def my_app(environ, start_response):
  status = '200 OK'
  response_headers = [('Content-type','text/html')]
  start_response(status, response_headers)

  yield page_header()

  vars = cgi.parse_qs(environ['QUERY_STRING'])
  q = vars.get('q')
  q = q and q[0]

  yield form_area(q)
  
  lc = linkedcorpus.LinkedCorpus()

  prebaked = vars.get('prebaked')
  prebaked = prebaked and prebaked[0]

  if not prebaked and not q:
    return

  opts = {}
  if vars.get('pages'):
    opts['pages'] = int(vars['pages'][0])
  do_search(lc, q=q, prebaked=prebaked, **opts)

  def show_results(type):
    for topic_ngram, topic, tweets in ranking.rank_and_filter(lc, background_model, q, type=type):
      s = "<b>%s</b> &nbsp; <small>(%s)</small>" % (topic, len(tweets))
      yield s
      yield "<ul>"
      for i,tweet in enumerate(tweets):
        if i > 20: break
        yield "<li>"
        yield nice_tweet(tweet, topic_ngram)
      yield "</ul>"
  
  yield "<table><tr><th>unigrams <th>bigrams"
  yield "<tr>"
  yield "<td valign=top>"
  for s in show_results('unigram'): yield s
  yield "</td>"
  yield "<td valign=top>"
  for s in show_results('bigram'): yield s
  yield "</td>"
  yield "</table>"

  #yield "<pre>"
  #yield repr(lc.model)
  #yield "<hr>"
  #yield repr(lc.index)
  #yield "</pre>"

def stringify(iter):
  for x in iter:
    if isinstance(x,unicode):
      yield x.encode('utf-8','xmlcharrefreplace')
    elif isinstance(x,str):
      yield x
    else:
      yield x


#background_model = lang_model.MemcacheLM()
background_model = lang_model.TokyoLM()

from wsgiref.simple_server import make_server, demo_app
#httpd = make_server('', 8000, demo_app)
httpd = make_server('', 8000, lambda e,s: stringify(my_app(e,s)))
print "Serving HTTP on port 8000..."
httpd.serve_forever()

