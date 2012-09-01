from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.api import namespace_manager
from google.appengine.ext.webapp.util import run_wsgi_app

from models import Student
from models import Class
from models import Attendance
from models import StudentPresent


from google.appengine.dist import use_library
use_library('django', '1.2')


class LoadTest(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    namespace_manager.set_namespace('')
    students = ['John Lennon',
                'Ringo Starr',
                'George Harrison',
                'Paul McCartney',]
    student_list = []
    for name in students:
      first_name, last_name = name.split()
      student = Student(first_name=first_name, last_name=last_name)
      student_key = student.put()
      student_list.append(student_key)
    music = Class(name='Music 101', enrolled=student_list)
    music.put()
    students = ['David Beckham',
                'Lionel Messi',
                'Diego Maradonna',
                'Cristiano Ronaldo',
                'George Best',
                'Wayne Rooney',
                'Zinedine Zidane',]
    student_list = []
    for name in students:
      first_name, last_name = name.split()
      student = Student(first_name=first_name, last_name=last_name)
      student_key = student.put()
      student_list.append(student_key)
    soccer = Class(name='Soccer camp', enrolled=student_list)
    soccer.put()
    students = ['Darth Vader',
                'Gordon Gekko',
                'Auric Goldfinger',
                'Count Dracula', ]
    student_list = []
    for name in students:
      first_name, last_name = name.split()
      student = Student(first_name=first_name, last_name=last_name)
      student_key = student.put()
      student_list.append(student_key)
    detention = Class(name='Detention', enrolled=student_list, default_hours=2)
    detention.put()
    self.response.out.write('done')

application = webapp.WSGIApplication(
  [('/load/test', LoadTest), ],
  debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
    main()
