import unittest
import webtest
import webapp2

from google.appengine.ext import ndb
from google.appengine.ext import testbed
from google.appengine.api import users

from attend import Attend
from models import Class  
from models import Student  


class AttendTestCase(unittest.TestCase):

  def setUp(self):
    app = webapp2.WSGIApplication([('/attend', Attend)])
    self.testapp = webtest.TestApp(app)
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_datastore_v3_stub()
    self.testbed.init_user_stub()
    self.testbed.init_memcache_stub()
    self.testbed.setup_env(
      USER_EMAIL = 'test@example.com',
      USER_ID = '123',
      USER_IS_ADMIN = '1',
      overwrite = True)
    self.createClassAndStudents()
    
  def createClassAndStudents(self):
    c = Class()
    c.name = 'Test Class'
    self.class_key = c.put()
    c = self.class_key.get()
    self.timezone = c.timezone
    s = Student()
    s.first_name = 'Joe'
    s.last_name = 'Smith'
    self.student_key = s.put()
    c.enrolled.append(self.student_key)
    c.put()
    # TODO: fix this to use a known date, since could potentially have problems if run in different timezone to default
    self.today_as_ordinal = Attend.today_as_ordinal(self.timezone)

  def tearDown(self):
     self.testbed.deactivate()

  def testAttendAddFirstStudent(self):
    params = {'class_id': self.class_key.id(), 
              'student_id': self.student_key.id(), 
              'yes': 1, 'date': self.today_as_ordinal}
    response = self.testapp.get('/attend', params)
    self.assertEqual(response.status_int, 302)
    query = Class.query()
    results = query.fetch(2)
    self.assertEqual(1, len(results))
    self.assertEqual('Test Class', results[0].name)
    attendance_key = ndb.Key('Class', self.class_key.id(), 'Attendance', self.today_as_ordinal)
    attendance = attendance_key.get()
    self.assertEqual(1, len(attendance.attending))
    student_key = attendance.attending[0].student
    student = student_key.get()
    self.assertEqual('Joe', student.first_name)
    self.assertEqual('Smith', student.last_name)

if __name__ == '__main__':
    unittest.main()
