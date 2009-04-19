#!/usr/bin/env python2.5

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

punc_re = re.compile(r'''^[^a-zA-Z0-9_@]+$''')

#def tokens(text):
#  return non_word.sub(' ', text).split()

stopwords = set(open("stopwords").read().split())


def unigrams(tokens):
  return [(tok,) for tok in tokens]

def bigrams(tokens):
  #return zip(['!START'] + tokens, tokens)
  return ngrams(tokens,2)

def multi_ngrams(tokens, n_and_up):
  ret = []
  for k in range(n_and_up, len(tokens)):
    ret += ngrams(tokens, k)
  return ret

def ngrams(tokens, n):
  return [tuple(tokens[i:(i+n)]) for i in range(len(tokens) - (n-1))]

    
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

def tokenize_and_clean(msg):
  toks = (tok.lower() for tok in twokenize.tokenize(msg))
  toks = (tok for tok in toks if not punc_re.search(tok))
  return list(toks)

def collect_statistics_into_model(filename, lang_model):
  for line in util.counter(  fileinput.input(filename)  ):
    toks = tokenize_and_clean(line)
    lang_model.info['big_n'] += len(toks)
    for unigram in unigrams(toks):
      lang_model.add('unigram', unigram)
    for bigram in bigrams(toks):
      lang_model.add('bigram', bigram)


def compare_models(collection_model, background_model, ngram_type, min_count=1):
  bkgnd_ngram_counts = background_model.counts[ngram_type]
  bkgnd_N = float(background_model.info["big_n"])
  coll_ngram_counts = collection_model.counts[ngram_type]
  coll_N = float(collection_model.info["big_n"])
  coll_ngrams_and_counts = coll_ngram_counts.items()
  coll_ngrams_and_mle_probs = map(lambda (b, c): (b, c/coll_N), coll_ngrams_and_counts)
  coll_ngrams_and_mle_prob_ratio = map(lambda (b, p): (b, compute_ratio(p, bkgnd_ngram_counts[b]/bkgnd_N)), coll_ngrams_and_counts)
  coll_ngrams_and_mle_prob_ratio.sort(key=lambda pair: pair[1], reverse=True)
  for ngram, ratio in coll_ngrams_and_mle_prob_ratio:
    if coll_ngram_counts[ngram] < min_count:
      continue
    yield ratio,ngram

def compute_ratio(num, denom):
  if denom == 0:
    return 0
  else:
    return num/denom

#  for bigram, count in coll_bigrams_and_counts:
#    if count < min_count:
#      continue
#    coll_MLE = count/coll_N
#    bkgnd_MLE = bkgnd_bigram_counts[bigram]/bkgnd_N
#    if coll_MLE > bkgnd_MLE * 100:
#      print "%s\t%s" % (count/coll_N, ' '.join(bigram))
#    else:
#      print "-\t%s" % ' '.join(bigram)

#def load_background_model():
#  global background_model
#  background_model = collect_statistics("data/the_en_tweets")


if __name__=='__main__':
  #background_model = collect_statistics("data/the_en_tweets")
  #collection_model = collect_statistics(sys.argv[1])

  background_model = lang_model.LocalLM()
  collect_statistics_into_model("data/the_en_tweets", background_model)

  #background_model = lang_model.MemcacheLM()

  collection_model = lang_model.LocalLM()
  collect_statistics_into_model(sys.argv[1], collection_model)
  for ratio,ngram in compare_models(collection_model, background_model, "unigram", 1):
    print "%s\t%s" % (ratio, ngram)

  #output_ngram_counts(unigram_counts, 100)
  #output_ngram_counts(bigram_counts, 20)
