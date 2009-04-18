#!/usr/bin/env python2.5

# Histogram of unigrams and bigrams in a stream of tweets
#
# What we actually want is difference from background collection

import sys
import re
import fileinput
from collections import defaultdict

non_word = re.compile(r'''[^a-zA-Z0-9_@]+''')

def tokens(text):
  return non_word.sub(' ', text).split()

def bigrams(tokens):
  return zip(['!START'] + tokens, tokens)

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

def collect_statistics(filename):
  unigram_counts = defaultdict(int)
  bigram_counts = defaultdict(int)
  big_n = 0
  for line in fileinput.input(filename):
    toks = map(lambda tok: tok.lower(), tokens(line))
    big_n += len(toks)
    for unigram in toks:
      unigram_counts[unigram] += 1
    for bigram in bigrams(toks):
      bigram_counts[bigram] += 1
  return { "unigrams": unigram_counts,
      "bigrams": bigram_counts,
      "big_n": big_n }

def compare_models(collection_model, background_model, min_count=1):
  bkgnd_bigram_counts = background_model["bigrams"]
  bkgnd_N = float(background_model["big_n"])
  coll_bigram_counts = collection_model["bigrams"]
  coll_N = float(collection_model["big_n"])
  coll_bigrams_and_counts = coll_bigram_counts.items()
  coll_bigrams_and_counts.sort()
  for bigram, count in coll_bigrams_and_counts:
    if count < min_count:
      continue
    coll_MLE = count/coll_N
    bkgnd_MLE = bkgnd_bigram_counts[bigram]/bkgnd_N
    if coll_MLE > bkgnd_MLE * 10:
      print "%s\t%s" % (count/coll_N, ' '.join(bigram))
    else:
      print "-\t%s" % ' '.join(bigram)

if __name__=='__main__':
  unigram_counts = defaultdict(int)
  bigram_counts = defaultdict(int)
  background_model = collect_statistics("the_en")
  collection_model = collect_statistics(sys.argv[1])
  compare_models(collection_model, background_model, 20)

  #output_ngram_counts(unigram_counts, 100)
  #output_ngram_counts(bigram_counts, 20)
