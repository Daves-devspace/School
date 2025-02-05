# apps/teachers/backend.py

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

# class StaffNumberBackend(ModelBackend):
#     def authenticate(self, request, username=None, password=None, **kwargs):
#         try:
#             # Try to authenticate using staff_number as username
#             user = User.objects.get(username=username)
#             if user.check_password(password):
#                 return user
#         except User.DoesNotExist:
#             return None
