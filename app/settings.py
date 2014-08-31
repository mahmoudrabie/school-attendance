# Stores constants in the Datastore so that you don't need
# to have different values in your code.


from google.appengine.ext import ndb
from google.appengine.api import memcache


settings = {}


class Config(ndb.Model):
  name = ndb.StringProperty(required=True)
  value = ndb.StringProperty(required=True)


def get_property(name, default=None):
  # First check the instance cache. 
  # If it is in instance cache, add to memcache.
  # If not in instance cache, then check memcache.
  # If not in memcache, run a Datastore query to populate memcache.
  global settings
  if name in settings: 
    if settings[name]:
      memcache.add(key=name, value=settings[name], namespace='settings')
      return settings[name]
  value = memcache.get(name, namespace='settings')
  if value is not None:
    return value
  else:
    qry = Config.query()
    results = qry.fetch(50)
    retval = None
    for r in results:
      memcache.add(key=r.name, value=r.value, namespace='settings')
      if r.name == name: retval = r.value
    if retval:
      return retval
    else:
      return default

def initialize_config():
  # Initializes the config in the Datastore with a single item
  # so that we can access via the Admin Console Datastore Viewer
  # to add more entries manually.
  qry = Config.query()
  results = qry.fetch(1)
  if not results:
      config = Config(name="config", value="initialized")
      config.put()


