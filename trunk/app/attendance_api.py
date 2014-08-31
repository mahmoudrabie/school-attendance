"""Attendance API implemented using Google Cloud Endpoints."""

import datetime
import endpoints
import logging
import os

from google.appengine.api import namespace_manager
from google.appengine.ext import ndb

from protorpc import messages
from protorpc import message_types
from protorpc import remote

from pytz import timezone
from pytz import utc

from models import Attendance
from models import StudentPresent


WEB_CLIENT_ID = 'replace this with your web client application ID'
ALLOWED_CLIENT_IDS = [WEB_CLIENT_ID, endpoints.API_EXPLORER_CLIENT_ID]

package = 'Attendance'


class AttendanceRecord(messages.Message):
  """Message for posting attendance for a class on a specific date."""
  classname = messages.IntegerField(1, required=True)
  student = messages.IntegerField(2, required=True)
  attended = messages.BooleanField(3, required=True)
  date = messages.IntegerField(4, required=True)


@endpoints.api(name='attendance', version='v1', 
               allowed_client_ids=ALLOWED_CLIENT_IDS,
               scopes=[endpoints.EMAIL_SCOPE])
class AttendanceAPI(remote.Service):
  """Attendance API v1."""

  @staticmethod
  def today_as_ordinal(class_timezone):
    naive_time = datetime.datetime.now()
    utc_time = utc.localize(naive_time)
    tz = timezone(class_timezone)
    local_time = utc_time.astimezone(tz)
    return local_time.date().toordinal()

  @staticmethod
  def is_present(attendance, student_key):
    for student_present in attendance.attending:
      if student_present.student == student_key:
        return True
    return False

  @staticmethod
  def is_enrolled(classname, student_key):
    for student_enrolled in classname.enrolled:
      if student_enrolled == student_key:
        return True
    return False

  @endpoints.method(AttendanceRecord, message_types.VoidMessage, path='post')
  def post_attendance(self, request):
    """Register whether or not a single student attended class.
    
    Arguments
      request: an AttendanceRecord message.

    Returns:
      An instance of message_types.VoidMessage.
    """
    current_user = endpoints.get_current_user()
    app_id = os.environ['APPLICATION_ID']
    if app_id.startswith('dev~') or app_id == 'testbed-test':
      email = 'test@gmail.com'
    else:
      if current_user is None:
        raise endpoints.UnauthorizedException('Invalid token.')
      email = current_user.email()

    domain = email.split('@')[1]
    if domain == 'gmail.com': domain = ''
    namespace_manager.set_namespace(domain)

    student_key = ndb.Key('Student', request.student)
    student = student_key.get()
    if not student:
      raise endpoints.BadRequestException('No student: %s' % request.student)
    classname_key = ndb.Key('Class', request.classname)
    classname = classname_key.get()
    if not classname:
      raise endpoints.BadRequestException('No class: %s' % request.classname)

    if not AttendanceAPI.is_enrolled(classname, student_key):
      raise endpoints.BadRequestException(
        'Student %s is not enrolled in class %s' % (student_key, classname.name))

    today = AttendanceAPI.today_as_ordinal(classname.timezone)
    if request.date != today:
      raise endpoints.BadRequestException('Date must be %s, but is: %s' 
                                          % (today, request.date))

    logging.info('Updating class: %s student: %s date: %s user: %s attend: %s' % 
                 (classname.name, request.student, request.date, 
                  email, request.attended))

    attendance_key = ndb.Key('Class', request.classname, 
                             'Attendance', request.date)
    attendance = attendance_key.get()
    if not attendance:
      attendance = Attendance(key=attendance_key, attending=[])
    if request.attended:
      if not AttendanceAPI.is_present(attendance, student_key):
        attendance.attending.append(StudentPresent(student=student_key))
        attendance.put()
    else:
      try:
        attendance.attending.remove(student_present)
        attendance.put()
      except ValueError:
        pass
    return message_types.VoidMessage()


application = endpoints.api_server([AttendanceAPI])
