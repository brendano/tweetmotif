# data structures that need to be shared with the frontend
import util

class TweetGroup:
  def __init__(self,**kwargs): self.__dict__.update(kwargs)

class TopicResults:
  def __init__(self, **kwargs):
    self.__dict__.update(kwargs)
