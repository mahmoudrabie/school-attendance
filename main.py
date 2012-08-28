# todo
# reporting interface - cron job to export to a spreadsheet
# http://code.google.com/p/gdata-python-client/source/browse/#hg%2Fsamples%2Foauth%2Foauth_on_appengine%253Fstate%253Dclosed
# Use closure to do ajax instead of attend post
# check how UI looks in web browser emulating android
# get my spare android running to test
# figure out how to handle login on android
# set up short cut on desktop, android
# handle time zones correct (from account api?)
# load data to prod system from ~/appengine/python_apps/sfschoolhouse.db
# prod and dev versions
# need to ensure accessed as attendance.sfschoolhouse.org if logged in as a schoolhouse.org user
# security check that user login domain matches namespace
# allow anyone to test Music, Football, etc. on appspot.com
# track number of hours per day - total num hours single field
# unit tests, integration tests
# code readability

import os
import datetime
import logging

from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import users

from models import Attendance
from models import Class
from models import Student

from google.appengine.dist import use_library
use_library('django', '1.2')


class Classes(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    query = Class.query()
    # TODO: handle school with >20 classes
    classes = query.fetch(20)
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
    class_id = self.request.get('class_id')
    date_ordinal = self.request.get('date')
    if not date_ordinal:
      # TODO handle time zone conversions needed because appengine dates are in GMT
      date_ordinal = datetime.date.today().toordinal()
    date_struct = datetime.date.fromordinal(int(date_ordinal))
    if date_struct == datetime.datetime.today().date():
      today = True
    else:
      today = False
    class_key = ndb.Key('Class', int(class_id))
    the_class = class_key.get()
    the_class.id = the_class.key.id()
    attendance_key = ndb.Key('Class', int(class_id), 'Attendance', int(date_ordinal))
    attendance = attendance_key.get()
    students = ndb.get_multi(the_class.enrolled)
    students.sort(key= lambda x: x.first_name, reverse=False)
    for student in students:
      student.id = student.key.id()
      if attendance:
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


class LoadData(webapp.RequestHandler):
  def get(self):
    students = []
    student_list = []
    for name in students:
      first_name, last_name = name.split()
      student = Student(first_name=first_name, last_name=last_name)
      student_key = student.put()
      student_list.append(student_key)
    the_class = Class(name='K-2 2012-13', enrolled=student_list)
    the_class.put()
    self.response.out.write('done')


application = webapp.WSGIApplication(
  [('/classes', Classes), ('/students', Students), ('/attend', Attend), 
   ('/loaddata', LoadData),],
  debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
