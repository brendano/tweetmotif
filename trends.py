import myurl
from datetime import datetime, timedelta
import simplejson

def current_topics():
  if needs_update(): pull()
  return data and data['trends'].values()[0]

data = None
last_update = datetime.now() - timedelta(days=999)

URL = "http://search.twitter.com/trends/current.json"
def pull():
  global data, last_update
  try:
    data = simplejson.load(myurl.urlopen(URL))
    last_update = datetime.now()
    print "Updated trends.data"
  except (ValueError,) + myurl.url_exceptions, e:
    print "Error updating trends: %s %s" % (type(e), e)
    return data

def needs_update():
  return (datetime.now() - last_update) > timedelta(minutes=10)

