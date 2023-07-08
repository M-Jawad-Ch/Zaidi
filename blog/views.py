from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from .models import Article, Category

from datetime import datetime
from json import loads, dumps


def index(req: HttpRequest):
    articles = Article.objects.all().order_by('-timestamp')[:12]
    categories = Category.objects.all()

    if not articles:
        return render(req, 'mtc.html')

    data = {}

    data['categories'] = [{'name': category.name,
                           'slug': category.slug} for category in categories]

    data['top_story'] = {
        'title': articles[0].title if articles else '',
        'desc': loads(articles[0].body)[0]['text'][0],
        'slug': articles[0].slug
    }

    data['articles'] = [
        {
            'title': article.title,
            'date': article.date,
            'slug': article.slug,
            'previews': [dumps(text) for text in loads(article.body)[0]['text'][:2]]
        } for article in articles[1:12]
    ]

    return render(req, 'index.html', data)


async def get_post(req: HttpRequest, slug: str):

    data = await Article.objects.aget(slug=slug)

    return render(req, 'post.html', {
        'title': data.title,
        'content': loads(data.body),
        'date': data.date
    })


async def get_post_via_category(req: HttpRequest, category: str, post: str):
    data = await Article.objects.aget(slug=post)

    return render(req, 'post.html', {
        'title': data.title,
        'content': loads(data.body),
        'date': data.date
    })


def get_category(req: HttpRequest, slug: str):
    articles = Article.objects.filter(
        category=slug).all().order_by('-timestamp')
    category = Category.objects.get(pk=slug)
    return render(req, 'category.html', {
        'category': {
            'slug': category.slug,
            'title': category.name
        },
        'articles': [{
            'title': article.title,
            'date': article.date,
            'slug': article.slug
        } for article in articles]})


def return_404(req: HttpRequest, *args, **kwargs):
    resp = HttpResponse()
    resp.status_code = 404
    return resp
