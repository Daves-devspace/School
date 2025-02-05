import re
from django.core.exceptions import ValidationError

def custom_username_validator(value):
    # Allow TCH/002/25 style usernames (letters, digits, and /)
    if not re.match(r'^[\w/@./+/-]*$', value):  # Allow letters, digits, and @/./+/-/_/
        raise ValidationError("Enter a valid username. This value may contain only letters, numbers, and @/./+/-/_ characters.")
