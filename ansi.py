""" Terminal coloring via ANSI escape codes """

def color(s, *codes):
  if len(codes)==0: raise Exception("what color, yo?")
  if len(codes)>1: codes = sorted(codes, key=code_precedence)
  for code in codes:
    s = CODES[code] + s
  s += CODES['reset']
  return s

def code_precedence(code):
  if code=='bold': return 10
  else: return 100

# adapted from http://dotfiles.org/~sd/.irbrc
CODES = dict(
  black    = "\033[0;30m",
  gray     = "\033[1;30m",
  lgray    = "\033[0;37m",
  white    = "\033[1;37m",
  red      = "\033[0;31m",
  lred     = "\033[1;31m",
  green    = "\033[0;32m",
  lgreen   = "\033[1;32m",
  brown    = "\033[0;33m",
  yellow   = "\033[1;33m",
  blue     = "\033[0;34m",
  lblue    = "\033[1;34m",
  purple   = "\033[0;35m",
  lpurple  = "\033[1;35m",
  cyan     = "\033[0;36m",
  lcyan    = "\033[1;36m",

  backblack  = "\033[40m",
  backred    = "\033[41m",
  backgreen  = "\033[42m",
  backyellow = "\033[43m",
  backblue   = "\033[44m",
  backpurple = "\033[45m",
  backcyan   = "\033[46m",
  backgray   = "\033[47m",

  reset      = "\033[0m",
  bold       = "\033[1m",
  underscore = "\033[4m",
  blink      = "\033[5m",
  reverse    = "\033[7m",
  concealed  = "\033[8m",
)


XTERM_SET_TITLE   = "\033]2;"
XTERM_END         = "\007"
ITERM_SET_TAB     = "\033]1;"
ITERM_END         = "\007"
SCREEN_SET_STATUS = "\033]0;"
SCREEN_END        = "\007"

