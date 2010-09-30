TweetMotif
=========

TweetMotif is a faceted/topic/summarizing search system for Twitter,
built on top of the search.twitter.com API.  http://tweetmotif.com


Do you just want the tokenizer?
===============================

All you need is two files:

* [twokenize.py][t]
* [emoticons.py][e]

[t]: http://github.com/brendano/tweetmotif/raw/master//twokenize.py
[e]: http://github.com/brendano/tweetmotif/raw/master//emoticons.py


More on TweetMotif
------------------

By Brendan O'Connor, Michel Krieger, and David Ahn. 
Written over April-May 2009 and released April 2010.

The TweetMotif paper (inside `EXAMPLES_AND_WRITING`, or a
[copy at this link][1]) overviews the system.

[1]: http://anyall.org/oconnor_krieger_ahn.icwsm2010.tweetmotif.pdf


Running TweetMotif
------------------

Prerequisites

* Tokyo Cabinet
* Tokyo Tyrant
* mod_wsgi
* Python: version 2.5 works

There are precompiled versions of the Tokyo infrastructure in `platform/`, for Mac
OSX 10.5 and Ubuntu 8.04-ish. In the off-chance they will work for your system,
uncomment the code that specifies to use them (`grep platform *.py`). You may also
have to muck around with `ld.so.conf.d` and `ldconfig` (on Linux) to get
`mod_wsgi`, which is inside Apache, to see them.

You also need to be running Tokyo Tyrant for the query cache. This is usually
inconvenient for just getting started; in which case, disable it by commenting out
the lines

    # the_cache = ....
    # @the_cache.wrap

In `query_cache.py`


Architecture
------------

There is a *backend* and *frontend*. The backend talks to search.twitter.com and
does all text processing, clustering, etc. The frontend is a Django web site with
normal and iPhone versions.

The backend makes extensive use of Tokyo Cabinet and Tyrant databases: for the
language model, and the query cache.

Both the backend and frontend are WSGI apps. Everything is set up to run through
`mod_wsgi`. They communicate via JSON-over-HTTP.

### Backend 

The backend is run through, confusingly enough, *frontend.py*. It also has a
primitive frontend for development purposes there.

### Frontend

The frontend is Django.  See *djfrontend/*.


License
-------

TweetMotif is licensed under the Apache License 2.0:
http://www.apache.org/licenses/LICENSE-2.0.html

Copyright Brendan O'Connor, Michel Krieger, and David Ahn, 2009-2010.
