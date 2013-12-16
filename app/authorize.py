from google.appengine.api import users
from google.appengine.api import namespace_manager


class Authorize():

  def __init__(self):
    self.user = users.get_current_user()

  def authorize(self):
    name, user_domain = self.user.email().split('@')
    namespace = namespace_manager.get_namespace()
    if not namespace:
      # namespace will be an empty string if not an apps domain
      # can be used with the test data
      return True
    elif namespace == user_domain:
      # if an apps domain, then the user must be a member of the domain
      return True
    else:
      return False

  def get_name(self):
    return self.user.nickname()


