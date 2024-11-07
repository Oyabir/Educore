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


@register.filter
def get(attendance_records, student):
    return next((record for record in attendance_records if record.student == student), None)



@register.filter
def zip_lists(list1, list2):
    return zip(list1, list2)