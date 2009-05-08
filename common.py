# data structures that need to be shared with the frontend
import util

class TweetGroup:
  def __init__(self,**kwargs): self.__dict__.update(kwargs)

class TopicResults:
  def __init__(self, **kwargs):
    self.__dict__.update(kwargs)

class Topic:
  def __init__(self, **kwargs):
    self.groups = self.ngram = None
    self.__dict__.update(kwargs)
  @property
  def group_count(self):
    return len(self.group_ids)
  @property
  def tweet_count(self):
    return len(self.tweets)
    
