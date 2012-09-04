# todo
# reporting interface - cron job to export to a spreadsheet
# http://code.google.com/p/gdata-python-client/source/browse/#hg%2Fsamples%2Foauth%2Foauth_on_appengine%253Fstate%253Dclosed
# Use closure to do ajax instead of attend post
# check how UI looks in web browser emulating android
# get my spare android running to test
# figure out how to handle login on android
# set up short cut on desktop, android
# load data to prod system from ~/appengine/python_apps/sfschoolhouse.db
# need to ensure accessed as attendance.sfschoolhouse.org if logged in as a schoolhouse.org user
# allow anyone to test Music, Football, etc. on appspot.com
# track number of hours per day - total num hours single field
# unit tests, integration tests
# code readability
# Handle Sunset ecare:
#  - List of parents working
#  - Need to have max attendance, which is dynamic depending on parents working
#  - Parents work every other week, so complex schedules.
#  - Kids need to be marked if parent attended, since different price
# allow admins to change attendance for other days
# use provisioning API to get groups (e.g. classes)
# check ereporter is working
# check what happens if call attend with date in future or past (should be an error)
# is there a way to scan in paper to the system

import os
import datetime
import logging

from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import namespace_manager

from models import Attendance
from models import Class
from models import Student
from models import StudentPresent

from pytz import timezone
from pytz import utc

from google.appengine.dist import use_library
use_library('django', '1.2')

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


class Classes(webapp.RequestHandler):

  def get(self):
    authz = Authorize()
    if not authz.authorize():
      self.error(403)
      return
    query = Class.query()
    # Max classes that can be handled is 50 per school
    classes = query.fetch(50)
    for the_class in classes:
      the_class.id = the_class.key.id()
    template_values = { 'classes': classes,
                        'username': authz.get_name(),
                        'logout': users.create_logout_url("/") }
    path = os.path.join(os.path.dirname(__file__), 'templates/classes.html')
    self.response.out.write(template.render(path, template_values))


class Students(webapp.RequestHandler):

  def today_as_ordinal(self, the_timezone):
    naive_time = datetime.datetime.now()
    utc_time = utc.localize(naive_time)
    tz = timezone(the_timezone)
    local_time = utc_time.astimezone(tz)
    return local_time.date().toordinal()

  def get(self):
    user = users.get_current_user()
    authz = Authorize()
    if not authz.authorize():
      self.error(403)
      return
    class_id = self.request.get('class_id')
    class_key = ndb.Key('Class', int(class_id))
    the_class = class_key.get()
    the_class.id = the_class.key.id()
    date_ordinal = self.request.get('date')
    errmsg = self.request.get('errmsg')
    today_as_ordinal = self.today_as_ordinal(the_class.timezone)
    if not date_ordinal:
      date_ordinal = today_as_ordinal
    if int(date_ordinal) == today_as_ordinal:
      today = True
    else:
      today = False
    date_struct = datetime.date.fromordinal(int(date_ordinal))
    attendance_key = ndb.Key('Class', int(class_id), 'Attendance', int(date_ordinal))
    attendance = attendance_key.get()
    students = ndb.get_multi(the_class.enrolled)
    students.sort(key= lambda x: x.first_name, reverse=False)
    for student in students:
      student.present = False
      student.hours = the_class.default_hours
      student.id = student.key.id()
      if attendance:
        for student_present in attendance.attending:
          if student_present.student == student.key:
            student.present = True
            student.hours = student_present.hours
            break
    template_values = { 'students': students,
                        'date_ordinal': date_ordinal,
                        'today': today,
                        'class': the_class,
                        'date_struct': date_struct,
                        'username': authz.get_name(),
                        'errmsg': errmsg }
    path = os.path.join(os.path.dirname(__file__), 'templates/students.html')
    self.response.out.write(template.render(path, template_values))


class Attend(webapp.RequestHandler):

  def today_as_ordinal(self, the_timezone):
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
    user = users.get_current_user()
    authz = Authorize()
    if not authz.authorize():
      self.error(403)
      return
    yes = self.request.get('yes')
    class_id = self.request.get('class_id')
    student_id = self.request.get('student_id')
    student_key = ndb.Key('Student', int(student_id))
    student = student_key.get()
    date_ordinal = self.request.get('date')
    date_struct = datetime.date.fromordinal(int(date_ordinal))
    class_key = ndb.Key('Class', int(class_id))
    the_class = class_key.get()
    hours = self.request.get('hours')
    today_as_ordinal = self.today_as_ordinal(the_class.timezone)
    if int(date_ordinal) == today_as_ordinal:
      attendance_key = ndb.Key('Class', int(class_id), 'Attendance', int(date_ordinal))
      attendance = attendance_key.get()
      attendance_already_exists = False
      try:
        if attendance:
          attendance_already_exists = True
          if yes:
            self.add_student(student_key, hours, attendance.attending)
          else:
            self.remove_student(student_key, attendance.attending)
        else:
          if yes:
            attendance = Attendance(key=attendance_key, attending=[])
            self.add_student(student_key, hours, attendance.attending)
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
    if attendance.attending:
      attendance.put()
    elif attendance_already_exists:
      attendance_key.delete()
    self.redirect('/students?class_id=%s&date=%s' % (class_id, date_ordinal))

class Logout(webapp.RequestHandler):
  def get(self):
    self.response.out.write('<a href="' + users.create_logout_url("/") + '">logout</a>')


application = webapp.WSGIApplication(
  [('/classes', Classes), ('/students', Students), ('/attend', Attend), ('/logout', Logout),],
  debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
