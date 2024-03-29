
from google.appengine.ext import ndb


class Student(ndb.Model):
  first_name = ndb.StringProperty(required=True)
  last_name = ndb.StringProperty(required=True)


class Class(ndb.Model):
  name = ndb.StringProperty(required=True)
  enrolled = ndb.KeyProperty(repeated=True)
  default_hours = ndb.FloatProperty(default=None)
  timezone = ndb.StringProperty(default='US/Pacific')


class StudentPresent(ndb.Model):
  student = ndb.KeyProperty(required=True)
  hours = ndb.FloatProperty(default=None)


class Attendance(ndb.Model):
  # Attendance objects have a Class as their ancestor.
  # Their key is a representation of the date of the class.
  # attendance_key = ndb.Key('Class', int(class_id), 'Attendance', int(date_ordinal))
  attending = ndb.StructuredProperty(StudentPresent, repeated=True)

