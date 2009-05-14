from copy import copy

def highlight(toks, ngrams_and_tags):
  ret = []
  ngram_alignments = {}
  for ngram in ngrams_and_tags:
    ngram_alignments[tuple(ngram)] = compute_highlight_alignments(toks, ngram)
  ngram_alignments = ngram_alignments.items()
  # doing longest first, forces subsumed <n-grams to be DOM children .. relies on endtags being all equivalent
  ngram_alignments.sort(key= lambda (ng,alignments): -len(ng) )
  for i in range(len(toks.text)):
    for ngram,(starts,ends) in ngram_alignments:
      if i in ends: ret += ngrams_and_tags[ngram][1]
      if i in starts: ret += ngrams_and_tags[ngram][0]
    ret += toks.text[i]
  for ngram,(starts,ends) in ngram_alignments:
    if len(toks.text) in ends:
      ret += ngrams_and_tags[ngram][1]
  return "".join(ret)

def simple_highlight(toks, ngram, start="<b>", end="</b>"):
  return highlight(toks, {ngram: (start,end)})

def compute_highlight_alignments(toks, ngram):
  toks = copy(toks)
  toks.append("!END")
  ngram = list(ngram)
  K = len(ngram)
  matching_positions = [i for i in range(len(toks) - K) if ngram==toks[i:(i+K)]]
  starts, ends = [], []
  for pos in matching_positions:
    starts.append( toks.alignments[pos] )
    ends.append(   toks.alignments[pos+K-1] + len(toks[pos+K-1]) )
  return starts,ends

# def test_overlap():
  

if __name__=='__main__':
  import bigrams
  for orig in [
      "Oracle to buy Sun? What's going to happen to MySQL? JRuby? Glassfish? Postgres seems like a no brainer",
      "# RT @rickwatson twittersphere blowing up over oracle buying sun, and with it #mysql. LAMP just became LAPP (replaced with postgres)",
      ]:
    toks=bigrams.tokenize_and_clean(orig)
    print highlight(toks,{('to','buy'):("[[","]]"), ('buy','sun'):("{{","}}")}       )
    print highlight(toks,{('blowing',):("[[","]]"), ('blowing','up'):("{{","}}")}       )
