import sys
from collections import defaultdict
import twokenize
import bigrams
import lang_model

class LinkedCorpus:
  def __init__(self):
    self.model = lang_model.LocalLM()
    self.index = defaultdict(list)
    self.bigram_index = defaultdict(list)

  def add_tweet(self, tweet):
    toks = tweet['toks']
    self.model.info['big_n'] += len(toks)
    for unigram in set(bigrams.filtered_unigrams(toks)):
      self.model.add('unigram',unigram)
      self.index[unigram].append(tweet)
    for bigram in set(bigrams.filtered_bigrams(toks)):
      self.model.add('bigram',bigram)
      self.index[bigram].append(tweet)
      self.bigram_index[bigram[0], None].append(bigram)
      self.bigram_index[None, bigram[1]].append(bigram)
    for trigram in set(bigrams.filtered_trigrams(toks)):
      self.model.add('trigram',trigram)
      self.index[trigram].append(tweet)
    #for ngram in set(bigrams.multi_ngrams(toks, n_and_up=3)):
    #  pass

  def fill_from_tweet_iter(self, tweet_iter, hash_fn=None):
    for tweet in tweet_iter:
      self.add_tweet(tweet)

