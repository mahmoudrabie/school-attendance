"""Attendance API implemented using Google Cloud Endpoints."""

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.ext import ndb

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

  @endpoints.method(AttendanceRecord, message_types.VoidMessage, path='post')
  def post_attendance(self, request):
    """Register whether or not a single student attended class.
    
    Arguments
      request: an AttendanceRecord message.

    Returns:
      An instance of message_types.VoidMessage.
    """
    current_user = endpoints.get_current_user()
    student_key = ndb.Key('Student', request.student)
    classname_key = ndb.Key('Class', request.classname)
    classname = classname_key.get()
    # can only edit attendance for today
    if classname.date_is_today(request.date):
      attendance_key = ndb.Key('Class', request.classname, 
                               'Attendance', request.date)
      attendance = attendance_key.get()
      if not attendance:
        attendance = Attendance(key=attendance_key, attending=[])
      if request.attended:
        if not attendance.is_present(student_key):
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
