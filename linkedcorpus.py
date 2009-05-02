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
      self.model.add('unigram',unigram)
      self.index[unigram].append(tweet)

    the_bigrams = set(bigrams.filtered_bigrams(toks))
    tweet['bigrams'] = the_bigrams
    for bigram in the_bigrams:
      self.model.add('bigram',bigram)
      self.index[bigram].append(tweet)
      self.bigram_index[bigram[0], None].append(bigram)
      self.bigram_index[None, bigram[1]].append(bigram)
    for trigram in set(bigrams.filtered_trigrams(toks)):
      self.model.add('trigram',trigram)
      self.index[trigram].append(tweet)
    #self.tweets_by_text.append(tweet)
    #for ngram in set(bigrams.multi_ngrams(toks, n_and_up=3)):
    #  pass

  def fill_from_tweet_iter(self, tweet_iter):
    for tweet in tweet_iter:
      self.add_tweet(tweet)

#if __name__=='__main__':
#  import cPickle as pickle
#  lc = LinkedCorpus()
#  for tweet in pickle.load(open(sys.argv[1])):
#    bigrams.analyze_tweet(tweet)
#    lc.add_tweet(tweet)

#import bigrams,linkedcorpus
#import cPickle as pickle
#def go():
#  lc = linkedcorpus.LinkedCorpus()
#  for tweet in pickle.load(open("save_the_tweets")):
#    bigrams.analyze_tweet(tweet)
#    lc.add_tweet(tweet)
#
