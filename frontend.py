from pprint import pprint
import search
import linkedcorpus
import model_analysis


def page_header():
  return """
  <h1>why is it trend????</h1>
  """

def do_search(q, lc):
  for r in search.yield_results(q,2):
    lc.add_tweet(r)

def my_app(environ, start_response):
  status = '200 OK'
  response_headers = [('Content-type','text/html')]
  start_response(status, response_headers)
  yield page_header()
  lc = linkedcorpus.LinkedCorpus()
  do_search("boyle", lc)
  for ratio,bigram in model_analysis.compare_models(lc.model, model_analysis.background_model):
    s = "<br>%s &nbsp; %s" % (" ".join(bigram), ratio)
    yield str(s)
    for tweet in lc.index[bigram]:
      yield "<br> &nbsp;"
      yield repr(tweet)
  #yield "<pre>"
  #yield repr(lc.model)
  #yield "<hr>"
  #yield repr(lc.index)
  #yield "</pre>"

print "loading corpus"
model_analysis.load_background_model()

from wsgiref.simple_server import make_server, demo_app
httpd = make_server('', 8000, my_app)
print "Serving HTTP on port 8000..."

# Respond to requests until process is killed
httpd.serve_forever()

