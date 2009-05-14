from __future__ import division
from pprint import pprint
from copy import copy
import ansi,util,common
from collections import defaultdict

def merge_multitweets(tweet_iter, key_fn=lambda tw: tw['text'], preserve=('text','toks',)):
  index = defaultdict(list)
  for tweet in tweet_iter:
    index[key_fn(tweet)].append(tweet)
  multitweets = {}
  for key,tweets in index.iteritems():
    if len(tweets)==1: continue
    # merge into a multitweet
    multitweet = copy(tweets[0])
    orig_keys = multitweet.keys()
    multikeys = set(orig_keys) - set(preserve)
    for k in multikeys:
      del multitweet[k]
      multitweet['multi_' + k] = [tw[k] for tw in tweets]
    multitweet['orig_tweets'] = tweets
    multitweet['id'] = " ".join([str(tw['id']) for tw in tweets])
    multitweet['created_at'] = min(tw['created_at'] for tw in tweets)
    multitweet['multi'] = True
    multitweets[key] = (multitweet,)
    #print "multitweet", multitweet['id']
  index.update(multitweets)
  for k,tweets_singleton in index.iteritems():
    assert len(tweets_singleton)==1
    yield tweets_singleton[0]

def dedupe(linkedcorpus):
  " finds neardupes, returns TweetGroups. "
  lc = linkedcorpus
  # prefiltering optimization to cut down on total pairwise comparisons
  trigrams = [tg for tg in lc.model.ngrams_by_type[3] if len(lc.index[tg]) > 1]
  c_tg = [ (len(lc.index[tg]), tg) for tg in trigrams]
  c_tg.sort()

  pair_merges = defaultdict(set)
  seen_pairs = set()
  for count, tg in c_tg:
    #print count,tg
    #for tw in lc.index[tg]: print "  %s" % tw['text']
    do_pair_merges(lc.index[tg], linkedcorpus, pair_merges, seen_pairs)
  tweet_group_assignments = pairs_to_groups(pair_merges)
  
  singletons = set(lc.tweets_by_id) - set(tweet_group_assignments)
  first_n = len(set(tweet_group_assignments.itervalues()))
  for x,id in enumerate(singletons):
    tweet_group_assignments[id] = first_n + x
  return tweet_group_assignments

def make_groups(tweets, tweet_group_assignments):
  tgs = dict( (t['id'], tweet_group_assignments[t['id']]) for t in tweets)
  tweet_groups = {}
  tweets_by_group = defaultdict(list)
  for t in tweets:
    g = tweet_group_assignments[t['id']]
    tweets_by_group[g].append(t)
  tweet_groups = []
  for g_id, tws in tweets_by_group.iteritems():
#    tws.sort(key= lambda t: (len(t['text']), t['id']))
    tws.sort(key= lambda t: t['created_at'])
    tweet_groups.append( common.TweetGroup(
      head = tws[0],
      rest = tws[1:],
      tweets = tws,
      n = len(tws),
      group_id = g_id,
      tweet_ids = set(t['id'] for t in tws),
    ))
  tweet_groups.sort(key= lambda g: (g.n, g.tweet_ids))
  return tweet_groups

def groupify_topic(topic, groups_by_tweet_id):
  topic.groups = make_groups(topic.tweets, groups_by_tweet_id)
  if not topic.tweets:
    print "wtf?", topic.tweets
  topic.group_ids = set(g.group_id for g in topic.groups)


def do_pair_merges(tweets, linkedcorpus, pair_merges, seen_pairs,
                   sim_thresh=0.65, min_shared=2):
  for i in range(len(tweets)):
    for j in range(i+1, len(tweets)):
      t1,t2 = tweets[i], tweets[j]
      id1,id2 = t1['id'], t2['id']
      if (id1,id2) in seen_pairs: 
        #print ansi.color("ALREADY SEEN %s %s" % (id1,id2), 'green')
        continue
      sim = sim_scorer(t1, t2, min_shared=min_shared)
      yes = sim >= sim_thresh
      if yes:
        #print ansi.color("%.3f MERGE YES %s %s" % (sim, id1,id2), 'blue')
        pair_merges[id1].add(id2)
        pair_merges[id2].add(id1)
      else:
        #print ansi.color("%.3f MERGE NO  %s %s" % (sim, id1,id2), 'red')
        pass
      #print "\t%s\n\t%s" % (t1['text'], t2['text'])
      seen_pairs.add((id1,id2))

