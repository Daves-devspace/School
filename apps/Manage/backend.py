import re

from django.contrib.auth.backends import ModelBackend

from apps.teachers.models import Teacher

import logging

logger = logging.getLogger(__name__)



class StaffNumberAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username and re.match(r'^TCH/\d{3}/\d{2}$', username):  # Check if the username matches the staff_number format
            try:
                teacher = Teacher.objects.get(staff_number=username)  # Get the teacher with the staff_number
                user = teacher.user  # Assuming each teacher is linked to a user
                if user.check_password(password):  # Check the password
                    logger.info(f"Successful login for teacher: {username}")
                    return user  # Return the user object if login is successful
                else:
                    logger.warning(f"Failed login attempt for teacher: {username} - Incorrect password")
            except Teacher.DoesNotExist:
                logger.error(f"Teacher with staff_number {username} does not exist.")
                return None  # Fail login if teacher does not exist

        # Fallback to default behavior for other user types (e.g., admin)
        return super().authenticate(request, username=username, password=password, **kwargs)


