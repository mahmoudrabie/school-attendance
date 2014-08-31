#!/usr/bin/python

import argparse
import os
import sys

home = os.environ['HOME']
sys.path.append(home + '/google-cloud-sdk/platform/google_appengine')
sys.path.append(home + '/google-cloud-sdk/platform/google_appengine/lib/fancy_urllib')
sys.path.append('./app')

from google.appengine.api import namespace_manager
from google.appengine.ext.remote_api import remote_api_stub

from models import Student
from models import Class

import getpass

def auth_func():
  return (raw_input('Username:'), getpass.getpass('Password:'))

def add_class(class_name):
  c = Class(name=class_name)
  k = c.put()
  return k

def add_student(first, last):
  s = Student(first_name=first, last_name=last)
  k = s.put()
  return k

def add_student_to_class(class_key, student_key):
  c = class_key.get()
  c.enrolled.append(student_key)
  c.put()

def get_student(first, last):
  qry = Student.query().filter(Student.first_name == first, Student.last_name == last)
  return qry.fetch(1)

def get_class(class_name):
  qry = Class.query().filter(Class.name == class_name)
  return qry.fetch(1)

def student_in_class(class_key, student_key):
  c = class_key.get()
  if student_key in c.enrolled:
    return True
  return False

def main():
  parser = argparse.ArgumentParser(description='Add students and classes to school attendance app.')
  parser.add_argument('--school', required=True,
                   help='Namespace representing the school.')
  parser.add_argument('--first', required=True,
                   help='First name of student.')
  parser.add_argument('--last', required=True,
                   help='Last name of student.')
  parser.add_argument('--class_name', required=True,
                   help='Name of class.')
  args = parser.parse_args()
  remote_api_stub.ConfigureRemoteApi('s~school-attendance', '/_ah/remote_api', 
                                     auth_func, 'school-attendance.appspot.com', 
                                     save_cookies=True)
  namespace_manager.set_namespace(args.school)
  c = get_class(args.class_name)
  if c:
    print 'Class found: %s' % c[0]
    class_key = c[0].key
  else:
    class_key = add_class(args.class_name)

  s = get_student(args.first, args.last)
  if s:
    print 'Student found: %s' % s[0]
    student_key = s[0].key
  else:
    student_key = add_student(args.first, args.last)

  result = student_in_class(class_key, student_key)
  if not result:
    add_student_to_class(class_key, student_key)

if __name__ == "__main__":
    main()

