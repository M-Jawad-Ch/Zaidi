

from .models import Category, ExtraPages


def ContextMiddleWare(get_response):

    def middleware(request):
        categories = Category.objects.all()
        extra_pages = ExtraPages.objects.all()

        request.categories = [{
            'name': category.name,
            'slug': category.slug,
            'link': category.get_absolute_url()
        } for category in categories]

        request.extra_pages = [{
            'slug': extra_page.slug,
            'name': extra_page.title,
            'link': extra_page.get_absolute_url()
        } for extra_page in extra_pages if extra_page.visible]

        response = get_response(request)

        return response

    return middleware
