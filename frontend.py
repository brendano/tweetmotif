from pprint import pprint
from datetime import datetime,timedelta
import time
from copy import copy
import util
import re
import sys
import os
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

if os.popen("hostname").read().strip()=='btoc.local':
  STATIC = "http://localhost/d/twi/twi/static"
else:
  STATIC = "http://anyall.org/twistatic"

def page_header():
  return """
  <meta http-equiv="Content-Type" content="text/html;charset=utf-8">
  <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.3.2/jquery.min.js"></script>
  <script src="%(STATIC)s/js.js"></script>
  <script src="%(STATIC)s/jquery.query-2.1.3.js"></script>
  <LINK REL ="STYLESHEET" TYPE="text/css" HREF="%(STATIC)s/css.css">

  <h1>omg twitter</h1>
  """ % globals()

def safehtml(x):
  return cgi.escape(str(x),quote=True)

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
  if type==bool:
    if val in ['0','f','false','False','no','n']: return False
    if val in ['1','t','true','True','yes','n']: return True
    raise Exception("bad bool value %s" % repr(val))
  return type(val)

class Opts(util.Struct):
  " modelled on trollop.rubyforge.org and gist.github.com/5682"
  def __init__(self, environ, *optlist):
    vars = cgi.parse_qs(environ['QUERY_STRING'])
    for opt in optlist:
      val = vars.get(opt.name)
      val = val[0] if val else None
      if val is None and opt.default is not None:
        val = copy(opt.default)
      elif val is None:
        raise Exception("option not given: %s" % opt.name)
      val = type_clean(val, opt.type)
      self[opt.name] = val
  def input(self, name, **kwargs):
    val = self[name]
    h = '''<input id=%s name=%s value="%s"''' % (name, name, safehtml(val))
    more = {}
    if type(val)==int:
      more['size'] = 2
    elif type(val)==float:
      more['size'] = 4
    more.update(kwargs)
    for k,v in more.iteritems():
      h += ''' %s="%s"''' % (k,v)
    h += ">"
    return h

def form_area(opts):
  ret = "<form method=get> query " + opts.input('q')
  ret += " for 100*" + opts.input('pages') + " tweets; "
  ret += " simple?" + opts.input('simple')
  ret += " split?" + opts.input('split')
  ret += " max topics" + opts.input('max_topics')
  ret += " ncol" + opts.input('ncol')
  ret += " <input type=submit>"
  ret += "</form>"
  return ret

def prebaked_iter(filename):
  for line in fileinput.input(filename):
    yield simplejson.loads(line)

from sane_re import *
At = _R(r'(@)(\w+)')



def nice_tweet(tweet, q_toks, topic_ngram):
  link = "http://twitter.com/%s/status/%s" % (tweet['from_user'],tweet['id'])
  s = ""
  s += "<span class=text>"
  hl_spec = {topic_ngram: ("<span class=topic_hl>","</span>")}
  for ug in set(bigrams.unigrams(q_toks)):
    if ug[0] in bigrams.stopwords: continue
    if ug[0] in topic_ngram: continue
    hl_spec[ug] = ("<span class=q_hl>","</span>")
  text = highlighter.highlight(tweet['toks'], hl_spec)
  text = twokenize.Url_RE.subn(r'<a class=t target=_blank href="\1">\1</a>', text)[0]
  #text = twokenize.AT_RE.subn(r'<a class=at target=_blank href="\1">\1</a>
  text = At.sub(text, r'@<a class=at target=_blank href="http://twitter.com/\2">\2</a>')
  s += text
  s += "</span>"
  s += " "
  #s += "<a class=m href='%s'>msg</a>" % link
  s += "<a class=m target=_blank href='%s'>%s</a>" % (link,tweet['from_user'])
  return s

def single_query(q, topic_label, pages=1, exclude=()):
  q_toks = bigrams.tokenize_and_clean(q, alignments=False)
  q = '''%s "%s"''' % (q,topic_label)
  sub_topic_ngram = tuple(bigrams.tokenize_and_clean(topic_label,True))
  exclude = set(exclude)
  yield "<ul>"
  for tweet in search.deduped_results(q, pages=pages, hash_fn=search.user_and_text_identity):
    if tweet['id'] in exclude: continue
    tweet['toks'] = bigrams.tokenize_and_clean(tweet['text'],True)
    yield "<li>" + nice_tweet(tweet, q_toks, sub_topic_ngram)
  yield "</ul>"

def table_byrow(items, ncol=3):
  yield "<table>"
  for i,x in enumerate(items):
    if i%ncol == 0:
      yield "<tr>"
    yield "<td>"
    yield x
  yield "<td>" * (len(items) % ncol)
  yield "</table>"

def topic_fragment(q_toks, topic):
  topic = copy(topic)
  h = "<ul>"
  for tweet in topic['tweets']:
    h+="<li>" + nice_tweet(tweet, q_toks, topic.ngram)
  h+="</ul>"

  topic['tweets_html'] = h
  del topic['tweets']
  return topic

def nice_date(d):
  return d.strftime("%Y-%m-%dT%H:%M:%S")

def nice_unitted_num(n,sing,plur=None):
  if n==1: return "%d %s" % (n,sing)
  plur = plur or sing+"s"
  return "%d %s" % (n,plur)

