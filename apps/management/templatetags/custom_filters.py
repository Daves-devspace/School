from django import template

register = template.Library()

@register.filter
def get_day_lessons(timetable_data, day):
    # Return the lessons for the given day
    return timetable_data.get(day, [])
@register.filter
def dict_get(dictionary, key):
    return dictionary.get(key, [])


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, None) if isinstance(dictionary, dict) else None
