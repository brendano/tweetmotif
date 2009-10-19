"""\
Easy-to-use regular expression API for Python, where _S() and _R() are the
primitives for everything.
  
    >>> from sane_re import *

Matching:

    >>> _R('[a-z]').match("hiho")          # Match (like =~)
    <Match 0:1>
    >>> _S("hiho").match('[a-z]')          # Match, other way if you want
    <Match 0:1>
    >>> _S("hiho")['h.']                   # Extraction by indexing
    'hi'
    >>> _S("hiho")['(h.)(h.)', 2]          # Extraction by indexing: pick group
    'ho'
    >>> _S("HIHO")['[a-z]']
    None
    >>> _S("HIHO")[ _R('[a-z]', 'i') ]     # Flags as string
    'H'
    >>> _R('[a-z]').matches("omg!")        # Multiple matches
    <generator object>
    >>> [x.span for x in _R('[a-z]').matches("omg!")]
    [(0, 1), (1, 2), (2, 3)]


Mashing:

    >>> _S("hiho").gsub('[io]', '_')
    'h_h_'

    >>> _S("hiho").gsub('[io]', lambda m: " |" + m[0] + "| ")
    'h |i| h |o| '

    >>> _S("hiho").split('[io]')
    ['h', 'h', '']

Groups:

    >>> _R('([a-z]+)([0-9]+)').show_match("hello world42 ok")
    hello world42 ok
          0000000   
          1111122   
    >>> match = _R('([a-z]+)([0-9]+)').show_match("hello world42 ok")
    >>> match[0]
    'world42'
    >>> match[1]
    'world'
    >>> match[2]
    '42'
    >>> match.groups
    ('world', '42')
    >>> match.groupspan(1)
    (6, 11)
    >>> match.groupspan(2)
    (11, 13)
"""

"""
More notes

We wrap `re` methods to rejigger their API, to make them more convenient and
consistent.

* Trying to close the usability gap with Perl/Ruby.  _R() is replacement for
  not having regex literal syntax builtin to the language.  _S() adds convenient
  methods, conforming to our conventions, that the string class doesn't have.
* I always forget re.search/match()'s argument order.  Using either _R().match() or
  _S().match() is completely unambiguous.
* Never use re.match(), always re.search().  What good is the former if you
  can use a caret?  Having both only causes confusion.
* Specify flags via a string of lowercase characters -- like open() -- but with
  the standard regex flags from Perl/Ruby/etc.
* Python doesn't have a do-only-one-substitution operation -- in Awk/Perl/Ruby
  terms, it has gsub() but not sub() -- so make naming clearer.
* Match objects have @property accessors like modern Python classes
"""

__author__  = "Brendan O'Connor (anyall.org, brenocon@gmail.com)"
__website__ = "http://anyall.org/sane_re.py"
__version__ = "Sept 2009"
__all__ = ['_S','_R']
import re, _sre
from StringIO import StringIO
from types import FunctionType
RegexType = type(re.compile("bla"))

def stringify(s, encoding='utf8', *args):
  if isinstance(s,str): return s
  return s.encode(encoding, *args)

def _S(string):
  string = stringify(string)
  return _Ss(string)
  
class _Ss(str):
  """ wrap a string, endowing it with regex methods """
  def gsub(self, regex, replacement):
    """ like py re.sub or ruby String.gsub """
    return gsub(self, _R(regex), replacement)
  replace = gsub
  def match(self, regex):
    """ like py re.search """
    return match(self, _R(regex))
  def split(self, regex, maxsplit=0):
    """ like py re.split.  overrides wrapped str.split() """
    #if isinstance(regex,(str,unicode)): return str.split(self,regex)
    return _R(regex).sre.split(self, maxsplit)
  def matches(self, regex, group=None):
    """ like py re.finditer """
    for m in _R(regex).sre.finditer(self):
      if group is None: yield wrap_match(m)
      else: yield wrap_match(m)[group]
  def __getitem__(self, args):
    """ like perl string[/regex/] or string[/reg(ex)/, 1] """
    if isinstance(args,int):
      # not for us
      return str.__getitem__(self, args)
    if isinstance(args,tuple):
      regex = args[0]
      group = args[1] if len(args)>1 else 0
    else:
      regex = args
      group = 0
    m = match(self, _R(regex))
    return m and m[group]
  def show_match(self, regex, group=0, numbers=True):
    """ for testing """
    import ansi,sys
    regex = _R(regex)
    def color_a_match(m):
      return ansi.color(m[group],'backblack','lgray')
    print self.gsub(regex, color_a_match)
    if not numbers: return
    groups_per_pos = [[] for i in range(len(self))]
    for m in self.matches(regex):
      for g in range(regex.groups+1):
        for i in range(*m.groupspan(g)):
          groups_per_pos[i].append(g)
    while 1:
      for i in range(len(self)):
        if groups_per_pos[i]:
          sys.stdout.write(str(groups_per_pos[i].pop(0)))
        else:
          sys.stdout.write(" ")
      sys.stdout.write("\n")
      if all(len(x)==0 for x in groups_per_pos): break

