from django import template

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """
    Checks if a user belongs to a specific group.
    """
    return user.groups.filter(name=group_name).exists()