def sim_scorer(t1, t2, min_shared):
  set1 = t1['trigrams']
  set2 = t2['trigrams']
  if len(set1 & set2) < min_shared: return -1
  return dice(set1, set2)
  
def dice(x,y):
  return 2*len(x&y) / (len(x)+len(y))
def jaccard(x,y):
  return len(x&y) / len(x|y)

def pairs_to_groups(pair_merges):
  group_counter = -1
  group_assignments = {}
  unassigned_ids = set(pair_merges.keys())

  while unassigned_ids:        ## outer loop: create a new group; one per connected component
    group_counter += 1
    g = group_counter
    id = unassigned_ids.pop()   # pick any node to seed a new group
    unassigned_ids.add(id)
    totraverse = set([id])      # traversal order irrelevant
    while totraverse:          ## inner loop: traverse each node in this component
      id = totraverse.pop()
      group_assignments[id] = g
      unassigned_ids.remove(id)
      for id2 in pair_merges[id]:  
        if id2 in unassigned_ids:
          totraverse.add(id2)
  return group_assignments


####

def dedupe_topics(topics, lc):
  # Scoring is not touched
  new_topics = []
  already_merged_topics = set()
  for i in range(len(topics)):
    if i in already_merged_topics:
      continue
    new_topic = topics[i]
    for j in range(i+1, len(topics)):
      this_topic = topics[j]
      if merge_topics(new_topic, this_topic):
        new_topic.label_set.add(this_topic.ngram)
        new_topic.group_ids = new_topic.group_ids.intersection(this_topic.group_ids)
        already_merged_topics.add(j)
    # make new_topic.groups consistent with new_topic.group_ids
    new_topic.groups = [ group for group in new_topic.groups
                         if group.group_id in new_topic.group_ids ]
    # NB: not making new_topic.tweets consistent b/c that only affects EXTRAS
    # Fix label for new_topic
    if len(new_topic.label_set) > 1:
      new_topic._label_ngrams, new_topic.label = construct_multi_label(new_topic, lc.model)
      new_topic.ngram = None
    new_topics.append(new_topic)
  return new_topics

import kmp
import __builtin__
import itertools
def construct_multi_label(topic, lang_model):
  arbitrary_tweet = topic.groups[0].head
  tokens = arbitrary_tweet['toks']
  ranges = []
  for label in topic.label_set:
    index = kmp.indexSubsequence(label, tokens)
    #print "%s in %s at %s" % (label, tokens, index)
    if index > -1:
      ranges.append(__builtin__.range(index, index + len(label)))
  indices = set()
  for range in ranges:
    indices.update(range)
  indices = list(indices)
  indices.sort()
  labels = []
  last_index = indices[0] - 1
  for index in indices:
    if index != last_index + 1:
      labels.append(None)
    labels.append(tokens[index])
    last_index = index
  labels = [ tuple(g) for k, g
             in itertools.groupby(labels, lambda it: it is not None)
             if k ]

  multi_label = choose_multi_label(labels, lang_model)
  if isinstance(multi_label[0], list):
    multi_label = tuple(tuple(x) for x in multi_label)

  # if len(labels) > 1:
  #   print "LABELS ",labels
  #   print "MULTI", multi_label

  return multi_label, " / ".join([ " ".join(label) for label in multi_label])

