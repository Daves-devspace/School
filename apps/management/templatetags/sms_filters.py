# templatetags/sms_filters.py
import math

from django import template

register = template.Library()

@register.filter
def ceil(value):
    try:
        return math.ceil(float(value))
    except:
        return 0