from django import template
register = template.Library()


@register.filter(name='lookup')
def lookup(dictinary: dict, key: str):
    return dictinary.get(key)
