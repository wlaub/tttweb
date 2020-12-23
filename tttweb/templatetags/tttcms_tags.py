from django import template

register = template.Library()

@register.filter(name='is_expanded')
def is_expanded(value):
    return value.ancestor or value.selected


