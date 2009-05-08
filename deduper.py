from __future__ import division
from pprint import pprint
import ansi,util
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
    tws.sort(key= lambda t: (len(t['text']), t['id']))
    tweet_groups.append( TweetGroup(
      head = tws[0],
      rest = tws[1:],
      tweets = tws,
      n = len(tws),
      group_id = g_id,
      tweet_ids = set(t['id'] for t in tws),
    ))
  tweet_groups.sort(key= lambda g: (g.n, g.tweet_ids))
  return tweet_groups


class TweetGroup:
  def __init__(self,**kwargs): self.__dict__.update(kwargs)


def do_pair_merges(tweets, linkedcorpus, pair_merges, seen_pairs,
                  sim_thresh=0.45, min_shared=2):
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


def dedupe_topics(topics):
  for i in range(len(topics)):
    for j in range(i+1, len(topics)):
      t1,t2 = topics[i],topics[j]
      #if t1.group_ids==t2.group_ids:
      #  print ansi.color("group-equivalent topics %s  %s" %(t1.ngram,t2.ngram),'blue')
      #  continue
      jacc = jaccard(t1.group_ids, t2.group_ids)
      if jacc > 0.3:
        s= "jacc %.2f = %2d/%2d,  loseleft %2d loseright %2d  %-20s  %-20s" % (
          jacc,
          len(t1.group_ids&t2.group_ids), len(t1.group_ids | t2.group_ids),
          len(t1.group_ids-t2.group_ids),
          len(t2.group_ids-t1.group_ids),
          t1.label, t2.label)
        if jaccard(t1.group_ids,t2.group_ids)>0.9:  s= ansi.color(s, 'blue')
        print s
  return topics



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


