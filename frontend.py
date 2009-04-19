from pprint import pprint
import cgi
import search
import linkedcorpus
import lang_model
import bigrams

def page_header():
  return """
  <style> ul { font-size:8pt } </style>
  <h1>why is it trend????</h1>
  """

def form_area(q):
  if q is None: q = ""
  return """<form method=get>query <input name=q value="%s></form>
  """ % (cgi.escape(q))


def do_search(q, lc):
  for r in search.yield_results(q,5):
    lc.add_tweet(r)

def nice_tweet(tweet):
  link = "http://twitter.com/%s/status/%s" % (tweet['from_user'],tweet['id'])
  s = ""
  s += "<span class=text>" + tweet['text'] + "</span>"
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
  do_search(q, lc)
  for ratio,bigram in bigrams.compare_models(lc.model, background_model,'bigram',1):
    s = "<b>%s</b> &nbsp; <small>(%s)</small>" % (" ".join(bigram), ratio)
    yield s
    yield "<ul>"
    for i,tweet in enumerate(lc.index[bigram]):
      if i > 10: break
      yield "<li>"
      yield nice_tweet(tweet)
    yield "</ul>"

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


background_model = lang_model.MemcacheLM()

from wsgiref.simple_server import make_server, demo_app
#httpd = make_server('', 8000, demo_app)
httpd = make_server('', 8000, lambda e,s: stringify(my_app(e,s)))
print "Serving HTTP on port 8000..."
httpd.serve_forever()

