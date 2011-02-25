#!/usr/bin/env python
from pprint import pprint
import cPickle as pickle
from datetime import datetime,timedelta
from collections import defaultdict
import time
from copy import copy
import re
import sys
import os
import simplejson
import cgi
import util
import sane_re
import search
import linkedcorpus
import lang_model
import bigrams
import ranking
import twokenize
import highlighter
import deduper

if os.popen("hostname").read().strip()=='btoc.local':
  STATIC = "http://localhost/d/twi/twi/static"
else:
  STATIC = "http://tweetmotif.com/backend_static"

def page_header():
  return '''
  <meta http-equiv="Content-Type" content="text/html;charset=utf-8">
  <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.3.2/jquery.min.js"></script>
  <script src="%(STATIC)s/js.js"></script>
  <script src="%(STATIC)s/jquery.query-2.1.3.js"></script>
  <LINK REL ="STYLESHEET" TYPE="text/css" HREF="%(STATIC)s/css.css">

  <div><b>twitter themes/topics/clusters summarization explorer thingamajigger</b></div>
  ''' % globals()

def safehtml(x):
  return cgi.escape(str(x),quote=True)

type_builtin = type
def opt(name, type=None, default=None):
  o = util.Struct(name=name, type=type, default=default)
  if type is None:
    if default is not None:
      o.type = type_builtin(default)
    else: 
      o.type = str #raise Exception("need type for %s" % name)
  #if o.type==bool: o.type=int
  return o

def type_clean(val,type):
  if type==bool:
    if val in (False,0,'0','f','false','False','no','n'): return False
    if val in (True,1,'1','t','true','True','yes','y'): return True
    raise Exception("bad bool value %s" % repr(val))
  if type==str or type==unicode:
    # nope no strings, you're gonna get unicode instead!
    return util.unicodify(val)
  return type(val)

class Opts(util.Struct):
  " modelled on trollop.rubyforge.org and gist.github.com/5682 "
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
  for k in 'ncol max_topics smoothing'.split():
    ret += " " + k + opts.input(k)
  ret += " <input type=submit>"
  ret += "</form>"
  return ret

def table_byrow(items, ncol):
  yield "<table>"
  for i,x in enumerate(items):
    if i%ncol == 0:
      yield "<tr>"
    yield "<td>"
    yield x
  yield "<td>" * (len(items) % ncol)
  yield "</table>"


######   below here stuff should be relevant to both dev and django frontends


from sane_re import *
At = _R(r'(@)(\w+)')

Url_RE = sane_re._R(twokenize.Url_RE)
def linkify(text, klass):
  def f(m):
    if m[1].startswith("http"): url = m[1]
    else: url = "http://" + m[1]
    return m.sre.expand(r'<a class="%s" target="_blank" href="%s">\1</a>' % (klass,url))
  return Url_RE.gsub(text, f)

# nice_tweet_cache = tchelpers.open("nice_tweets.tch")

def nice_tweet(tweet, q_toks, topic_ngrams):
  return _nice_tweet(tweet,q_toks,topic_ngrams)  # disable cache

  key = pickle.dumps( (tweet, q_toks, topic_ngram) )
  if key in nice_tweet_cache:
    #print "nice_tweet CACHE HIT"
    return nice_tweet_cache[key]
  else:
    #print "NEW nice_tweet"
    nt = _nice_tweet(tweet,q_toks,topic_ngram)
    nice_tweet_cache[key] = nt
    return nt

import kmp

def _nice_tweet(tweet, q_toks, topic_ngrams):
  s = ""
  s += '<span class="text">'
  hl_spec = dict((ng, ('<span class="topic_hl">','</span>')) for ng in topic_ngrams)
  for qg in list(set(bigrams.bigrams(q_toks))) + list(set(bigrams.unigrams(q_toks))):
    if len(qg)==1 and qg[0] in bigrams.super_stopwords: continue
    if len(qg)==1 and any(qg[0] in ng for ng in topic_ngrams): continue
    if len(qg)>=2 and any(kmp.isSubseq(qg, ng) for ng in topic_ngrams): continue
    hl_spec[qg] = ('<span class="q_hl">','</span>')
  text = highlighter.highlight(tweet['toks'], hl_spec)
  text = linkify(text, klass='t')
  #text = twokenize.Url_RE.subn(r'<a class=t target=_blank href="\1">\1</a>', text)[0]
  #text = twokenize.AT_RE.subn(r'<a class=at target=_blank href="\1">\1</a>
  text = At.gsub(text, r'<a class="at" target="_blank" href="http://twitter.com/\2">@\2</a>')
  s += text
  s += "</span>"
  
  s += " &nbsp; "
  s += '<span class="authors">'
  if 'orig_tweets' in tweet:
    s += "%d authors:" % len(tweet['orig_tweets'])
    subtweets = tweet['orig_tweets']
  else:
    subtweets = (tweet,)
  for subtweet in subtweets:
    user = subtweet['from_user']
    link = "http://twitter.com/%s/status/%s" % (user, subtweet['id'])
    s += " "
    # calling encode() here makes NO SENSE AT ALL why do we need it?
    s += '<a class="m" target="_blank" href="%s">%s</a>' % (util.stringify(link), util.stringify(user))
  s += '</span>'
  return s

