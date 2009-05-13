#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

# Histogram of unigrams and bigrams in a stream of tweets
#
# What we actually want is difference from background collection

from __future__ import division
import sys
import re
import fileinput
import cPickle as pickle
from collections import defaultdict
import twokenize
import lang_model
import util

import tchelpers
tok_cache = tchelpers.IntKeyWrapper(tchelpers.open_tc("toks.tch"))

def analyze_tweet(tweet):
  tweet['toks'] = tokenize_and_clean(tweet['text'], alignments=True); return   # turn off caching
  if tweet['id'] in tok_cache:
    #print "CACHE HIT    %s" % tweet['text']
    toks = pickle.loads(tok_cache[tweet['id']])
  else:
    #print "NEW ANALYSIS %s" % tweet['text']
    toks = tokenize_and_clean(tweet['text'], alignments=True)
    tok_cache[tweet['id']] = pickle.dumps(toks)
  tweet['toks'] = toks

from twokenize import regex_or
mycompile = lambda pat:  re.compile(pat,  re.UNICODE)
# junk tokens are a more aggressive cleaning assumption than usual.
JunkTok = mycompile(r'''^[^a-zA-Z0-9_@]+$''')
# dont make n-grams across phrase boundary markers.
PhraseBoundaryTok = regex_or(r'''[.,“"'?!:;|-]+''', twokenize.Entity)
PhraseBoundaryTok = mycompile('^'+PhraseBoundaryTok+'$')
EdgePunctTok = mycompile('^' + twokenize.EdgePunct + '+$')

def tokenize_and_clean(msg, alignments):
  if alignments: 
    toks = twokenize.tokenize(msg)
  else:          
    toks = twokenize.simple_tokenize(msg)
  for i in range(len(toks)):
    toks[i] = toks[i].lower()
  inds = range(len(toks))
  #if len(inds) < len(toks): print "dropping junk", sorted(list(toks[i] for i in (set(range(len(toks)))-set(inds))))
  if alignments: 
    return toks.subset(inds)
  else:
    return [toks[i] for i in inds]

def unigrams(tokens):
  return [(tok,) for tok in tokens]

def bigrams(tokens):
  return ngrams(tokens,2)

def trigrams(tokens):
  return ngrams(tokens,3)

def ngrams(tokens, n):
  return [tuple(tokens[i:(i+n)]) for i in range(len(tokens) - (n-1))]

read_set = lambda f: set(open(f).read().split())
stopwords                  = read_set("stopwords_dir/normal_stopwords")
stopwords_only_as_unigrams = read_set("stopwords_dir/only_as_unigrams")
super_stopwords            = read_set("stopwords_dir/super_stopwords")
rightside_stopwords        = read_set("stopwords_dir/rightside_stopwords")
leftside_stopwords         = read_set("stopwords_dir/leftside_stopwords")

def unigram_stopword_filter(unigrams):
  ret = [ug for ug in unigrams
   if  ug[0] not in super_stopwords and
       ug[0] not in stopwords and
       ug[0] not in stopwords_only_as_unigrams and
       ug[0] not in leftside_stopwords and
       ug[0] not in rightside_stopwords and
       not PhraseBoundaryTok.search(ug[0])  and
       not EdgePunctTok.search(ug[0])
  ]
  #if set(unigrams) - set(ret):
  #  print "dropping unigram stopwords", " ".join(sorted(x[0] for x in (set(unigrams) - set(ret))))
  return ret

def bigram_stopword_filter(bigrams):
  ret = [ng for ng in bigrams
    if  ng[0] not in super_stopwords and
        not EdgePunctTok.search(ng[0]) and
        ng[-1] not in super_stopwords and
        not EdgePunctTok.search(ng[1]) and
        not any(PhraseBoundaryTok.search(tok) for tok in ng) and
        not any(JunkTok.search(tok) for tok in ng)
  ]
  #for reject in set(ngrams) - set(ret):
  #  print "dropping stopword-implicated", reject
  return ret

def ngram_stopword_filter(ngrams):
  ret = [ng for ng in ngrams
    if  ng[0] not in super_stopwords and
        ng[0] not in leftside_stopwords and 
        ng[-1] not in super_stopwords and
        ng[-1] not in rightside_stopwords and
        not (JunkTok.search(ng[0]) or JunkTok.search(ng[-1])) and
        not any(PhraseBoundaryTok.search(tok) for tok in ng)
  ]
  #for reject in set(ngrams) - set(ret):
  #  print "dropping stopword-implicated", reject
  return ret

def kill_hashtags(ngrams):
  # for n>1-grams
  return (ng for ng in ngrams if all(not tok.startswith('#') for tok in ng))

cc = util.chaincompose
filtered_unigrams  = cc(unigrams, unigram_stopword_filter)
filtered_bigrams   = cc(bigrams,  bigram_stopword_filter, kill_hashtags)
filtered_trigrams  = cc(trigrams, ngram_stopword_filter, kill_hashtags)


def output_ngram_counts(ngram_counts, min_count=1):
  join_flag = False
  if type(ngram_counts.keys()[0]) == tuple:
    join_flag = True
  histogram_bucket = min_count/2
  ngrams_and_counts = ngram_counts.items()
  ngrams_and_counts.sort(key=lambda x: x[0])
  for ngram, count in ngrams_and_counts:
    if count >= min_count:
      if join_flag:
        ngram = ' '.join(ngram)
      print "%s\t%s" % ("*" * (count/histogram_bucket), ngram)

def collect_statistics_into_model(text_iter, lang_model):
  for line in util.counter( text_iter ):
    toks = tokenize_and_clean(line, alignments=False)
    lang_model.info['big_n'] += len(toks)
    for unigram in filtered_unigrams(toks):
      lang_model.add(unigram)
    for bigram in filtered_bigrams(toks):
      lang_model.add(bigram)
    for trigram in filtered_trigrams(toks):
      lang_model.add(trigram)


if __name__=='__main__':
  import util; util.fix_stdio()

  background_model = lang_model.TokyoLM()
  collection_model = lang_model.LocalLM()
  collect_statistics_into_model(open(sys.argv[1]), collection_model)
