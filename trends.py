import myurl
from datetime import datetime, timedelta
import simplejson

def current_topics():
  if needs_update(): pull()
  if not data: return []
  for x in data['trends'].values()[0]:
    # twitter's x['query'] is too complex, often with boolean OR's.  ugly.  
    # silly to optimize recall so let's do only one form.
    if 'simple_query' not in x:
      x['simple_query'] = ('"%s"' % x['name']) if len(x['name'].split())>1 else x['name']
  return data['trends'].values()[0]

data = None
last_update = datetime.now() - timedelta(days=999)

URL = "http://search.twitter.com/trends/current.json"
def pull(ntry=5):
  global data, last_update
  for x in range(ntry):
    try:
      data = simplejson.load(myurl.urlopen(URL))
      last_update = datetime.now()
      print "Updated trends.data"
      return data

    except (ValueError,) + myurl.url_exceptions, e:
      print "Error updating trends: %s %s" % (type(e), e)

    

def needs_update():
  return (datetime.now() - last_update) > timedelta(minutes=5)

if __name__=='__main__':
  print current_topics()
