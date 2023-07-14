from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from .models import Article, Category

from json import loads, dumps


def index(req: HttpRequest):
    articles = Article.objects.all().order_by('-timestamp')[:12]
    categories = Category.objects.all()

    if not articles:
        return render(req, 'mtc.html')

    data = {}

    data['categories'] = [{
        'name': category.name,
        'slug': category.slug
    } for category in categories]

    data['top_story'] = {
        'title': articles[0].title if articles else '',
        'desc': articles[0].body,
        'slug': articles[0].slug
    }

    data['articles'] = [
        {
            'title': article.title,
            'date': article.date,
            'slug': article.slug,
            'previews': article.body
        } for article in articles[1:12]
    ]

    return render(req, 'index.html', data)

def get_post_via_category(req: HttpRequest, post: str):
    data = Article.objects.get(slug=post)
    
    recent = [ article for article in Article.objects.all().order_by('-timestamp') if article.image and article.slug != data.slug][:4]

    categories = Category.objects.all()

    return render(req, 'post.html', {
        'title': data.title,
        'content': data.body,
        'date': data.date,
        'image_url': data.image.image.url if data.image else None,

        'categories': [{
            'name':category.name,
            'slug': category.slug
        } for category in categories],

        'recent': [{
            'title':article.title,
            'image':article.image.image.url,
            'date':article.date,
            'slug': article.slug,
            'category': article.category.slug
        } for article in recent if article.category],

        'related': [{
            'title':article.title,
            'image':article.image.image.url,
            'date': article.date,
            'slug': article.slug,
            'category': article.category.slug
        } for article in Article.objects.filter(category=data.category).all() if article.slug != data.slug]
    })


def get_category(req: HttpRequest, slug: str):
    articles = Article.objects.filter(category=slug).all().order_by('-timestamp')
    category = Category.objects.get(pk=slug)

    
    return render(req, 'category.html', {
        'category': {
            'slug': category.slug,
            'name': category.name
        },
        'articles': [{
            'slug': article.slug,
            'title': article.title,
            'image': article.image.image.url,
            'date': article.date,
            'desc': article.body
        } for article in articles]
    })


def return_404(req: HttpRequest, *args, **kwargs):
    resp = HttpResponse()
    resp.status_code = 404
    return resp
