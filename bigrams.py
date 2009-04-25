#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

# Histogram of unigrams and bigrams in a stream of tweets
#
# What we actually want is difference from background collection

from __future__ import division
import sys
import re
import fileinput
from collections import defaultdict
import twokenize
import lang_model
import util

def analyze_tweet(tweet):
  toks = tokenize_and_clean(tweet['text'], alignments=True)
  tweet['toks'] = toks

mycompile = lambda pat:  re.compile(pat,  re.UNICODE)
# junk tokens contribute no information and can be ignored
#JunkTok = mycompile(r'''^[^a-zA-Z0-9_@]+$''')
JunkTok = mycompile(r'''^$''')
# dont make n-grams across phrase boundary markers.
PhraseBoundaryTok = r'''[.,“"'?!:;-]+ | %s '''  % twokenize.Entity
PhraseBoundaryTok = re.compile('^('+PhraseBoundaryTok+')$', re.U|re.X)

def tokenize_and_clean(msg, alignments):
  if alignments: 
    toks = twokenize.tokenize(msg)
  else:          
    toks = twokenize.simple_tokenize(msg)
  for i in range(len(toks)):
    toks[i] = toks[i].lower()
  inds = [i for i in range(len(toks)) if not JunkTok.search(toks[i])]
  #if len(inds) < len(toks): print "dropping junk", sorted(list(toks[i] for i in (set(range(len(toks)))-set(inds))))
  if alignments: 
    return toks.subset(inds)
  else:
    return [toks[i] for i in inds]

def unigrams(tokens):
  return [(tok,) for tok in tokens]

def bigrams(tokens):
  return ngrams(tokens,2)

def multi_ngrams(tokens, n_and_up):
  ret = []
  for k in range(n_and_up, len(tokens)):
    ret += ngrams(tokens, k)
  return ret

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
    if ug[0] not in super_stopwords and
      ug[0] not in stopwords_only_as_unigrams and
      ug[0] not in stopwords and
      not PhraseBoundaryTok.search(ug[0]) 
  ]
  #if set(unigrams) - set(ret):
  #  print "dropping unigram stopwords", " ".join(sorted(x[0] for x in (set(unigrams) - set(ret))))
  return ret

def ngram_stopword_filter(ngrams):
  ret = [ng for ng in ngrams
    if ng[0] not in super_stopwords and
      ng[0] not in leftside_stopwords and 
      ng[-1] not in super_stopwords and
      ng[-1] not in rightside_stopwords and
      not PhraseBoundaryTok.search(ng[0]) and
      not PhraseBoundaryTok.search(ng[-1]) and
      not any(PhraseBoundaryTok.search(inner_tok) for inner_tok in ng[1:-1])
  ]
  #for reject in set(ngrams) - set(ret):
  #  print "dropping stopword-implicated", reject
  return ret

filtered_unigrams = util.chaincompose(unigrams, unigram_stopword_filter)
filtered_bigrams  = util.chaincompose(bigrams, ngram_stopword_filter)
filtered_multi_ngrams  = util.chaincompose(multi_ngrams, ngram_stopword_filter)


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
      lang_model.add('unigram', unigram)
    for bigram in filtered_bigrams(toks):
      lang_model.add('bigram', bigram)


def compare_models(collection_model, background_model, ngram_type, min_count=1):
  bkgnd_ngram_counts = background_model.counts[ngram_type]
  bkgnd_N = background_model.info["big_n"]
  coll_ngram_counts = collection_model.counts[ngram_type]
  coll_N = collection_model.info["big_n"]
  coll_ngrams_and_counts = coll_ngram_counts.items()

  coll_ngrams_and_mle_probs = map(lambda (b,c): (b, c/coll_N), coll_ngrams_and_counts)
  coll_ngrams_and_mle_prob_ratio = map(lambda (b,p): (b, compute_ratio(p, bkgnd_ngram_counts[b]/bkgnd_N)), coll_ngrams_and_counts)
  #coll_ngrams_and_mle_prob_ratio = map(lambda (b,p): (b, pseudocounted_ratio(p, bkgnd_ngram_counts[b]/bkgnd_N)), coll_ngrams_and_counts)  # pseudocount smoothing is crappy because causes ties.  how about good-turing or kneser-ney?
  coll_ngrams_and_mle_prob_ratio.sort(key=lambda pair: pair[1], reverse=True)
  for ngram, ratio in coll_ngrams_and_mle_prob_ratio:
    if coll_ngram_counts[ngram] < min_count:
      continue
    yield ratio,ngram

  #ngrams = [ngram for ngram,count in coll_ngrams_and_counts]
  #counts = [count for ngram,count in coll_ngrams_and_counts]
  #mle_probs = [c/coll_N for c in counts]
  #mle_prob_ratio = [compute_ratio(mle_probs[i], bkgnd_ngram_counts[ngrams[i]]) for i in range(len(ngrams))]
  #inds = range(len(ngrams))
  #inds.sort(key=lambda i: mle_prob_ratio[i], reverse=True)
  #for i in inds:
  #  if counts[i] < min_count: continue
  #  yield mle_prob_ratio[i], ngrams[i]


def compute_ratio(num, denom):
  if denom == 0:
    return 0
  else:
    return num/denom

def pseudocounted_ratio(num,denom, a=0.1):
  return (num+a) / (denom+a)

#  for bigram, count in coll_bigrams_and_counts:
#    if count < min_count:
#      continue
#    coll_MLE = count/coll_N
#    bkgnd_MLE = bkgnd_bigram_counts[bigram]/bkgnd_N
#    if coll_MLE > bkgnd_MLE * 100:
#      print "%s\t%s" % (count/coll_N, ' '.join(bigram))
#    else:
#      print "-\t%s" % ' '.join(bigram)

if __name__=='__main__':
  import util; util.fix_stdio()
  #background_model = lang_model.LocalLM()
  #collect_statistics_into_model(open("data/the_en_tweets"), background_model)

  background_model = lang_model.TokyoLM()
  #background_model = lang_model.MemcacheLM()

  collection_model = lang_model.LocalLM()
  collect_statistics_into_model(open(sys.argv[1]), collection_model)
  type='unigram'
  for ratio,ngram in compare_models(collection_model, background_model, type, 1):
    print "%s\t%s\t%s\t%s" % (ratio, ngram, collection_model.counts[type][ngram], background_model.counts[type][ngram])

  #output_ngram_counts(unigram_counts, 100)
  #output_ngram_counts(bigram_counts, 20)