import bigrams
import math
def choose_multi_label(labels, lang_model):
  longest = util.argmax(labels, scorer=lambda ngram: len(ngram))
  if len(longest) > 3:
    best = util.argmax(bigrams.trigrams(longest), lambda ng: lang_model.lidstone(ng))
    best = (best,)
  elif len(longest) == 3:
    best = longest
    best = (best,)
  elif len(longest) <= 2:
    # this is kinda shitty set of them .. would rather want all possible skip n-grams (O(N^2) of them?)
    z = [(tuple(x),) for x in labels] + bigrams.bigrams(labels) + bigrams.trigrams(labels)
    assert z
    z = [x for x in z if len(util.flatten(x)) <= 3]
    # sum is too weird
    # lexicographic ordering of the top-ranked sublabels in the multilabel
    def scorer(ngrams):
      scores = [lang_model.lidstone(ng) for ng in ngrams]
      if len(scores) < 3:
        scores += [0]*(3 - len(scores))
      scores.sort(reverse=True)
      # print "SCORE %-30s %s" % (scores, ngrams)
      return scores
    z.sort(key= scorer, reverse=True)
    # print "RANKING",z
    best = z[0]
  else:
    assert False
  return best
  

def intersection(tweets1, tweets2, lc):
  tweet1_ids = set([ tweet['id'] for tweet in tweets1 ])
  tweet2_ids = set([ tweet['id'] for tweet in tweets2 ])
  intersection_ids = tweet1_ids.intersection(tweet2_ids)
  return [ lc.tweets_by_id[id] for id in intersection_ids ]

def merge_topics(topic1, topic2, use_jaccard=True):
  if use_jaccard:
    jacc = jaccard(topic1.group_ids, topic2.group_ids)
    merge = jacc > 0.9
    # if jacc > 0.3:
    #   s= "jacc %.2f = %2d/%2d,  loseleft %2d loseright %2d  %-20s  %-20s" % (
    #     jacc,
    #     len(topic1.group_ids&topic2.group_ids),
    #     len(topic1.group_ids | topic2.group_ids),
    #     len(topic1.group_ids-topic2.group_ids),
    #     len(topic2.group_ids-topic1.group_ids),
    #     topic1.label, topic2.label)
    #   if merge:
    #     s = ansi.color(s, 'blue')
    #   print s
  else:
    merge = topic1.group_ids==topic2.group_ids
    if merge:
      print ansi.color("group-equivalent topics %s  %s" %(topic1.ngram,topic2.ngram),'blue')
  # if not merge and len(set(topic1.ngram) & set(topic2.ngram)) >= 2:
  #   print "wtf no merge? %-20s %-20s" % (topic1.ngram, topic2.ngram)
  return merge

####

# pure reporting below.  dont use.

def topic_xp(topic, lc):
  pairs = {}
  for i in range(len(topic.tweets)):
    for j in range(i+1, len(topic.tweets)):
      t1 = topic.tweets[i]
      t2 = topic.tweets[j]
      set1 = t1['bigrams'] | t1['unigrams']
      set2 = t2['bigrams'] | t2['unigrams']
      pairs[t1['id'],t2['id']] = (set1,set2)
  items = pairs.items()
  items.sort(key= lambda (ids,(x,y)): -dice(x,y))
  import ansi
  for (id1,id2),(x,y) in items:
    nums = "%.3f" % dice(x,y)
    t1,t2 = lc.tweets_by_id[id1], lc.tweets_by_id[id2]
    f = twokenize.squeeze_whitespace
    s1,s2 = ["%s %s" % (ansi.color(t['from_user'],'green') + " "*(15-len(t['from_user'])), f(t['text'])) for t in [t1,t2]]
    print "%-8s %s\n%-8s %s" % (nums, s1, " ", s2)

def topic_pair_report(res,lc):
  import ansi
  for topic in res.topics:
    print
    print ansi.color("*** Topic: ",'blue'), ansi.color(repr(topic.ngram),'bold')
    if len(topic.tweets)>100:
      print "skipping"
    else:
      topic_xp(topic,lc)