HTTP_RE = _R(r'\bhttp://')
WWW_RE = _R(r'\bwww[0-9]?\.')

def nice_label(topic_label):
  s = topic_label
  s = HTTP_RE.replace(s,'')
  s = WWW_RE.replace(s,'')
  return s

def topic_group_html(groups):
  h = "<ul>"
  for group in groups:
    h += "<li>"
    h += group.head_html
    if group.rest:
      h += "<ul>"
      for subord_html in group.rest_htmls:
        h += "<li>" + subord_html
      h += "</ul>"
  h += "</ul>"
  return h

def nice_unitted_num(n, sing, plur=None):
  if n==1: return "%d %s" % (n,sing)
  plur = plur or sing+"s"
  return "%d %s" % (n,plur)

def nice_timedelta(delt):
  x = []
  if delt.days > 0:
    x.append(nice_unitted_num(delt.days, "day"))
    #if delt.seconds > 60*60 and delt.days <= 1:
    #  x.append(nice_unitted_num(int(delt.seconds/60/60), "hour"))
  elif delt.seconds > 60*60:
    x.append(nice_unitted_num(int(delt.seconds/60/60), "hour"))
  elif delt.seconds > 60:
    x.append(nice_unitted_num(int(delt.seconds/60), "minute"))
  else:
    x.append(nice_unitted_num(delt.seconds, "second"))
  s = ', '.join(x)
  return s
  #return "%s back to %s" % (d2.strftime("%Y-%m-%dT%H:%M:%S"), d1.strftime("%Y-%m-%dT%H:%M:%S"))

# def single_query(q, topic_label, pages=1, rpp=20, exclude=()):
#   q_toks = bigrams.tokenize_and_clean(q, alignments=False)
#   q = '''%s "%s"''' % (q,topic_label)
#   sub_topic_ngram = tuple(bigrams.tokenize_and_clean(topic_label,True))
#   exclude = set(exclude)
#   tweets = search.cleaned_results(q, pages=pages, rpp=rpp, key_fn=search.user_and_text_identity)
#   tweets = list(tw for tw in tweets if tw['id'] not in exclude)
#   lc = linkedcorpus.LinkedCorpus()
#   lc.fill_from_tweet_iter(tweets)
#   groups_by_tweet_id = deduper.dedupe(lc)
#   groups = deduper.make_groups(tweets, groups_by_tweet_id)
#   for group in groups:
#     assert False, "broken"
#     group.head_html = nice_tweet(group.head, q_toks, sub_topic_ngram)
#     group.rest_htmls = [nice_tweet(t,q_toks,sub_topic_ngram) for t in group.rest]
#   yield topic_group_html(groups)