def nice_datespan(d1,d2):
  if d2<d1: d1,d2=d2,d1
  #if (datetime.utcnow() - d2) < timedelta(hours=4):
  #  s = "now"
  #else:
  #  s = d2.strftime("%Y-%m-%dT%H:%M:%S")
  #s += " back to "
  s = "over the last "
  delt = datetime.utcnow()-d1
  x = []
  if delt.days:
    x.append(nice_unitted_num(delt.days, "day"))
    if delt.seconds > 60*60: 
      x.append(nice_unitted_num(int(delt.seconds/60/60), "hour"))
  else:
    x.append(nice_unitted_num(int(delt.seconds/60/60), "hour"))
  s += ', '.join(x)
  #s += " ago"
  return s



  
  return "%s back to %s" % (d2.strftime("%Y-%m-%dT%H:%M:%S"), d1.strftime("%Y-%m-%dT%H:%M:%S"))

def my_app(environ, start_response):
  status = '200 OK'
  response_headers = [('Content-type','text/html')]
  start_response(status, response_headers)

  opts = Opts(environ,
      opt('q', default=''),
      opt('pages', default=2),
      opt('prebaked', default=''),
      opt('split', default=0),
      opt('simple', default=0),
      opt('max_topics', default=50),
      opt('ncol', default=3),
      opt('single_query', default=0),
      )

  if opts.single_query:
    opts2 = Opts(environ, opt('q',str), opt('topic_label',str), opt('exclude',default=''))
    opts2.exclude = [int(x) for x in opts2.exclude.split()]
    for x in single_query(**opts2):
      yield x
    return

  yield page_header()
  yield form_area(opts)
  
  lc = linkedcorpus.LinkedCorpus()

  if not opts.prebaked and not opts.q:
    return

  if opts.prebaked: tweet_iter = prebaked_iter(opts.prebaked)
  elif opts.q: tweet_iter = search.deduped_results(opts.q, pages=opts.pages, hash_fn=search.user_and_text_identity)  #hash_fn=search.tweet_identity)

  lc.fill_from_tweet_iter(tweet_iter)

  q_toks = bigrams.tokenize_and_clean(opts.q, True)

  if not opts.simple:
    yield "<table><tr>"
    yield "<th>topics"
    if lc.tweets_by_id:
      earliest = min(tw['created_at'] for tw in lc.tweets_by_id.itervalues())
      latest   = max(tw['created_at'] for tw in lc.tweets_by_id.itervalues())
      s=  "for %d tweets" % len(lc.tweets_by_id)
      s+= " from %s" % nice_datespan(earliest,latest)
      yield " <small>%s</small>" % s


    yield "<th>tweets"
    yield "<tr><td valign=top id=topic_list>"
    res = ranking.rank_and_filter3(lc, background_model, opts.q)
    topics = res.topics
    if len(topics) > opts.max_topics:
      print "throwing out %d topics" % (len(topics)-opts.max_topics)
      topics = topics[:opts.max_topics]
    if res.leftover_tweets:
      topics.append(util.Struct(ngram=('**EXTRAS**',),label="<i>[other...]</i>",tweets=res.leftover_tweets,ratio=-42))
    topic_labels = ("""<span class=topic_label onclick="topic_click(this)" topic_label="%s">%s</span><br>""" % (cgi.escape(topic.label), topic.label.replace(" ","&nbsp;"))  for topic in topics)
    #for x in topic_labels: yield x
    for x in table_byrow(list(topic_labels), ncol=opts.ncol): yield x
    #if res.leftover_tweets:
    #  yield "%d extra tweets without topics" % len(res.leftover_tweets)

    yield "<td valign=top>"
    yield "<div id=tweets>"
    yield "click on a topic on the left please"
    yield "</div>"
    yield "<div id=tweets_more>"
    yield "</div>"
    yield "</table>"
    yield "<script>"
    for t in topics:  t['tweet_ids'] = util.myjoin([tw['id'] for tw in t['tweets']])
    bigass = dict((t.label, topic_fragment(q_toks,t)) for t in topics)
    yield "topics = "
    yield simplejson.dumps(bigass)
    yield ";"
    yield "load_default_topic();"
    yield "</script>"
    return

  def simple_show_topic(topic):
    s = "<b>%s</b> &nbsp; <small>(%s)</small>" % (topic.label, len(topic.tweets))
    yield s
    yield "<ul>"
    for i,tweet in enumerate(topic.tweets):
      if i > 20: break
      yield "<li>"
      yield nice_tweet(tweet, q_toks, topic.ngram)
    yield "</ul>"

  if opts.split:
    def show_results(type):
      for topic in ranking.rank_and_filter1(lc, background_model, opts.q, type=type):
        for s in simple_show_topic(topic): yield s
    yield "<table><tr><th>unigrams <th>bigrams"
    yield "<tr>"
    yield "<td valign=top>"
    for s in show_results('unigram'): yield s
    yield "</td>"
    yield "<td valign=top>"
    for s in show_results('bigram'): yield s
    yield "</td>"
    yield "</table>"
  elif not opts.split:
    for topic in ranking.rank_and_filter3(lc, background_model, opts.q):
      for s in simple_show_topic(topic):
        yield s
        #yield cgi.escape(simplejson.dumps(topic_fragment(q_toks,topic)))






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

