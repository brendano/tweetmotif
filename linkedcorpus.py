import twokenize
from collections import defaultdict

def bigrams(tokens):
  return zip(['!START'] + tokens, tokens)

class LinkedCorpus:
  def __init__(self):
    self.model = { 
      "unigrams": defaultdict(int),
      "bigrams":  defaultdict(int),
      "big_n": 0
    }
    self.index = defaultdict(list)

  def add_tweet(self, tweet):
    s = tweet['text']

    unigram_counts = self.model['unigrams']
    bigram_counts = self.model['bigrams']
    toks = map(lambda tok: tok.lower(), twokenize.tokenize(s))
    self.model['big_n'] += len(toks)
    for unigram in toks:
      unigram_counts[unigram] += 1
      self.index[unigram].append(tweet)
    for bigram in bigrams(toks):
      bigram_counts[bigram] += 1
      self.index[bigram].append(tweet)


    
