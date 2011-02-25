# data structures that need to be shared with the frontend
# actually the theory behind this isnt working - pickle.loads drags in other modules anyways.
# maybe this is now a "datastructures" file.
import util

class TweetGroup:
  def __init__(self,**kwargs):
    self.__dict__.update(kwargs)

class TopicResults:
  def __init__(self, **kwargs):
    self.__dict__.update(kwargs)

class Topic:
  def __init__(self, **kwargs):
    self.groups = self.ngram = self._label_ngrams = None
    self.__dict__.update(kwargs)
    assert self.ngram
    self.label_set = set([self.ngram])

  @property
  def label_ngrams(self):
    assert self._label_ngrams or self.ngram
    return self._label_ngrams or (self.ngram,)

  @property
  def group_count(self):
    return len(self.group_ids)

  @property
  def tweet_count(self):
    return len(self.tweets)
