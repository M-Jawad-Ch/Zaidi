from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest
from django.views.decorators.http import require_http_methods
from django.db.utils import IntegrityError

from django.core.mail import send_mail
from django.conf import settings

from .models import Article, Category, Contact, Comment, Index, ExtraPages

from threading import Thread


@require_http_methods(['GET'])
def index(req: HttpRequest):
    data = Index.objects.first()

    if not data:
        return render(req, 'mtc.html', {})

    latest_posts = [article for article in
                    Article.objects.order_by('-timestamp').all()
                    if article.image and article.visible][:10]

    return render(req, 'index.html', {
        'page_title': data.title,
        'desc': data.description,
        'image_text': data.image_text,
        'image': data.image.image.url if data.image else '',
        'heading': data.heading,
        'body':  data.body,

        'latest_posts': [{
            'title': article.title,
            'date': article.date,
            'category': article.category.name,
            'categorylink': article.category.get_absolute_url(),
            'slug': article.slug,
            'image': article.image.image.url,
            'link': article.get_absolute_url(),
            'desc': article.summary,
            'author': f'{article.author.first_name} {article.author.last_name}' if article.author else 'None'
        } for article in latest_posts],
    })


@require_http_methods(['GET'])
def extra_page(req: HttpRequest, extra_page: str):
    pages: list[ExtraPages] = ExtraPages.objects.all()

    page = None
    for page_ in pages:
        if page_.slug == extra_page:
            page = page_

    return render(req, 'extra_page.html', {
        'slug': page.slug,
        'title': page.title,
        'body': page.body,
        'image': page.image.image.url if page.image else None,
        'link': page.get_absolute_url(),
        'desc': page.description
    }) if page and page.visible else return_404(req)


@require_http_methods(['GET'])
def get_post(req: HttpRequest, category: str, post: str):
    try:
        data = Article.objects.get(pk=post)
        category: Category = Category.objects.get(pk=category)
    except Article.DoesNotExist:
        return return_404(req)

    if not data.visible or not data.category or category != data.category:
        return return_404(req)

    recent = [article for article in Article.objects.all().order_by(
        '-timestamp') if article.visible and article.image and article.slug != data.slug][:4]

    comments = Comment.objects.filter(article=data).all()
    category = data.category

    return render(req, 'post.html', {
        'title': data.title,
        'slug': data.slug,
        'category': data.category.slug,
        'content': data.body,
        'date': data.date,
        'image_url': data.image.image.url if data.image else None,
        'desc': data.summary,
        'link': data.get_absolute_url(),
        'author': f'{data.author.first_name} {data.author.last_name}' if data.author else '',
        'category': category.name,
        'categorylink': category.get_absolute_url(),

        'comments': [{
            'text': comment.text,
            'date': comment.date,
            'name': comment.name
        } for comment in comments],

        'recent': [{
            'title': article.title,
            'image': article.image.image.url,
            'date': article.date,
            'slug': article.slug,
            'category': article.category.slug,
            'link': article.get_absolute_url()
        } for article in recent if article.visible and article.category],

        'related': [{
            'title': article.title,
            'image': article.image.image.url,
            'date': article.date,
            'slug': article.slug,
            'category': article.category.slug,
            'link': article.get_absolute_url()
        } for article in Article.objects.filter(category=data.category).all() if article.visible and article.slug != data.slug and article.image]
    })


@require_http_methods(['GET'])
def get_category(req: HttpRequest, slug: str):
    articles = Article.objects.filter(
        category=slug).all().order_by('-timestamp')
    category = Category.objects.get(pk=slug)

    return render(req, 'category.html', {
        'articles': [{
            'slug': article.slug,
            'title': article.title,
            'image': article.image.image.url if article.image else '',
            'date': article.date,
            'desc': article.summary,
            'link': article.get_absolute_url(),
            'author': f'{article.author.first_name} {article.author.last_name} ~ ' if article.author else ''
        } for article in articles if article.visible],

        'link': category.get_absolute_url(),
        'name': category.name,
        'image': category.image.image.url if category.image else '',
        'desc': category.description,
        'title': category.title
    })


@require_http_methods(['POST'])
def add_contact(req: HttpRequest):
    data = req.POST.dict()

    try:
        _contact = Contact.objects.create(email=data.get('email'))
    except IntegrityError:
        print('error')
        return redirect('/contact-us/')

    _contact.first_name = data.get('first-name')
    _contact.last_name = data.get('last-name')
    _contact.comments = data.get('comments')
    _contact.save()

    def thread_func():
        if settings.EMAIL_HOST_USER and settings.EMAIL_RECEIVER and settings.EMAIL_HOST_PASSWORD:
            send_mail(
                'Contact Form',
                f'{_contact.first_name} {_contact.last_name} wants to get in contact.\n\nEmail: {_contact.email}\n\n\n{_contact.comments}',
                settings.EMAIL_HOST_USER,
                [settings.EMAIL_RECEIVER],
                fail_silently=True
            )

    Thread(target=thread_func, daemon=True).start()

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

    pages: list[ExtraPages] = ExtraPages.objects.all()

    page = None
    for page_ in pages:
        if page_.slug == 'contact-us':
            page = page_

    return render(req, 'contact.html', {
        'slug': page.slug,
        'title': page.title,
        'body': page.body,
        'image': page.image.image.url if page.image else None,
        'link': page.get_absolute_url(),
        'desc': page.description
    }) if page and page.visible else return_404(req)


@require_http_methods(['GET'])
def return_404(req: HttpRequest, *args, **kwargs):
    return HttpResponse('404')
