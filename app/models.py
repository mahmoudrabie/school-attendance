import datetime

from pytz import timezone
from pytz import utc

from google.appengine.ext import ndb


class Student(ndb.Model):
  first_name = ndb.StringProperty(required=True)
  last_name = ndb.StringProperty(required=True)


class Class(ndb.Model):
  name = ndb.StringProperty(required=True)
  enrolled = ndb.KeyProperty(repeated=True)
  default_hours = ndb.FloatProperty(default=None)
  timezone = ndb.StringProperty(default='US/Pacific')

  def date_is_today(self, date):
    naive_time = datetime.datetime.now()
    utc_time = utc.localize(naive_time)
    tz = timezone(self.timezone)
    local_time = utc_time.astimezone(tz)
    return local_time.date().toordinal() == date


class StudentPresent(ndb.Model):
  student = ndb.KeyProperty(required=True)
  hours = ndb.FloatProperty(default=None)


class Attendance(ndb.Model):
  # Attendance objects have a Class as their ancestor.
  # Their key is a representation of the date of the class.
  # attendance_key = ndb.Key('Class', int(class_id), 'Attendance', int(date_ordinal))
  attending = ndb.StructuredProperty(StudentPresent, repeated=True)

  @classmethod
  def is_present(self, student_key):
    for student_present in attending:
      if student_present.student == student_key:
        return True
    return False
