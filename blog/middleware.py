from django.http import HttpResponse, HttpRequest
from django.shortcuts import redirect

from .models import Category, ExtraPages


def ContextMiddleWare(get_response):

    def middleware(request: HttpRequest):
        categories = Category.objects.all()
        extra_pages = ExtraPages.objects.all()

        request.categories = [{
            'name': category.name,
            'slug': category.slug,
            'link': category.get_absolute_url()
        } for category in categories]

        request.extra_pages = [{
            'slug': extra_page.slug,
            'name': extra_page.name(),
            'link': extra_page.get_absolute_url()
        } for extra_page in extra_pages if extra_page.visible]

        response: HttpResponse = get_response(request)

        return response

    return middleware


def RedirectMiddleWare(get_response):

    def middleware(request: HttpRequest):
        if request.headers['Host'] != 'www.medpoise.com':
            return redirect('https://www.medpoise.com' + request.path, permanent=True)

        return get_response(request)

    return middleware
