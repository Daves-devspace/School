from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter(name='get_item')
def get_item(dictionary, key):
    try:
        return dictionary[key]
    except KeyError:
        return None