def the_app(environ, start_response):
  global_init()
  status = '200 OK'

  opts = Opts(environ,
      opt('q', default=''),
      opt('pages', default=2),
      opt('split', default=0),
      opt('simple', default=0),
      opt('max_topics', default=40),
      opt('ncol', default=3),
      opt('save', default=False),
      opt('load', default=False),
      opt('smoothing', default='lidstone'),
      opt('single_query', default=0),
      opt('format', default='dev'),
      )

  print "OPTIONS %s" % (opts,)

  response_headers = [('Content-type','text/html')]
  start_response(status, response_headers)

  if opts.single_query:
    # the requery
    opts2 = Opts(environ, opt('q',str), opt('topic_label',str), opt('exclude',default=''))
    opts2.exclude = [int(x) for x in opts2.exclude.split()]
    for x in single_query(**opts2):
      yield x
    return

  lc = linkedcorpus.LinkedCorpus()
  tweets_file = 'saved_tweets/save_%s_tweets' % opts.q
  tweet_iter = search.cleaned_results(opts.q, 
      pages = opts.pages, 
      key_fn = search.user_and_text_identity, 
      save = tweets_file if opts.save else None,
      load = tweets_file if opts.load else None
  )
  tweet_iter = deduper.merge_multitweets(tweet_iter)
  lc.fill_from_tweet_iter(tweet_iter)
  q_toks = bigrams.tokenize_and_clean(opts.q, True)
  res = ranking.extract_topics(lc, background_model, **opts)
  groups_by_tweet_id = deduper.dedupe(lc)
  for topic in res.topics:
    deduper.groupify_topic(topic, groups_by_tweet_id)
  ranking.late_topic_clean(res, max_topics=opts.max_topics)
  ranking.gather_leftover_tweets(res, lc)
  if res.topics and res.topics[-1].groups is None:
    deduper.groupify_topic(res.topics[-1], groups_by_tweet_id)  
  for topic in res.topics:
    topic.tweet_ids = util.myjoin([tw['id'] for tw in topic.tweets])
    for group in topic.groups:
      group.head_html = nice_tweet(group.head, q_toks, topic.label_ngrams)
      group.rest_htmls = [nice_tweet(t,q_toks,topic.label_ngrams) for t in group.rest]
  for topic in res.topics:
    topic.groups.sort(key=lambda g: g.head['created_at'], reverse=True)
  if lc.tweets_by_id:
    earliest = min(tw['created_at'] for tw in lc.tweets_by_id.itervalues())
    time_since_earliest = nice_timedelta(datetime.utcnow() - earliest)
  else:
    time_since_earliest = None
  
  if opts.format == 'pickle':
    # pickle.dumps(res) is 800k with dump/load = 100ms/60ms
    # trimmed json-like version is 150k with dump/load = 5ms/2ms.
    yield pickle.dumps(res)
    return
  if opts.format == 'json':
    topic_info = dict( (t.label,
       {
         'label': t.label,
         'nice_label': nice_label(t.label),
         'tweet_ids': t.tweet_ids,
         'groups': [{'head_html':g.head_html, 'rest_htmls':g.rest_htmls} for g in t.groups],
         'query_refinement': ranking.query_refinement(opts.q, t),
       })
        for t in res.topics)
    topic_list = [t.label for t in res.topics]
    results = {'topic_list':topic_list, 'topic_info': topic_info, 'time_since_earliest': time_since_earliest,}
    yield simplejson.dumps(results)
    return
  if opts.format != 'dev': raise Exception("bad format")
  
  for topic in res.topics:
    topic.tweets_html = topic_group_html(topic.groups)
  bigass_topic_dict = dict((t.label, dict(
    label= t.label, 
    tweets_html= t.tweets_html, 
    tweet_ids= t.tweet_ids,
  )) for t in res.topics)

  yield page_header()
  yield form_area(opts)  
  yield "<table><tr>"
  yield "<th>topics"
  if lc.tweets_by_id:
    earliest = min(tw['created_at'] for tw in lc.tweets_by_id.itervalues())
    #latest   = max(tw['created_at'] for tw in lc.tweets_by_id.itervalues())
    s=  "for %d tweets" % len(lc.tweets_by_id)
    s+= " over the last %s" % nice_timedelta(datetime.utcnow() - earliest)
    yield " <small>%s</small>" % s

  yield "<th>tweets"
  yield "<tr><td valign=top id=topic_list>"
  
  topic_labels = ['''<span class="topic_label" onclick="topic_click(this)" topic_label="%s"
  >%s</span><small>&nbsp;%d,&thinsp;%d</small><br>''' % (
    cgi.escape(topic.label), topic.label, topic.group_count, topic.tweet_count )
                  for topic in res.topics]
  for x in table_byrow(topic_labels, ncol=opts.ncol): yield x

  yield "<td valign=top>"
  yield "<div id=tweets>"
  yield "click on a topic on the left please"
  yield "</div>"
  yield "<div id=tweets_more>"
  yield "</div>"
  yield "</table>"
  yield "<script>"

  yield "topics = "
  yield simplejson.dumps(bigass_topic_dict)
  yield ";"
  yield "load_default_topic();"
  yield "</script>"

def app_stringify(iter):
  for x in iter:
    yield util.stringify(x, 'utf8', 'xmlcharrefreplace')

def global_init():
  global background_model
  background_model = lang_model.TokyoLM()

application = util.chaincompose(the_app, app_stringify)

if __name__=='__main__':
  import util; util.fix_stdio(shutup=False)
  from wsgiref.simple_server import make_server
  httpd = make_server('', 8080, application)
  print "Serving HTTP on port 8080..."
  httpd.serve_forever()
