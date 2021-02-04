from django import template
from django.utils.http import urlencode
import markdown
import urllib

register = template.Library()

@register.filter(name='is_expanded')
def is_expanded(value):
    return value.ancestor or value.selected

@register.filter(name='render_markdown')
def render_markdown(value):
    if value == None: return ''
    md = markdown.Markdown(extensions=['extra', 'sane_lists', 'nl2br'])
    return md.convert(value)

@register.filter(name='page_range')
def page_range(page_obj):
    return range(1,100)
    return range(1,page_obj.paginator.num_pages+1)

@register.simple_tag
def format_querystring(base_query, *args, **kwargs):
    """
    args defines keys that are lists to extend
    kwargs is values to add
    base_query is a dictionary of querystring params
    {
       name:[values],

    }
    and **kwargs is a set of extra values to be merged into the query
    return the querystring
    name=value,value,value&name=value,value,value etc
    """

    query = {}
    for key, value in base_query.items():
        query[key] = urllib.parse.unquote(value).split(',')

    for key, value in kwargs.items():
        if value == None:
            query.pop(key, None)
        elif not key in query.keys() or not key in args:
            query[key] = [str(value)]
        elif not value in query[key]:
            query[key].append(str(value))

    result = []
    for key, value in query.items():
        result.append((f'{key}',f'{",".join(value)}'))
    result = urlencode(result)
    if len(result) == 0: return ''
    return '?' + result

