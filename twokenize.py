# -*- coding: utf-8 -*-
""" tokenizer for tweets!  might be appropriate for other social media dialects too.
general philosophy is to throw as little out as possible.
development philosophy: every time you change a rule, do a diff of this
program's output on ~100k tweets.  if you iterate through many possible rules
and only accept the ones that seeem to result in good diffs, it's a sort of
statistical learning with in-the-loop human evaluation :)
"""

__author__="brendan o'connor (anyall.org)"

import re,sys
import emoticons
mycompile = lambda pat:  re.compile(pat,  re.UNICODE)
def regex_or(*items):
  r = '|'.join(items)
  r = '(' + r + ')'
  return r
def pos_lookahead(r):
  return '(?=' + r + ')'
def neg_lookahead(r):
  return '(?!' + r + ')'
def optional(r):
  return '(%s)?' % r


PunctChars = r'''['“".?!,:;]'''
Punct = '%s+' % PunctChars
Entity = '&(amp|lt|gt|quot);'

# Url Regex from http://daringfireball.net/2010/07/improved_regex_for_matching_urls
# should handle bit.ly, goog.gl, t.co, mailto:, urls with unicode, etc.
Url = r'''
(?xi)
\b
(                           # Capture 1: entire matched URL
  (?:
    [a-z][\w-]+:                # URL protocol and colon
    (?:
      /{1,3}                        # 1-3 slashes
      |                             #   or
      [a-z0-9%]                     # Single letter or digit or '%'
                                    # (Trying not to match e.g. "URI::Escape")
    )
    |                           #   or
    www\d{0,3}[.]               # "www.", "www1.", "www2." … "www999."
    |                           #   or
    [a-z0-9.\-]+[.][a-z]{2,4}/  # looks like domain name followed by a slash
  )
  (?:                           # One or more:
    [^\s()<>]+                      # Run of non-space, non-()<>
    |                               #   or
    \(([^\s()<>]+|(\([^\s()<>]+\)))*\)  # balanced parens, up to 2 levels
  )+
  (?:                           # End with:
    \(([^\s()<>]+|(\([^\s()<>]+\)))*\)  # balanced parens, up to 2 levels
    |                                   #   or
    [^\s`!()\[\]{};:'".,<>?«»“”‘’]        # not a space or one of these punct chars
  )
)
'''

Url_RE = re.compile("(%s)" % Url, re.U|re.I)

Timelike = r'\d+:\d+'
NumNum = r'\d+\.\d+'
NumberWithCommas = r'(\d+,)+?\d{3}' + pos_lookahead(regex_or('[^,]','$'))

Abbrevs1 = ['am','pm','us','usa','ie','eg']
def regexify_abbrev(a):
  chars = list(a)
  icase = ["[%s%s]" % (c,c.upper()) for c in chars]
  dotted = [r'%s\.' % x for x in icase]
  return "".join(dotted)
Abbrevs = [regexify_abbrev(a) for a in Abbrevs1]

BoundaryNotDot = regex_or(r'\s', '[“"?!,:;]', Entity)
aa1 = r'''([A-Za-z]\.){2,}''' + pos_lookahead(BoundaryNotDot)
aa2 = r'''([A-Za-z]\.){1,}[A-Za-z]''' + pos_lookahead(BoundaryNotDot)
ArbitraryAbbrev = regex_or(aa1,aa2)

assert '-' != '―'
Separators = regex_or('--+', '―')
Decorations = r' [  ♫   ]+ '.replace(' ','')

EmbeddedApostrophe = r"\S+'\S+"

ProtectThese = [
    emoticons.Emoticon,
    Url,
    Entity,
    Timelike,
    NumNum,
    NumberWithCommas,
    Punct,
    ArbitraryAbbrev,
    Separators,
    Decorations,
    EmbeddedApostrophe,
]
Protect_RE = mycompile(regex_or(*ProtectThese))


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

def unicodify(s, encoding='utf8', *args):
  if isinstance(s,unicode): return s
  if isinstance(s,str): return s.decode(encoding, *args)
  return unicode(s)

def tokenize(tweet):
  text = unicodify(tweet)
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
  if Protect_RE.search(s):
    for m in Protect_RE.finditer(s):
      goods.append( (i,m.start()) )
      bads.append(m.span())
      i = m.end()
    goods.append( (m.end(), len(s)) )
  else:
    goods = [ (0, len(s)) ]
  assert len(bads)+1 == len(goods)

  goods = [s[i:j] for i,j in goods]
  bads  = [s[i:j] for i,j in bads]
  #print goods
  #print bads
  goods = [unprotected_tokenize(x) for x in goods]
  res = []
  for i in range(len(bads)):
    res += goods[i]
    res.append(bads[i])
  res += goods[-1]

  res = post_process(res)
  return res

AposS = mycompile(r"(\S+)('s)$")

def post_process(pre_toks):
  # hacky: further splitting of certain tokens
  post_toks = []
  for tok in pre_toks:
    m = AposS.search(tok)
    if m:
      post_toks += m.groups()
    else:
      post_toks.append( tok )
  return post_toks

WS_RE = mycompile(r'\s+')
def squeeze_whitespace(s):
  new_string = WS_RE.sub(" ",s)
  return new_string.strip()

# fun: copy and paste outta http://en.wikipedia.org/wiki/Smart_quotes
EdgePunct      = r"""[  ' " “ ” ‘ ’ < > « » { } ( \) [ \]  ]""".replace(' ','')
#NotEdgePunct = r"""[^'"([\)\]]"""  # alignment failures?
NotEdgePunct = r"""[a-zA-Z0-9]"""
EdgePunctLeft  = r"""(\s|^)(%s+)(%s)""" % (EdgePunct, NotEdgePunct)
EdgePunctRight =   r"""(%s)(%s+)(\s|$)""" % (NotEdgePunct, EdgePunct)
EdgePunctLeft_RE = mycompile(EdgePunctLeft)
EdgePunctRight_RE= mycompile(EdgePunctRight)

def edge_punct_munge(s):
  s = EdgePunctLeft_RE.sub( r"\1\2 \3", s)
  s = EdgePunctRight_RE.sub(r"\1 \2\3", s)
  return s


def unprotected_tokenize(s):
  return s.split()

if __name__=='__main__':
  for line in sys.stdin:
    print u" ".join(tokenize(line[:-1])).encode('utf-8')
    #print "CUR\t" + " ".join(tokenize(line[:-1]))
    #print "WS\t" + " ".join(line[:-1].split())
    #print ansi.color(line.strip(),'red')
    #print ansi.color(" ".join(tokenize(line.strip())),'blue','bold')

