import sys
from collections import defaultdict
import twokenize
import bigrams
import lang_model

class LinkedCorpus:
  " Hold tweets & indexes .. that is, ngrams are 'linked' to their tweets. "
  def __init__(self):
    self.model = lang_model.LocalLM()
    self.index = defaultdict(list)
    self.bigram_index = defaultdict(list)
    self.tweets_by_id = {}

  def add_tweet(self, tweet):
    self.tweets_by_id[tweet['id']] = tweet
    toks = tweet['toks']
    self.model.info['big_n'] += len(toks)

    the_unigrams = set(bigrams.filtered_unigrams(toks))
    tweet['unigrams'] = the_unigrams
    for unigram in the_unigrams:
      self.model.add(unigram)
      self.index[unigram].append(tweet)

    the_bigrams = set(bigrams.filtered_bigrams(toks))
    tweet['bigrams'] = the_bigrams
    for bigram in the_bigrams:
      self.model.add(bigram)
      self.index[bigram].append(tweet)
      self.bigram_index[bigram[0], None].append(bigram)
      self.bigram_index[None, bigram[1]].append(bigram)

    tweet['trigrams'] = set(bigrams.filtered_trigrams(toks))
    for trigram in tweet['trigrams']:
      self.model.add(trigram)
      self.index[trigram].append(tweet)
    #self.tweets_by_text.append(tweet)
    #for ngram in set(bigrams.multi_ngrams(toks, n_and_up=3)):
    #  pass

  def fill_from_tweet_iter(self, tweet_iter):
    for tweet in tweet_iter:
      self.add_tweet(tweet)

if __name__=='__main__':
  import cPickle as pickle
  import search
  q = sys.argv[1]
  smoothing = sys.argv[2]
  bg_model = lang_model.TokyoLM(readonly=True)
  lc = LinkedCorpus()
  tweet_iter = search.cleaned_results(q,
      pages = 2, 
      key_fn = search.user_and_text_identity, 
      save = None,
      load = None
      )
  lc.fill_from_tweet_iter(tweet_iter)
  for ratio, ngram in lc.model.compare_with_bg_model(bg_model, 3, min_count=3, smoothing_algorithm=smoothing):
    print "%s\t%s" % ('_'.join(ngram), ratio)
