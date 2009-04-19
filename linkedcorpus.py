from collections import defaultdict
import twokenize
import bigrams
import lang_model

class LinkedCorpus:
  def __init__(self):
    self.model = lang_model.LocalLM()
    self.index = defaultdict(list)

  def add_tweet(self, tweet):
    toks = bigrams.tokenize_and_clean(tweet['text'])
    self.model.info['big_n'] += len(toks)
    for unigram in toks:
      self.model.add('unigram',unigram)
      self.index[unigram].append(tweet)
    for bigram in bigrams.bigrams(toks):
      self.model.add('bigram',bigram)
      self.index[bigram].append(tweet)


    
