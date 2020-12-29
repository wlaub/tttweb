from django import template
import markdown

register = template.Library()

@register.filter(name='is_expanded')
def is_expanded(value):
    return value.ancestor or value.selected

@register.filter(name='render_markdown')
def render_markdown(value):
    md = markdown.Markdown(extensions=['extra', 'sane_lists', 'nl2br'])
    return md.convert(value)


