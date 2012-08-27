from google.appengine.ext import ndb

class Student(ndb.Model):
  first_name = ndb.StringProperty()
  last_name = ndb.StringProperty()

class Class(ndb.Model):
  name = ndb.StringProperty()
  enrolled = ndb.KeyProperty(repeated=True)

class Attendance(ndb.Model):
  attending = ndb.KeyProperty(repeated=True)
