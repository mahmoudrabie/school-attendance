import os
import datetime

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
    # TODO: handle case with >20 classes
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
    date = self.request.get('date')
    if date:
      the_date = datetime.datetime.fromtimestamp(int(date))
    else:
      # TODO handle time zone conversions needed because appengine dates are in GMT
      the_date = datetime.datetime.now()
    after = the_date + datetime.timedelta(days=1)
    before = the_date - datetime.timedelta(days=1)
    class_key = ndb.Key('Class', int(class_id))
    the_class = class_key.get()
    the_class.id = the_class.key.id()
    students = ndb.get_multi(the_class.enrolled)
    students.sort(key= lambda x: x.first_name, reverse=False)
    for student in students:
      student.id = student.key.id()
    template_values = { 'students': students,
                        'class': the_class,
                        'the_date': the_date,
                        'before': before,
                        'after': after,
                        'username': user.nickname(),
                        'logout': users.create_logout_url("/") }
    path = os.path.join(os.path.dirname(__file__), 'templates/students.html')
    self.response.out.write(template.render(path, template_values))


class Attend(webapp.RequestHandler):
  def post(self):
    user = users.get_current_user()
    class_id = self.request.get('class_id')
    student_id = self.request.get('student_id')
    student_key = ndb.Key('Student', int(student_id))
    date = self.request.get('date')
    attendance_key = ndb.Key('Class', int(class_id), 'Attendance', int(date))
    attendance = attendance_key.get()
    if attendance:
      if student_key not in attendance.attending:
        attendance.attending.append(student_key)
    else:
      attendance = Attendance(key=attendance_key, attending=[student_key])
      attendance.put()
    self.redirect('/students?class_id=%s&date=%s' % (class_id, date))


class LoadData(webapp.RequestHandler):
  def get(self):
    john = Student(first_name='John', last_name='Lennon')
    paul = Student(first_name='Paul', last_name='McCartney')
    george = Student(first_name='George', last_name='Harrison')
    ringo = Student(first_name='Ringo', last_name='Starr')
    john_key = john.put()
    paul_key = paul.put()
    george_key = george.put()
    ringo_key = ringo.put()
    music = Class(name='Music', enrolled=[john_key, paul_key, george_key, ringo_key])
    music.put()
    self.response.out.write('done')


application = webapp.WSGIApplication(
  [('/classes', Classes), ('/students', Students), ('/attend', Attend), 
   ('/loaddata', LoadData),],
  debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
