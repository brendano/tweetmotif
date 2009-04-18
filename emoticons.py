#from __future__ import print_function
import re,sys
import util

mycompile = lambda pat:  re.compile(pat,  re.UNICODE)
#SMILEY = mycompile(r'[:=].{0,1}[\)dpD]')
#MULTITOK_SMILEY = mycompile(r' : [\)dp]')

HAPPY_MOUTHS = r'[\)\]D]'
SAD_MOUTHS = r'[\(\[]'
TONGUE = r'[pP]'
OTHER_MOUTHS = r'[doO]'

NORMAL_EYES = r'[:=]'
WINK = r'[;]'

NOSE_AREA = r'(| |-)'   ## rather tight precision, could use . wildcard...

HAPPY_RE =  mycompile( '(\^_\^|' + NORMAL_EYES + NOSE_AREA + HAPPY_MOUTHS + ')')
SAD_RE = mycompile(NORMAL_EYES + NOSE_AREA + SAD_MOUTHS)

WINK_RE = mycompile(WINK + NOSE_AREA + HAPPY_MOUTHS)
TONGUE_RE = mycompile(NORMAL_EYES + NOSE_AREA + TONGUE)
OTHER_RE = mycompile( '('+NORMAL_EYES+'|'+WINK+')'  + NOSE_AREA + OTHER_MOUTHS )

EMOTICON_S = (
    "("+NORMAL_EYES+"|"+WINK+")"+ NOSE_AREA + 
    "("+TONGUE+"|"+OTHER_MOUTHS+"|"+SAD_MOUTHS+"|"+HAPPY_MOUTHS+")"
)
EMOTICON_RE = mycompile(EMOTICON_S)

#EMOTICON_RE = "|".join([HAPPY_RE,SAD_RE,WINK_RE,TONGUE_RE,OTHER_RE])
#EMOTICON_RE = mycompile(EMOTICON_RE)

def analyze_tweet(text):
  h= HAPPY_RE.search(text)
  s= SAD_RE.search(text)
  if h and s: return "BOTH_HS"
  if h: return "HAPPY"
  if s: return "SAD"
  return "NA"

  # more complex & harder, so disabled for now
  #w= WINK_RE.search(text)
  #t= TONGUE_RE.search(text)
  #a= OTHER_RE.search(text)
  #h,w,s,t,a = [bool(x) for x in [h,w,s,t,a]]
  #if sum([h,w,s,t,a])>1: return "MULTIPLE"
  #if sum([h,w,s,t,a])==1:
  #  if h: return "HAPPY"
  #  if s: return "SAD"
  #  if w: return "WINK"
  #  if a: return "OTHER"
  #  if t: return "TONGUE"
  #return "NA"

#if __name__=='__main__':
#  for line in util.counter(  sys.stdin  ):
#    print(analyze_tweet(line.strip()), line.strip(), sep="\t")
