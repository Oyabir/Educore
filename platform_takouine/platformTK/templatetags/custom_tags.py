from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter
def in_group(user, group_name):
    """Check if the user belongs to a given group."""
    return user.groups.filter(name=group_name).exists()
