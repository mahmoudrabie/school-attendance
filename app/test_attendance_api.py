# see 
# http://stackoverflow.com/questions/20384743/how-to-unit-test-google-cloud-endpoints
# http://stackoverflow.com/questions/19117695/how-do-i-test-cloud-endpoints-with-oauth-on-devserver
# http://blog.redgreenrefactor.eu/post/69835849322/developer-diaries-testing-google-app-engine-endpoints

# but get error from #1
#   File "/home/jlowry/google-cloud-sdk/platform/google_appengine/lib/webob-1.2.3/webob/response.py", line 361, in _body__get
#     % (self.content_length, len(body))
# AssertionError: Content-Length is different from actual app_iter length (512!=65)
# When comment out this assertion, then get error:
#   File "/usr/lib/python2.7/dist-packages/webtest/app.py", line 1111, in _check_status
#     res.body))
# AppError: Bad response: 401 Unauthorized (not 200 OK or 3xx redirect for http://localhost/_ah/spi/AttendanceAPI.post_attendance)
# {"state": "APPLICATION_ERROR", "error_message": "Invalid token."}


import endpoints
import unittest
import webtest
import webapp2

from google.appengine.ext import ndb
from google.appengine.ext import testbed
from google.appengine.api import users

from attendance_api import AttendanceAPI
from models import Class  
from models import Student  


class AttendTestCase(unittest.TestCase):

  def setUp(self):
    app = endpoints.api_server([AttendanceAPI], restricted=False)
    self.testapp = webtest.TestApp(app)
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_datastore_v3_stub()
    self.testbed.init_user_stub()
    self.testbed.init_memcache_stub()
    self.testbed.setup_env(
      USER_EMAIL = 'test@gmail.com',
      USER_ID = '123',
      USER_IS_ADMIN = '1',
      overwrite = True,
      current_version_id='testbed.version')
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
    self.today_as_ordinal = AttendanceAPI.today_as_ordinal(self.timezone)

  def tearDown(self):
     self.testbed.deactivate()

  def testAttendAddFirstStudent(self):
    params = {'classname': self.class_key.id(), 
              'student': self.student_key.id(), 
              'attended': True, 
              'date': self.today_as_ordinal}
    response = self.testapp.post_json('/_ah/spi/AttendanceAPI.post_attendance', params)
    self.assertEqual(response.status_int, 200)
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
