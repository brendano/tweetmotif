import re,sys
import emoticons
mycompile = lambda pat:  re.compile(pat,  re.UNICODE)
def flatten(iter):
  return list(itertools.chain(*iter))

URL_S = 'https?://\S+'
PUNCT_S = '[.?!,:;]+'
ENTITY_S = '&(amp|lt|gt|quot);'

TIMELIKE = r'\d+:\d+'
ABBREVS = [r'[aA]\.[mM]\.', r'[pP]\.[mM]\.']

PROTECT_THESE = [
    emoticons.EMOTICON_S,
    URL_S,
    ENTITY_S,
    TIMELIKE,
    PUNCT_S,
]
PROTECT_THESE += ABBREVS
PROTECT_S = "|".join(PROTECT_THESE)
PROTECT_RE = mycompile(PROTECT_S)

EDGE_SINGLE_QUOTE = r"\s'\S|\S'\s"

def tokenize(tweet):
  s = tweet
  s = squeeze_whitespace(s)
  s = edge_quote_munge(s)

  goods = []
  bads = []
  i = 0
  if PROTECT_RE.search(s):
    for m in PROTECT_RE.finditer(s):
      goods.append( (i,m.start()) )
      bads.append(m.span())
      i = m.end()
    goods.append( (m.end(), len(s)) )
  else:
    goods = [ (0, len(s)) ]
  #print goods
  #print bads
  assert len(bads)+1 == len(goods)

  goods = [s[i:j] for i,j in goods]
  bads  = [s[i:j] for i,j in bads]
  goods = [unprotected_tokenize(x) for x in goods]
  res = []
  for i in range(len(bads)):
    res += goods[i]
    res.append(bads[i])
  res += goods[-1]
  return res

WS_RE = mycompile(r'\s+')
def squeeze_whitespace(s):
  new_string,n = WS_RE.subn(" ",s)
  return new_string


SQUOTE_LEFTEDGE  = mycompile(r"\s'(\S)")
SQUOTE_RIGHTEDGE = mycompile(r"(\S)'\s")
def edge_quote_munge(s):
  s = SQUOTE_LEFTEDGE.subn( r" ' \1", s)[0]
  s = SQUOTE_RIGHTEDGE.subn(r"\1 ' ", s)[0]
  return s


SPLITTER_RE = mycompile(r'[^a-zA-Z0-9_@]+')
def unprotected_tokenize(s):
  return s.split()



if __name__=='__main__':
  for line in sys.stdin:
    print " ".join(tokenize(line.strip()))

