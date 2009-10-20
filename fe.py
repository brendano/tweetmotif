import sys
sys.path.insert(0,'/usr2/corpora/tweets/tweetmotif')
import twokenize,util,bigrams
util.fix_stdio()
from sane_re import *

AposFix = _R(r"( |^)(' [stm])( |$)")


for line in sys.stdin:
  parts = util.unicodify(line[:-1]).split("\t")
  text = parts[-1]
  toks = twokenize.simple_tokenize(text)
  toked = " ".join(toks)
  #print "\t".join(parts[:-1]) + "\t" + toked
  #try: AposFix.show_match(toked)
  #except: pass
  featstr = AposFix.gsub(toked, lambda m: m[1]+m[2].replace(" ","")+m[3])
  featstr = featstr.lower()
  toks = featstr.split()
  feats = [ug[0] for ug in bigrams.filtered_unigrams(toks)]
  feats += ["_".join(ng) for ng in bigrams.filtered_bigrams(toks)]

  print "\t".join(parts[:-1]) + "\t" + util.unicodify(" ".join(feats))
