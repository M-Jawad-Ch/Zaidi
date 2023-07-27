import json

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest
from django.views.decorators.http import require_http_methods
from django.db.utils import IntegrityError
from .models import Article, Category, Contact, Comment, Index, ExtraPages


@require_http_methods(['GET'])
def index(req: HttpRequest):
    data = Index.objects.first()
    if not data:
        return render(req, 'mtc.html', {})

    categories = Category.objects.all()
    latest_posts = [article for article in
                    Article.objects.order_by('-timestamp').all()
                    if article.image][:6]

    extra_pages = ExtraPages.objects.all()

    return render(req, 'index.html', {
        'page_title': data.title,
        'desc': data.description,
        'image_text': data.image_text,
        'image': data.image.image.url if data.image else '',
        'heading': data.heading,
        'body':  data.body,

        'categories': [{
            'name': category.name,
            'slug': category.slug
        } for category in categories],

        'latest_posts': [{
            'title': article.title,
            'category': article.category.slug,
            'slug': article.slug,
            'image': article.image.image.url,
            'link': article.get_absolute_url()
        } for article in latest_posts],

        'extra_pages': [{
            'slug': extra_page.slug,
            'name': extra_page.title
        } for extra_page in extra_pages if extra_page.visible]
    })


@require_http_methods(['GET'])
def extra_page(req: HttpRequest, extra_page: str):
    pages: list[ExtraPages] = ExtraPages.objects.all()

    page = None
    for page_ in pages:
        if page_.slug == extra_page:
            page = page_

    extra_pages = ExtraPages.objects.all()

    return render(req, 'extra_page.html', {
        'slug': page.slug,
        'title': page.title,
        'body': page.body,
        'image': page.image.image.url if page.image else None,

        'extra_pages': [{
            'slug': extra_page.slug,
            'name': extra_page.title
        } for extra_page in extra_pages if extra_page.visible]
    }) if page and page.visible else return_404(req)


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

    extra_pages = ExtraPages.objects.all()

    return render(req, 'post.html', {
        'title': data.title,
        'slug': data.slug,
        'category': data.category.slug,
        'content': data.body,
        'date': data.date,
        'image_url': data.image.image.url if data.image else None,
        'desc': data.summary,
        'link': data.get_absolute_url(),

        'comments': [{
            'text': comment.text,
            'date': comment.date,
            'name': comment.name
        } for comment in comments],

        'categories': [{
            'name': category.name,
            'slug': category.slug,
            'link': category.get_absolute_url()
        } for category in categories],

        'recent': [{
            'title': article.title,
            'image': article.image.image.url,
            'date': article.date,
            'slug': article.slug,
            'category': article.category.slug,
            'link': article.get_absolute_url()
        } for article in recent if article.category],

        'extra_pages': [{
            'slug': extra_page.slug,
            'name': extra_page.title
        } for extra_page in extra_pages if extra_page.visible],

        'related': [{
            'title': article.title,
            'image': article.image.image.url,
            'date': article.date,
            'slug': article.slug,
            'category': article.category.slug,
            'link': article.get_absolute_url()
        } for article in Article.objects.filter(category=data.category).all() if article.slug != data.slug and article.image]
    })


@require_http_methods(['GET'])
def get_category(req: HttpRequest, slug: str):
    articles = Article.objects.filter(
        category=slug).all().order_by('-timestamp')
    category = Category.objects.get(pk=slug)
    extra_pages = ExtraPages.objects.all()

    return render(req, 'category.html', {
        'category': {
            'slug': category.slug,
            'name': category.name,
            'link': category.get_absolute_url()
        },
        'articles': [{
            'slug': article.slug,
            'title': article.title,
            'image': article.image.image.url if article.image else '',
            'date': article.date,
            'desc': article.summary,
            'link': article.get_absolute_url()
        } for article in articles],

        'extra_pages': [{
            'slug': extra_page.slug,
            'name': extra_page.title
        } for extra_page in extra_pages if extra_page.visible],

        'link': category.get_absolute_url()
    })


@require_http_methods(['GET'])
def about(req: HttpRequest):
    extra_pages = ExtraPages.objects.all()
    return render(req, 'about.html', {
        'extra_pages': [{
            'slug': extra_page.slug,
            'name': extra_page.title
        } for extra_page in extra_pages if extra_page.visible]
    })


@require_http_methods(['POST'])
def add_contact(req: HttpRequest):
    data = req.POST.dict()

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

    Comment.objects.create(text=data.get('comment'),
                           article=article, name=data.get('name'))

    return redirect(article.get_absolute_url())


@require_http_methods(['GET'])
def contact(req: HttpRequest):
    extra_pages = ExtraPages.objects.all()

    return render(req, 'contact.html', {
        'extra_pages': [{
            'slug': extra_page.slug,
            'name': extra_page.title
        } for extra_page in extra_pages if extra_page.visible]
    })


@require_http_methods(['GET'])
def return_404(req: HttpRequest, *args, **kwargs):
    resp = HttpResponse()
    resp.status_code = 404
    return resp
