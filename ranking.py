from __future__ import division
import twokenize,util,re,bigrams
import itertools
from copy import copy

#norm_re = re.compile(r'[^a-zA-Z0-9_@]')
norm_re = re.compile(r'^[^a-zA-Z0-9_@]+')
def tok_norm(tok):
  s = norm_re.subn('',tok)[0]
  if len(s)>=1: return s
  return tok

def rank_and_filter1(linkedcorpus, background_model, q, type='bigram'):
  # topic extraction
  #q_toks = [tok_norm(t) for t in twokenize.tokenize(q)]
  q_toks = bigrams.tokenize_and_clean(q, alignments=False)
  q_toks = map(tok_norm, q_toks)
  q_toks_set = set(q_toks)
  stopwords = bigrams.stopwords - q_toks_set
  for ratio,ngram in bigrams.compare_models(linkedcorpus.model, background_model,type, min_count=3):
    norm_ngram = [tok_norm(t) for t in ngram]
    #if set(norm_ngram) <= bigrams.stopwords:
    #  print "reject stopwords", norm_ngram
    #  continue
    #if len(norm_ngram)==1 and norm_ngram[0] in bigrams.stopwords_as_unigrams:
    #  print "reject unigram stopword", norm_ngram
    #  continue
    if set(norm_ngram) <= q_toks_set:
      #print "reject query-subsumed", norm_ngram
      continue
    #if len(linkedcorpus.index[ngram]) <= 2: continue
    if len(norm_ngram)>1 and norm_ngram[-1] in stopwords: 
      #print "reject effective n-1gram", norm_ngram
      continue
    topic_label = " ".join(ngram)
    tweets = linkedcorpus.index[ngram]
    yield util.Struct(ngram=ngram, label=topic_label, tweets=tweets, ratio=ratio)
    #yield ngram, topic_label, tweets

def n_1_g_in_n_g_check(n_g, n_1_g, n, topic_dict_list):
  n_topics = topic_dict_list[n-1]
  n_1_topics = topic_dict_list[n-2]
  if n_1_g in n_1_topics and \
        test_weak_dominance(n_topics[n_g], n_1_topics[n_1_g]):
    #print "%dgram %s dominated by %dgram %s" % (n-1, n_1_g, n,n_g)
    del n_1_topics[n_1_g]

def rank_and_filter2(linkedcorpus, background_model, q):
  # topic deduping
  unigram_topics = dict((t.ngram,t) for t in rank_and_filter1(linkedcorpus, background_model, q, 'unigram'))
  bigram_topics  = dict((t.ngram,t) for t in rank_and_filter1(linkedcorpus, background_model, q, 'bigram'))
  trigram_topics  = dict((t.ngram,t) for t in rank_and_filter1(linkedcorpus, background_model, q, 'trigram'))
  topics = [ unigram_topics, bigram_topics, trigram_topics ]
  #print trigram_topics
  #print "STOP"
  #trigram_topics = dict()
  for bg in bigram_topics:
    n_1_g_in_n_g_check(bg, (bg[0],), 2, topics)
    n_1_g_in_n_g_check(bg, (bg[1],), 2, topics)
    #bg_overlap_check(bg, 'left')
    #bg_overlap_check(bg, 'right')
  for tg in trigram_topics:
    n_1_g_in_n_g_check(tg, (tg[0],tg[1]), 3, topics)
    n_1_g_in_n_g_check(tg, (tg[1],tg[2]), 3, topics)
  return {'unigram':unigram_topics, 'bigram':bigram_topics, 'trigram':trigram_topics}

def score_topic(topic):
  return topic.ratio
  #a = 1 if len(topic.ngram)==1 else 1.5
  #return topic.ratio * a

def rank_and_filter3(linkedcorpus, background_model, q):
  # apply final topic ranking
  r = rank_and_filter2(linkedcorpus, background_model, q)
  all_topics = r['unigram'].values() + r['bigram'].values() + r['trigram'].values()
  all_topics.sort(key=score_topic, reverse=True)
  tweet_ids_in_topics = set()
  for t in all_topics:
    tweet_ids_in_topics |= set(tw['id'] for tw in t.tweets)
  leftover_ids = set(linkedcorpus.tweets_by_id.iterkeys()) - tweet_ids_in_topics
  leftover_tweets = [linkedcorpus.tweets_by_id[id] for id in leftover_ids]
  return Topics(topics=all_topics, leftover_tweets=leftover_tweets, linkedcorpus=linkedcorpus)
  #return all_topics

