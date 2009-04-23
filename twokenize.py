# -*- coding: utf-8 -*-
import re,sys
import emoticons
import util
mycompile = lambda pat:  re.compile(pat,  re.UNICODE)
def flatten(iter):
  return list(itertools.chain(*iter))

URL_S = 'https?://\S+'
PUNCT_S = '''[“".?!,:;]+'''
ENTITY_S = '&(amp|lt|gt|quot);'

TIMELIKE = r'\d+:\d+'
NUMNUM = r'\d+\.\d+'
ABBREVS1 = ['am','pm','us','usa','ie','eg']
def regexify_abbrev(a):
  chars = list(a)
  icase = ["[%s%s]" % (c,c.upper()) for c in chars]
  dotted = [r'%s\.' % x for x in icase]
  return "".join(dotted)
ABBREVS = [regexify_abbrev(a) for a in ABBREVS1]

ARBITRARY_ABBREV = r'''([A-Z]\.){3,99}'''

PROTECT_THESE = [
    emoticons.EMOTICON_S,
    URL_S,
    ENTITY_S,
    TIMELIKE,
    NUMNUM,
    PUNCT_S,
    ARBITRARY_ABBREV,
]
PROTECT_THESE += ABBREVS
PROTECT_S = "|".join(PROTECT_THESE)
PROTECT_RE = mycompile(PROTECT_S)


class Tokenization(list):
  " list of tokens, plus extra info "
  def __init__(self):
    self.alignments = []
    self.text = ""
  def subset(self, tok_inds):
    new = Tokenization()
    new += [self[i] for i in tok_inds]
    new.alignments = [self.alignments[i] for i in tok_inds]
    new.text = self.text
    return new
  def assert_consistent(t):
    assert len(t) == len(t.alignments)
    assert [t.text[t.alignments[i] : (t.alignments[i]+len(t[i]))] for i in range(len(t))] == list(t)

def align(toks, orig):
  s_i = 0
  alignments = [None]*len(toks)
  for tok_i in range(len(toks)):
    while True:
      L = len(toks[tok_i])
      if orig[s_i:(s_i+L)] == toks[tok_i]:
        alignments[tok_i] = s_i
        s_i += L
        break
      s_i += 1
      if s_i >= len(orig): raise AlignmentFailed((orig,toks,alignments))
      #if orig[s_i] != ' ': raise AlignmentFailed("nonspace advance: %s" % ((s_i,orig),))
  if any(a is None for a in alignments): raise AlignmentFailed((orig,toks,alignments))

  return alignments

class AlignmentFailed(Exception): pass

def tokenize(tweet):
  text = util.unicodify(tweet)
  text = squeeze_whitespace(text)
  t = Tokenization()
  t += simple_tokenize(text)
  t.text = text
  t.alignments = align(t, text)
  return t

def simple_tokenize(text):
  s = text
  s = edge_punct_munge(s)

  # strict alternating ordering through the string.  first and last are goods.
  # good bad good bad good bad good
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
  return new_string.strip()

EDGE_PUNCT      = r"""['"([\)\]]"""   # alignment failures. hm.
#NOT_EDGE_PUNCT = r"""[^'"([\)\]]"""
NOT_EDGE_PUNCT = r"""[a-zA-Z0-9]"""
EDGE_PUNCT_LEFT  = r"""(\s|^)(%s+)(%s)""" % (EDGE_PUNCT, NOT_EDGE_PUNCT)
EDGE_PUNCT_RIGHT =   r"""(%s)(%s+)(\s|$)""" % (NOT_EDGE_PUNCT, EDGE_PUNCT)
EDGE_PUNCT_LEFT_RE = mycompile(EDGE_PUNCT_LEFT)
EDGE_PUNCT_RIGHT_RE= mycompile(EDGE_PUNCT_RIGHT)

def edge_punct_munge(s):
  s = EDGE_PUNCT_LEFT_RE.subn( r"\1\2 \3", s)[0]
  s = EDGE_PUNCT_RIGHT_RE.subn(r"\1 \2\3", s)[0]
  return s


SPLITTER_RE = mycompile(r'[^a-zA-Z0-9_@]+')
def unprotected_tokenize(s):
  return s.split()

if __name__=='__main__':
  import ansi
  util.fix_stdio()
  for line in sys.stdin:
    print ansi.color(line.strip(),'red')
    print ansi.color(" ".join(tokenize(line.strip())),'blue','bold')

