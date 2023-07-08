from django import template
register = template.Library()


@register.simple_tag()
def slice(articles: list, idxs: str):
    a, b = idxs.split(':')
    return articles[a:b]
