# todo
# do not display old classes, students that left
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
# need a web clip for chrome on iphone (or auto-login for safari)
# set up chrome bookmark, web clip on mobiles, desktops. 
import os
import datetime
import logging
import webapp2

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import namespace_manager

from authorize import Authorize
from models import Attendance
from models import Class
from models import Student
from models import StudentPresent

from pytz import timezone
from pytz import utc


class Classes(webapp2.RequestHandler):

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
    school = namespace_manager.google_apps_namespace()
    if not school: school = 'Test school'
    template_values = { 'classes': classes,
                        'school': school,
                        'username': authz.get_name(),
                        'logout': users.create_logout_url("/") }
    path = os.path.join(os.path.dirname(__file__), 'templates/classes.html')
    self.response.out.write(template.render(path, template_values))


class Students(webapp2.RequestHandler):

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
    
    school = namespace_manager.google_apps_namespace()
    if not school: school = 'Test school'
    template_values = { 'students': students,
                        'date_ordinal': date_ordinal,
                        'today': today,
                        'class': the_class,
                        'school': school,
                        'date_struct': date_struct,
                        'username': authz.get_name(),
                        'errmsg': errmsg }
    path = os.path.join(os.path.dirname(__file__), 'templates/students.html')
    self.response.out.write(template.render(path, template_values))


class Logout(webapp2.RequestHandler):
  def get(self):
    self.response.out.write('<a href="' + users.create_logout_url("/") + '">logout</a>')

# TODO: this breaks if we remove someone from enrolled.
# Sadly, there is no deleted field in enrolled.
class Export(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    authz = Authorize()
    if not authz.authorize():
      self.error(403)
      return
    self.response.headers['Content-Type'] = 'text/plain'
    class_id = self.request.get('class_id')
    class_key = ndb.Key('Class', int(class_id))
    the_class = class_key.get()
    enrolled = the_class.enrolled
    all_students = {}
    self.response.out.write(',')
    for student_key in enrolled:
      if student_key not in all_students:
        the_student = student_key.get()
        all_students[student_key] = the_student
        self.response.out.write('%s %s,' % (the_student.first_name, the_student.last_name))
    self.response.out.write('\n')

    qry = Attendance.query(ancestor=class_key).order(Attendance.key)
    attendance = qry.fetch(200)
    for the_attendance in attendance:
      the_attendance_key = the_attendance.key
      date_ordinal = the_attendance_key.id()
      date_struct = datetime.date.fromordinal(int(date_ordinal))
      date_str = date_struct.isoformat()
      self.response.out.write('%s,' % (date_str))
      students = the_attendance.attending
      attending_students = {}
      for student in students:
        student_key = student.student
        attending_students[student_key] = student.hours
      for the_enrolled in enrolled:
        if the_enrolled in attending_students:
          output = attending_students[the_enrolled]
          if not output: output = 1
          self.response.out.write('%s,' % (output))
        else:
          self.response.out.write(',')
      self.response.out.write('\n')
    

app = webapp2.WSGIApplication(
  [('/classes', Classes), ('/students', Students), ('/logout', Logout),
   ('/export', Export),],
  debug=True)

