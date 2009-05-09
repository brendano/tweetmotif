from __future__ import division
import twokenize,util,re,bigrams,deduper,common
import itertools
from copy import copy

#norm_re = re.compile(r'[^a-zA-Z0-9_@]')
norm_re = re.compile(r'^[^a-zA-Z0-9_@]+')
def tok_norm(tok):
  s = norm_re.subn('',tok)[0]
  if len(s)>=1: return s
  return tok

def rank_and_filter1(linkedcorpus, background_model, q, smoothing, n, **bla):
  q_toks = bigrams.tokenize_and_clean(q, alignments=False)
  q_toks = map(tok_norm, q_toks)
  q_toks_set = set(q_toks)
  stopwords = bigrams.stopwords - q_toks_set
  for ratio,ngram in linkedcorpus.model.compare_with_bg_model(background_model, n, min_count=3, smoothing_algorithm=smoothing):
    norm_ngram = [tok_norm(t) for t in ngram]
    if set(norm_ngram) <= q_toks_set:
      #print "reject query-subsumed", norm_ngram
      continue
    #if len(linkedcorpus.index[ngram]) <= 2: continue
    if len(norm_ngram)>1 and norm_ngram[-1] in stopwords: 
      #print "reject effective n-1gram", norm_ngram
      continue
    topic_label = " ".join(ngram)
    tweets = linkedcorpus.index[ngram]
    yield common.Topic(ngram=ngram, label=topic_label, tweets=tweets, ratio=ratio)

def n1g_in_ng(n_g, n_1_g, n, topic_dict_list):
  n_topics = topic_dict_list[n-1]
  n_1_topics = topic_dict_list[n-2]
  if n_1_g in n_1_topics and \
        test_weak_dominance(n_topics[n_g], n_1_topics[n_1_g]):
    #print "%dgram %s dominated by %dgram %s" % (n-1, n_1_g, n,n_g)
    del n_1_topics[n_1_g]

def rank_and_filter2(linkedcorpus, background_model, **opts):
  # topic deduping
  lc,bm=linkedcorpus,background_model
  unigram_topics = dict((t.ngram,t) for t in rank_and_filter1(lc,bm, n=1, **opts))
  bigram_topics  = dict((t.ngram,t) for t in rank_and_filter1(lc,bm, n=2, **opts))
  trigram_topics = dict((t.ngram,t) for t in rank_and_filter1(lc,bm, n=3, **opts))
  topics = [ unigram_topics, bigram_topics, trigram_topics ]
  for bg in bigram_topics:
    n1g_in_ng(bg, (bg[0],), 2, topics)
    n1g_in_ng(bg, (bg[1],), 2, topics)
    #bg_overlap_check(bg, 'left')
    #bg_overlap_check(bg, 'right')
  for tg in trigram_topics:
    n1g_in_ng(tg, (tg[0],tg[1]), 3, topics)
    n1g_in_ng(tg, (tg[1],tg[2]), 3, topics)
  return {'unigram':unigram_topics, 'bigram':bigram_topics, 'trigram':trigram_topics}

def score_topic(topic):
  return topic.ratio
  #a = 1 if len(topic.ngram)==1 else 1.5
  #return topic.ratio * a

def test_weak_dominance(topic1, topic2):
  def ids(topic): return (tw['id'] for tw in topic.tweets)
  return set(ids(topic1)) >= set(ids(topic2))

def extract_topics_from_ngram_topics(ngram_topics, linkedcorpus):
  # apply final topic ranking
  r = ngram_topics
  all_topics = r['unigram'].values() + r['bigram'].values() + r['trigram'].values()
  all_topics.sort(key=score_topic, reverse=True)
  return common.TopicResults(topics=all_topics, linkedcorpus=linkedcorpus)

