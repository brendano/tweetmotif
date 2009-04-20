import twokenize,util,re,bigrams


#norm_re = re.compile(r'[^a-zA-Z0-9_@]')
norm_re = re.compile(r'^[^a-zA-Z0-9_@]+')
def tok_norm(tok):
  s = norm_re.subn('',tok)[0]
  if len(s)>=1: return s
  return tok

def rank_and_filter(linkedcorpus, background_model, q, type='bigram'):
  print twokenize.tokenize(q)
  q_toks = [tok_norm(t) for t in twokenize.tokenize(q)]
  q_toks_set = set(q_toks)
  stopwords = bigrams.stopwords - q_toks_set
  for ratio,ngram in bigrams.compare_models(linkedcorpus.model, background_model,type,2):
    if type=='unigram':
      ngram=(ngram,)
    norm_ngram = [tok_norm(t) for t in ngram]
    if (set(norm_ngram) - q_toks_set) <= stopwords: continue
    #if len(linkedcorpus.index[ngram]) <= 2: continue
    if set(norm_ngram) <= stopwords: continue
    if len(norm_ngram)>1 and norm_ngram[-1] in stopwords: 
      # may as well be an n-1 gram
      continue
    topic_label = ngram if isinstance(ngram,str) else " ".join(ngram)
    tweets = linkedcorpus.index[ngram[0]] if len(ngram)==1 else linkedcorpus.index[ngram]
    ngram = (ngram,) if isinstance(ngram,str) else ngram
    yield ngram, topic_label, tweets


def prebaked_iter(filename):
  for line in util.counter(fileinput.input(filename)):
    yield simplejson.loads(line)

if __name__=='__main__':
  import fileinput
  import simplejson
  import sys, linkedcorpus
  import codecs; sys.stdout = codecs.open('/dev/stdout','w',encoding='utf8',buffering=0)

  q = sys.argv[1]         # coachella
  prebaked = sys.argv[2]  # data/c500

  lc = linkedcorpus.LinkedCorpus()
  for tweet in prebaked_iter(prebaked):
    lc.add_tweet(tweet)

  import lang_model, ansi
  background_model = lang_model.MemcacheLM()
  for topic, tweets in rank_and_filter(lc, background_model, q):
    print ansi.color(topic,'bold','blue'), "(%s)" % len(tweets)
    for tweet in tweets: print "",tweet['text']