def gsub(string, regex, replacement):
  "string and regex need to be sane_re.{_S,_R} wrappers"
  if isinstance(replacement, FunctionType):
    return fancy_sub(string, regex.sre, replacement)
  return regex.sre.sub(replacement, string)
def match(string, regex):
  "string and regex need to be sane_re.{_S,_R} wrappers"
  return wrap_match(regex.sre.search(string))

def fancy_sub(string, regex, repl_fn=lambda m: ">> %s <<" % m[0]):
  "string and regex need to be sane_re.{_S,_R} wrappers"
  ret = StringIO()
  last = 0
  for m in string.matches(regex):
    ret.write(string[last:m.start])
    ret.write(repl_fn(m))
    last = m.end
  if last < len(string):
    ret.write(string[last:])
  return ret.getvalue()

class _R:
  """ regex wrapper.  supports most _S methods too. """
  def __init__(self, arg, flags='', bin_flags=0):
    self.orig = None
    if isinstance(arg, RegexType):
      self.sre = arg
    elif isinstance(arg, _R):
      self.sre = arg.sre
    elif isinstance(arg, (str,unicode)):
      bin_flags |= flag_convert(flags)
      self.sre = re.compile(arg,bin_flags)
      self.orig = arg
    else: raise TypeError
  def __getattr__(self,name): return getattr(self.sre,name)
  def gsub(regex,string,replacement): return gsub(_S(string),regex,replacement)
  replace = gsub
  def match(regex,string): return match(_S(string), regex)
  def split(regex,string,maxsplit=0): return _S(string).split(regex,maxsplit=maxsplit)
  def matches(regex,string,group=None): return _S(string).matches(regex,group=group)
  def show_match(regex,string,**kwargs): return _S(string).show_match(regex,**kwargs)
  def __str__(self): 
    if self.orig: return '/' + self.orig + '/'
    return "<_R with %s>" % repr(self.sre)
  __repr__ = __str__

def wrap_match(sre_match):
  if sre_match is None: return None
  return Match(sre_match)

class Match:
  def __init__(self, sre):
    self.sre = sre
  @property
  def span(self): return self.sre.span()
  @property
  def start(self): return self.sre.start()
  @property
  def end(self): return self.sre.end()
  @property
  def groups(self): return self.sre.groups()
  @property
  def groupdict(self): return self.sre.groupdict()
  def groupspan(self,group):
    if isinstance(group,int): return self.sre.span(group)
    else: raise TypeError
  def groupstart(self,group):
    if isinstance(group,int): return self.sre.start(group)
    else: raise TypeError
  def groupend(self,group):
    if isinstance(group,int): return self.sre.end(group)
    else: raise TypeError
  def __getitem__(self,group):
    if isinstance(group,int):
      return self.sre.group(group)
    if isinstance(group,str):
      return self.sre.groupdict()[group]
    else: raise TypeError
  def __str__(self):
    return "<Match %d:%d>" % self.span
  __repr__ = __str__


flag_mappings = {
    'i':re.IGNORECASE,
    'l':re.LOCALE,
    'm':re.MULTILINE,
    's':re.DOTALL,
    'u':re.UNICODE,
    'x':re.VERBOSE, }

def flag_convert(flags):
  bin_flags = 0
  for flag in flags:
    bin_flags |= flag_mappings[flag]
  return bin_flags

#def _s(x):
#  if isinstance(x,unicode): return _su(x)
#  if isinstance(x,str): return _ss(x)

def fancy_sub_sre(string, sre_regex, repl_fn=lambda m: ">> %s <<" % m.group()):
  """ like ruby String.gsub() when passing in a block """
  ret = StringIO()
  last = 0
  for m in sre_regex.finditer(string):
    ret.write(string[last:m.start()])
    ret.write(repl_fn(m))
    last = m.end()
  if last < len(string):
    ret.write(string[last:])
  return ret.getvalue()