def extract_topics(linkedcorpus, background_model, **opts):
  ngram_topics = rank_and_filter2(linkedcorpus, background_model, **opts)
  topic_res = extract_topics_from_ngram_topics(ngram_topics, linkedcorpus)
  return topic_res

def gather_leftover_tweets(topic_res, linkedcorpus):
  present_tweets = set(tw['id'] for topic in topic_res.topics for tw in topic.tweets)
  leftover_tweets = set(linkedcorpus.tweets_by_id) - present_tweets
  topic_res.leftover_tweets = [linkedcorpus.tweets_by_id[id] for id in leftover_tweets]
  if topic_res.leftover_tweets:
    new_topic = common.Topic(
      ngram=('**EXTRAS**',), label="<i>[other...]</i>",
      tweets=topic_res.leftover_tweets, ratio=-42)
    topic_res.topics.append(new_topic)

def late_topic_clean(topic_res, max_topics):
  assert topic_res.topics[0].groups
  res=topic_res
  print "nonsingleton count:", util.uniq_c(len(t.groups)>1 for t in res.topics)
  res.topics = [t for t in res.topics if len(t.groups)>1]
  #res.topics = deduper.dedupe_topics(res.topics)
  if max_topics < len(res.topics):
    print "truncating topics"
    topic_res.topics = topic_res.topics[:max_topics]

 
if __name__=='__main__':
  import simplejson
  import sys
  import linkedcorpus,search
  import util; util.fix_stdio()
  
  def prebaked_iter(filename):
    for line in util.counter(open(filename)):
      yield simplejson.loads(line)  

  # python ranking.py coachella data/coachella_500 | after RESULTS | tsv2fmt | head -40
  q = sys.argv[1]
  prebaked = sys.argv[2]

  lc = linkedcorpus.LinkedCorpus()
  tweets = prebaked_iter(prebaked)
  tweets = search.hard_dedupe_tweets(tweets)
  tweets=list(tweets)
  print "%d tweets" % len(tweets)
  tweets = list(search.group_multitweets(tweets))
  print "%d tweets after multigrouping" % len(tweets)
  print "MARK"
  lc.fill_from_tweet_iter(tweets)

  import lang_model, ansi
  background_model = lang_model.TokyoLM(readonly=True)

  res = rank_and_filter3(lc, background_model, q, smoothing='mle')
  print 'RESULTS'
  for topic in res.topics:
    #if len(topic.ngram)==3: print "%s\t%s\t%s" % (topic.label, topic.ratio, len(topic.tweets))
    print "%s\t%s\t%s" % (topic.label, topic.ratio, len(topic.tweets))
    #print ansi.color(topic.label,'bold','blue'), "(%s)" % len(topic.tweets)
    #for tweet in topic.tweets: print "",tweet['text']
  if res.leftover_tweets:
    print "%d leftover tweets" % len(res.leftover_tweets)


#################################################################
# Dangerous: was a closure in rank_and_filter2
#################################################################

def bg_overlap_check(bg, direction):
  if direction == 'left':
    wildcard = (None, bg[0])
  else:
    wildcard = (bg[1], None)
  if wildcard in linkedcorpus.bigram_index:
    for overlap_bg in linkedcorpus.bigram_index[wildcard]:
      if overlap_bg not in bigram_topics or not test_weak_dominance(bigram_topics[bg], bigram_topics[overlap_bg]):
        continue
      if direction == 'left':
        trigram = (overlap_bg[0], bg[0], bg[1])
      else:
        trigram = (bg[0], bg[1], overlap_bg[1])
      if trigram in trigram_topics:
        continue
      print "Adding trigram %s, %s, %s for dominated bigram %s, %s" % (trigram + overlap_bg)
      trigram_topic = copy(bigram_topics[overlap_bg])
      trigram_topic.ngram = trigram
      trigram_topic.label = ' '.join(trigram)
      trigram_topic.ratio = 10000 * (trigram_topic.ratio + 1)
      trigram_topics[trigram] = trigram_topic
