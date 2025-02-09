# apps/Manage/validators.py
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

custom_username_validator = RegexValidator(
    r'^[\/\w@.+_-]+\Z',  # Explicitly includes forward slash
    _("Enter a valid username. May contain letters, numbers, and @/./+/-/_// characters."),
    code='invalid_username'
)