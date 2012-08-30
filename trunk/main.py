# todo
# reporting interface - cron job to export to a spreadsheet
# http://code.google.com/p/gdata-python-client/source/browse/#hg%2Fsamples%2Foauth%2Foauth_on_appengine%253Fstate%253Dclosed
# Use closure to do ajax instead of attend post
# check how UI looks in web browser emulating android
# get my spare android running to test
# figure out how to handle login on android
# set up short cut on desktop, android
# test time zones using remote api
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
from pytz import timezone

from google.appengine.dist import use_library
use_library('django', '1.2')


class Classes(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    name, user_domain = user.email()
    namespace = namespace_manager.get_namespace()
    if namespace and namespace != user_domain:
      self.error(403)
      return
    query = Class.query()
    # Max classes that can be handled is 50 per school
    classes = query.fetch(50)
    for the_class in classes:
      the_class.id = the_class.key.id()
    template_values = { 'classes': classes,
                        'username': user.nickname(),
                        'logout': users.create_logout_url("/") }
    path = os.path.join(os.path.dirname(__file__), 'templates/classes.html')
    self.response.out.write(template.render(path, template_values))


class Students(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    name, user_domain = user.email()
    if namespace_manager.get_namespace() != user_domain:
      self.error(403)
      return
    class_id = self.request.get('class_id')
    class_key = ndb.Key('Class', int(class_id))
    the_class = class_key.get()
    the_class.id = the_class.key.id()
    date_ordinal = self.request.get('date')
    if not date_ordinal:
      utc_time = datetime.datetime.now()
      tz = the_class.timezone
      local_time = utc_time.astimezone(tz)
      date_ordinal = localtime.date().toordinal()
    date_struct = datetime.date.fromordinal(int(date_ordinal))
    if date_struct == datetime.datetime.today().date():
      today = True
    else:
      today = False
    attendance_key = ndb.Key('Class', int(class_id), 'Attendance', int(date_ordinal))
    attendance = attendance_key.get()
    students = ndb.get_multi(the_class.enrolled)
    students.sort(key= lambda x: x.first_name, reverse=False)
    for student in students:
      student.id = student.key.id()
      if attendance:
        # need to change this... since attendance is no a data structure
        if student.key in attendance.attending:
          student.present = True
        else:
          student.present = False
      else:
        student.present = False
    template_values = { 'students': students,
                        'date_ordinal': date_ordinal,
                        'today': today,
                        'class': the_class,
                        'date_struct': date_struct,
                        'username': user.nickname(),
                        'logout': users.create_logout_url("/") }
    path = os.path.join(os.path.dirname(__file__), 'templates/students.html')
    self.response.out.write(template.render(path, template_values))


class Attend(webapp.RequestHandler):
  def post(self):
    user = users.get_current_user()
    name, user_domain = user.email()
    if namespace_manager.get_namespace() != user_domain:
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
    # TODO: allow admins to change attendance for other days
    if date_struct == datetime.datetime.today().date():
      attendance_key = ndb.Key('Class', int(class_id), 'Attendance', int(date_ordinal))
      attendance = attendance_key.get()
      if attendance:
        if yes and student_key not in attendance.attending:
          attendance.attending.append(student_key)
        if not yes and student_key in attendance.attending:
          attendance.attending.remove(student_key)
      else:
        if yes:
          attendance = Attendance(key=attendance_key, attending=[student_key])
    if attendance:
      if yes:
        status = "present"
      else:
        status = "absent"
      logging.info('Change by %s: %s %s marked as %s for %s' % 
                   (user.nickname(), student.first_name, student.last_name, status, the_class.name))
      attendance.put()
    self.redirect('/students?class_id=%s&date=%s' % (class_id, date_ordinal))


application = webapp.WSGIApplication(
  [('/classes', Classes), ('/students', Students), ('/attend', Attend),],
  debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
