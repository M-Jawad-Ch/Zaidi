import json

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest
from django.views.decorators.http import require_http_methods
from django.db.utils import IntegrityError
from .models import Article, Category, Contact, Comment, Index


@require_http_methods(['GET'])
def index(req: HttpRequest):
    data = Index.objects.first()
    if not data:
        return render(req, 'mtc.html', {})

    return render(req, 'index.html', {
        'image': data.image.image.url,
        'heading': data.heading,
        'body':  # data.body
        """
Lorem, ipsum dolor sit amet consectetur adipisicing elit. Quia illum sapiente itaque laboriosam omnis minima voluptatibus consectetur eveniet neque dolorum.
Lorem, ipsum dolor sit amet consectetur adipisicing elit. Quia illum sapiente itaque laboriosam omnis minima voluptatibus consectetur eveniet neque dolorum.

"""
    })


@require_http_methods(['GET'])
def get_post(req: HttpRequest, category: str, post: str):
    try:
        data = Article.objects.get(pk=post)
    except Article.DoesNotExist:
        return return_404(req)

    recent = [article for article in Article.objects.all().order_by(
        '-timestamp') if article.image and article.slug != data.slug][:4]

    categories = Category.objects.all()
    comments = Comment.objects.filter(article=data).all()

    return render(req, 'post.html', {
        'title': data.title,
        'slug': data.slug,
        'category': data.category.slug,
        'content': data.body,
        'date': data.date,
        'image_url': data.image.image.url if data.image else None,

        'comments': [{
            'text': comment.text,
            'date': comment.date
        } for comment in comments],

        'categories': [{
            'name': category.name,
            'slug': category.slug
        } for category in categories],

        'recent': [{
            'title': article.title,
            'image': article.image.image.url,
            'date': article.date,
            'slug': article.slug,
            'category': article.category.slug
        } for article in recent if article.category],

        'related': [{
            'title': article.title,
            'image': article.image.image.url,
            'date': article.date,
            'slug': article.slug,
            'category': article.category.slug
        } for article in Article.objects.filter(category=data.category).all() if article.slug != data.slug and article.image]
    })


@require_http_methods(['GET'])
def get_category(req: HttpRequest, slug: str):
    articles = Article.objects.filter(
        category=slug).all().order_by('-timestamp')
    category = Category.objects.get(pk=slug)

    return render(req, 'category.html', {
        'category': {
            'slug': category.slug,
            'name': category.name
        },
        'articles': [{
            'slug': article.slug,
            'title': article.title,
            'image': article.image.image.url if article.image else '',
            'date': article.date,
            'desc': article.summary
        } for article in articles]
    })


@require_http_methods(['GET'])
def about(req: HttpRequest):
    return render(req, 'about.html')


@require_http_methods(['POST'])
def add_contact(req: HttpRequest):
    data = req.POST.dict()

    print(data)

    try:
        _contact = Contact.objects.create(email=data.get('email'))
    except IntegrityError:
        return redirect('/contact-us/')

    _contact.first_name = data.get('first-name')
    _contact.last_name = data.get('last-name')
    _contact.comments = data.get('comments')
    _contact.save()

    return redirect('/contact-us/')


@require_http_methods(['POST'])
def comment(req: HttpRequest, category: str, post: str):
    article = Article.objects.get(pk=post)

    data = req.POST.dict()

    Comment.objects.create(text=data.get('comment'), article=article)

    return redirect(article.get_absolute_url())


@require_http_methods(['GET'])
def contact(req: HttpRequest):
    return render(req, 'contact.html')


@require_http_methods(['GET'])
def return_404(req: HttpRequest, *args, **kwargs):
    resp = HttpResponse()
    resp.status_code = 404
    return resp
