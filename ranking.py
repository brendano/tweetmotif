import twokenize,util,re,bigrams
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
  for ratio,ngram in bigrams.compare_models(linkedcorpus.model, background_model,type,3):
    norm_ngram = [tok_norm(t) for t in ngram]
    #if set(norm_ngram) <= bigrams.stopwords:
    #  print "reject stopwords", norm_ngram
    #  continue
    #if len(norm_ngram)==1 and norm_ngram[0] in bigrams.stopwords_as_unigrams:
    #  print "reject unigram stopword", norm_ngram
    #  continue
    if set(norm_ngram) <= q_toks_set:
      print "reject query-subsumed", norm_ngram
      continue
    #if len(linkedcorpus.index[ngram]) <= 2: continue
    if len(norm_ngram)>1 and norm_ngram[-1] in stopwords: 
      print "reject effective n-1gram", norm_ngram
      continue
    topic_label = " ".join(ngram)
    tweets = linkedcorpus.index[ngram]
    yield util.Struct(ngram=ngram, label=topic_label, tweets=tweets, ratio=ratio)
    #yield ngram, topic_label, tweets

def rank_and_filter2(linkedcorpus, background_model, q):
  # topic deduping
  unigram_topics = dict((t.ngram,t) for t in rank_and_filter1(linkedcorpus, background_model, q, 'unigram'))
  bigram_topics  = dict((t.ngram,t) for t in rank_and_filter1(linkedcorpus, background_model, q, 'bigram'))
  trigram_topics = dict()
  def ug_in_bg_check(bg,ug):
    if ug in unigram_topics and test_weak_dominance(bigram_topics[bg], unigram_topics[ug]):
      print "killing %s since it's dominated by %s" % (ug, bg)
      del unigram_topics[ug]
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
  for bg in bigram_topics:
    ug_in_bg_check(bg, (bg[0],))
    ug_in_bg_check(bg, (bg[1],))
    bg_overlap_check(bg, 'left')
    bg_overlap_check(bg, 'right')
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
  return all_topics

def test_weak_dominance(topic1, topic2):
  def ids(topic): return (tw['id'] for tw in topic.tweets)
  return set(ids(topic1)) >= set(ids(topic2))

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
  tweets = search.dedupe_tweets(tweets, hash_fn=search.user_and_text_identity)
  lc.fill_from_tweet_iter(tweets)

  import lang_model, ansi
  background_model = lang_model.TokyoLM(readonly=True)
  #for topic_ngram, topic_label, tweets in rank_and_filter(lc, background_model, q, type='bigram'):
  #for topic in rank_and_filter2(lc, background_model, q, type='bigram'):

  res = rank_and_filter3(lc, background_model, q)
  print 'RESULTS'
  for topic in res:
    print "%s\t%s\t%s" % (topic.label, topic.ratio, len(topic.tweets))
    #print ansi.color(topic.label,'bold','blue'), "(%s)" % len(topic.tweets)
    #for tweet in topic.tweets: print "",tweet['text']


