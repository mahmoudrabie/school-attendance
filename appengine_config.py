from google.appengine.api import namespace_manager

from google.appengine.dist import use_library
use_library('django', '1.2')

# Called only if the current namespace is not set.
def namespace_manager_default_namespace_for_request():
  # The returned string will be used as the Google Apps domain.
  return namespace_manager.google_apps_namespace()