def test_weak_dominance(topic1, topic2):
  def ids(topic): return (tw['id'] for tw in topic.tweets)
  return set(ids(topic1)) >= set(ids(topic2))

class Topics:
  def __init__(self, **kwargs):
    self.__dict__.update(kwargs)
  def cutoff_topics(self, num_left):
    self.topics = self.topics[:num_left]
    tweets_left = set(itertools.chain(*( ((tw['id'] for tw in topic['tweets']) for topic in self.topics) )))
    new_leftover_ids = set(self.linkedcorpus.tweets_by_id) - tweets_left - set(tw['id'] for tw in self.leftover_tweets)
    self.leftover_tweets += (self.linkedcorpus.tweets_by_id[i] for i in new_leftover_ids)

def rank_and_filter4(lc, background_model, q, max_topics):
  # topic pruning
  assert max_topics
  res = rank_and_filter3(lc, background_model, q)
  if len(res.topics) > max_topics:
    print "throwing out %d topics" % (len(res.topics) - max_topics)
    res.cutoff_topics(max_topics)
  if res.leftover_tweets:
    res.topics.append(util.Struct(ngram=('**EXTRAS**',),label="<i>[other...]</i>",tweets=res.leftover_tweets,ratio=-42))
  return res

def topic_xp(topic, lc):
  pairs = {}
  for i in range(len(topic.tweets)):
    for j in range(i+1, len(topic.tweets)):
      t1 = topic.tweets[i]
      t2 = topic.tweets[j]
      set1 = t1['bigrams'] | t1['unigrams']
      set2 = t2['bigrams'] | t2['unigrams']
      #x = len(t1['bigrams'] & t2['bigrams']) + len(t1['unigrams'] & t2['unigrams'])
      #y = len(t1['bigrams'] | t2['bigrams']) + len(t1['unigrams'] | t2['unigrams'])
      pairs[t1['id'],t2['id']] = (set1,set2)
  items = pairs.items()
  scorer = lambda x,y: len(x&y) / len(x|y)   # jaccard
  scorer = lambda x,y: 2*len(x&y) / (len(x)+len(y))  # dice
  items.sort(key= lambda (ids,(x,y)): -scorer(x,y))
  import ansi
  for (id1,id2),(x,y) in items:
    nums = "%.3f" % scorer(x,y)
    t1,t2 = lc.tweets_by_id[id1], lc.tweets_by_id[id2]
    f = twokenize.squeeze_whitespace
    s1,s2 = ["%s %s" % (ansi.color(t['from_user'],'green') + " "*(15-len(t['from_user'])), f(t['text'])) for t in [t1,t2]]
    print "%-8s %s\n%-8s %s" % (nums, s1, " ", s2)
    #pairs[t1['id'],t2['id']] = 

def topic_pair_report(res,lc):
  import ansi
  for topic in res.topics:
    print
    print ansi.color("*** Topic: ",'blue'), ansi.color(repr(topic.ngram),'bold')
    if len(topic.tweets)>100:
      print "skipping"
    else:
      topic_xp(topic,lc)


def prebaked_iter(filename):
  for line in util.counter(open(filename)):
    yield simplejson.loads(line)

if __name__=='__main__':
  import simplejson
  import sys
  import linkedcorpus,search
  import util; util.fix_stdio()

  # python ranking.py coachella data/coachella_500 | after RESULTS | tsv2fmt | head -40
  q = sys.argv[1]
  prebaked = sys.argv[2]

  lc = linkedcorpus.LinkedCorpus()
  tweets = prebaked_iter(prebaked)
  tweets = search.dedupe_tweets(tweets, key_fn=search.user_and_text_identity)
  tweets=list(tweets)
  print "%d tweets" % len(tweets)
  tweets = list(search.group_multitweets(tweets))
  print "%d tweets after multigrouping" % len(tweets)
  print "MARK"
  lc.fill_from_tweet_iter(tweets)

  import lang_model, ansi
  background_model = lang_model.TokyoLM(readonly=True)
  #for topic_ngram, topic_label, tweets in rank_and_filter(lc, background_model, q, type='bigram'):
  #for topic in rank_and_filter2(lc, background_model, q, type='bigram'):

  res = rank_and_filter3(lc, background_model, q)
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
