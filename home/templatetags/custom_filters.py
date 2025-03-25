from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary[key]

@register.filter
def dict_items(dictionary):
    return dictionary.items()

@register.filter
def int_range(value):
    """Generates a range of integers."""
    try:
        return range(int(value))
    except (ValueError, TypeError):
        return

@register.filter
def add(value, arg):
    return value + arg