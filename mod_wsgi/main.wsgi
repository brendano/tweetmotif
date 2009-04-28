import os
import sys
dotdot = os.path.join(os.path.dirname(sys.modules[__name__].__file__), '..')
os.chdir(dotdot)
#print>>sys.stderr, os.getcwd()
#print>>sys.stderr, dotdot
sys.path.insert(0,'')
sys.stdout = sys.stderr
from frontend import application

#def application(environ, start_response):
#  status = '200 OK'
#  output = 'Hello good World!'
#
#  response_headers = [('Content-type', 'text/html')]
#  start_response(status, response_headers)
#
#  yield repr(sys.path)
#  yield "<hr>"
#  yield "<table>"
#  for k in sorted(environ.keys()):
#    yield "<tr><td>" + k
#    yield "<td>" + str(environ[k])
#    #yield "<br>"
#  yield "</table>"
#  yield "<hr>"
#  yield output
