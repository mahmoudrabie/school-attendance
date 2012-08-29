from google.appengine.ext import ndb

class Student(ndb.Model):
  first_name = ndb.StringProperty()
  last_name = ndb.StringProperty()

class Class(ndb.Model):
  name = ndb.StringProperty()
  enrolled = ndb.KeyProperty(repeated=True)
  default_hours = ndb.FloatProperty(default=None)
  timezone = ndb.StringProperty(default='US/Pacific')

class Attendance(ndb.Model):
  attending = ndb.KeyProperty(repeated=True)
  hours = ndb.FloatProperty()
