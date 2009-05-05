# python scotchy.py record
# python -mcProfile -s cumulative scotchy.py play
# anyall.org/chunk.py
# python -mcProfile -s cumulative scotchy.py play | chunk END.. | less
# python -mcProfile -s cumulative scotchy.py play | chunk END.. | head
# for x in 1 2 3; do python -mcProfile -s cumulative scotchy.py play | chunk END.. | head -1; done
import cPickle as pickle
from wsgiref.simple_server import make_server, demo_app
import scotch.recorder
import frontend
import util; util.fix_stdio()
recorder = scotch.recorder.Recorder(frontend.application, verbosity=1)
filename = 'recording.pickle'

import sys
if sys.argv[1] == 'record':
  try:
    httpd = make_server('', 8080, recorder)
    print "Serving HTTP on port 8080..."
    httpd.handle_request()
  finally:
    f = open(filename,'w')
    pickle.dump(recorder.record_holder, f)
    f.close()
    print "SCOTCH: saved %d records to %s" % (len(recorder.record_holder), filename)

elif sys.argv[1] == 'play':
  print "SCOTCH: loading records from %s" % filename
  record_holder = pickle.load(open(filename))
  for x in [1]:
    for record in record_holder:
      new_response = record.refeed(frontend.application)
      #print new_response.content_list
  print "END"






