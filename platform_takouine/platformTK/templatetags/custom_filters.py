# myapp/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, "0")



@register.filter
def capitalize_first(value):
    if isinstance(value, str):
        return value.capitalize()
    return value