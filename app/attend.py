import datetime
import logging
import webapp2

from google.appengine.ext import ndb
from google.appengine.api import users

from authorize import Authorize
from models import Attendance
from models import StudentPresent

from pytz import timezone
from pytz import utc


class Attend(webapp2.RequestHandler):

  @staticmethod
  def today_as_ordinal(the_timezone):
    naive_time = datetime.datetime.now()
    utc_time = utc.localize(naive_time)
    tz = timezone(the_timezone)
    local_time = utc_time.astimezone(tz)
    return local_time.date().toordinal()

  def add_student(self, student_key, hours, attending_list):
    student_already_present = False
    if attending_list:
      for student_present in attending_list:
        if student_present.student == student_key:
          student_already_present = True
          break
    if not student_already_present or not attending_list:
      if hours:
        hours = float(hours)
      else:
        hours = None
      attending_list.append(StudentPresent(student=student_key, hours=hours))

  def remove_student(self, student_key, attending_list):
    if attending_list:
      for student_present in attending_list:
        if student_present.student == student_key:
          attending_list.remove(student_present)
          break

  def get(self):
    # authorize web requests
    user = users.get_current_user()
    authz = Authorize()
    if not authz.authorize():
      self.error(403)
      return
    # get the form input
    yes = int(self.request.get('yes'))
    class_id = self.request.get('class_id')
    student_id = self.request.get('student_id')
    if student_id:
      student_key = ndb.Key('Student', int(student_id))
      student = student_key.get()
    date_ordinal = self.request.get('date')
    date_struct = datetime.date.fromordinal(int(date_ordinal))
    class_key = ndb.Key('Class', int(class_id))
    the_class = class_key.get()
    hours = self.request.get('hours')
    today_as_ordinal = self.today_as_ordinal(the_class.timezone)
    # can only edit attendance for today
    attendance = None
    if int(date_ordinal) == today_as_ordinal:
      attendance_key = ndb.Key('Class', int(class_id), 'Attendance', int(date_ordinal))
      attendance = attendance_key.get()
      attendance_already_exists = False
      try:
        if attendance:
          attendance_already_exists = True
          if yes:
            if student_id:
              self.add_student(student_key, hours, attendance.attending)
            else:
              students = ndb.get_multi(the_class.enrolled)
              for student in students:
                self.add_student(student.key, hours, attendance.attending)
          else:
            self.remove_student(student_key, attendance.attending)
        else:
          if yes:
            attendance = Attendance(key=attendance_key, attending=[])
            if student_id:
              self.add_student(student_key, hours, attendance.attending)
            else:
              students = ndb.get_multi(the_class.enrolled)
              for student in students:
                self.add_student(student.key, hours, attendance.attending)

      except ValueError:
        # hours was not a float
        self.redirect('/students?class_id=%s&date=%s&errmsg=Invalid%%20value%%20for%%20hours' % (class_id, date_ordinal))
        return
    if attendance:
      if yes:
        status = "present"
      else:
        status = "absent"
      logging.info('Change by %s: %s %s marked as %s for %s (hours: %s)' % 
                   (authz.get_name(), student.first_name, student.last_name, status, the_class.name, hours))
      attendance.put()
    elif attendance_already_exists:
      attendance_key.delete()
    self.redirect('/students?class_id=%s&date=%s' % (class_id, date_ordinal))


app = webapp2.WSGIApplication([('/attend', Attend),], debug=True)

