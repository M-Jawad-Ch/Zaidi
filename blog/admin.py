from typing import Any
from django.contrib import admin, messages
from django.contrib.admin.sites import AdminSite
from django.http import HttpRequest

from threading import Thread
from random import randrange

import asyncio
from django.http.request import HttpRequest
import requests

from django_object_actions import DjangoObjectActions, action
from django.utils.text import slugify

from .models import Article, Generator, Category, Image, Rss, Used
from .models import ImageGenerator, assign_category, Contact, Comment, Index
from .models import ExtraPages

from .openai_handler import generate, generate_image_prompt, generate_image, summarize
from .rss_handler import get_descriptions_and_links
from .scrapingHandler import scrape

# Register your models here.


@admin.register(ExtraPages)
class ExtraPagesAdmin(admin.ModelAdmin):
    list_display = ['slug', 'visible']
    list_per_page = 20


@admin.register(Index)
class IndexAdmin(admin.ModelAdmin):
    def has_add_permission(self, request: HttpRequest) -> bool:
        return False  # super().has_add_permission(request)

    def has_delete_permission(self, request: HttpRequest, obj: Any | None = ...) -> bool:
        return False  # super().has_delete_permission(request, obj)


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    readonly_fields = ['timestamp', 'html']
    ordering = ['-timestamp']
    list_display = ['name', 'timestamp']
    list_per_page = 20
    search_fields = ['name', 'alt']

    def save_model(self, request: Any, obj: Image, form: Any, change: Any) -> None:
        obj.name = slugify(obj.name)

        return super().save_model(request, obj, form, change)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    search_fields = ['first_name', 'last_name', 'email', 'comments']
    readonly_fields = ('first_name', 'last_name', 'comments', 'email')
    list_per_page = 20


@admin.register(ImageGenerator)
class ImageGeneratorAdmin(DjangoObjectActions, admin.ModelAdmin):
    date_hierarchy = "date"
    empty_value_display = "-empty-"
    readonly_fields = ('date', 'used', 'running', 'image')
    list_display = ['prompt', 'used', 'running']
    change_actions = ['_start_image_generation']
    list_per_page = 20

    @action(label='Generate Image', description='Generate Image using DALL-E 2')
    def _start_image_generation(self, req: HttpRequest, object: ImageGenerator):
        def generate():
            object.running = True
            object.save()

            image = generate_image(object.prompt, slugify(object.name))

            if not image:
                print('No Image')
                object.running = False
                object.save()
                return

            object.image = image
            object.running = False
            object.used = True
            object.save()

        thread = Thread(target=generate, daemon=True)
        thread.start()

        messages.success(req, 'The generator has started.')


def generate_thread_func(object: Rss):
    for _ in range(5):
        try:
            res = requests.get(object.url)
            if res.status_code == 200:
                break
        except Exception as e:
            print(e)

    description_and_links = get_descriptions_and_links(res.text)

    used_links = [x.url for x in Used.objects.all()]
    description_and_links = [
        x for x in description_and_links if x not in used_links]

    if not description_and_links:
        return

    idx: int = randrange(len(description_and_links))
    link: str = description_and_links[idx]
    del description_and_links
    del used_links

    desc = scrape([link])[0]['text']

    generator = Generator(content=desc, rss=object)

    def callback():
        used_link = Used(url=link)
        used_link.save()

    generate_article(generator, callback)


@admin.register(Rss)
class RssAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_per_page = 20

    @action(label='Generate Article', description='Generate Articles using the Rss feeds')
    def start_article_generation(self, req: HttpRequest, object: Rss):
        thread = Thread(target=generate_thread_func,
                        daemon=True, args=[object])
        thread.start()

        messages.success(req, 'The generator has started.')

    change_actions = ['start_article_generation']


@admin.register(Used)
class UsedAdmin(admin.ModelAdmin):
    list_per_page = 20


@admin.action(description="Publish selected")
def publish(modeladmin, request, queryset):
    queryset.update(visible=True)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    date_hierarchy = "date"
    empty_value_display = "-empty-"
    readonly_fields = ('date', 'timestamp', 'modified',
                       'slug', 'rss', 'image_html')
    list_display = ['title', 'visible', 'category', 'timestamp']
    ordering = ['-timestamp']
    exclude = ('embedding', 'date')
    actions = [publish]
    search_fields = ['title', 'summary', 'body']
    list_per_page = 20
    fieldsets = (
        (None, {
            'fields': ('title', 'image', 'image_html', ('category', 'author'), 'visible',
                       'summary', 'body', 'rss', 'timestamp', 'modified')
        }),
    )

    def image_html(self, obj: Article):
        return obj.image.html if obj.image else None


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    search_fields = ['text', 'name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    exclude = ('embedding',)
    search_fields = ['name', 'description']
    readonly_fields = ('visible',)
    list_display = ('name', 'visible',)
    ordering = ('name',)


def _generate_image(article: Article):
    loop_ = asyncio.new_event_loop()
    asyncio.set_event_loop(loop_)

    image_prompt = loop_.run_until_complete(
        generate_image_prompt(article.body))
    image = generate_image(image_prompt, slugify(article.title)[:30])

    if image:
        article.image = image
    else:
        pass

    article.save()
    loop_.close()


def generate_article(object: Generator, callback=None, do_summarize=True):
    object.running = True
    object.save()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    object.content = loop.run_until_complete(
        summarize(object.content)) if do_summarize else object.content
    object.save()

    article = loop.run_until_complete(generate(object.content))

    if article:
        object.article = article

        article.author = object.author
        article.rss = object.rss
        article.save()

    loop.close()

    object.running = False
    object.used = True if article else False
    object.save()

    if object.used and callback:
        callback()


@admin.register(Generator)
class GeneratorAdmin(DjangoObjectActions, admin.ModelAdmin):
    date_hierarchy = "date"
    empty_value_display = "-empty-"
    readonly_fields = ('date', 'used', 'running', 'article')
    list_per_page = 20
    search_fields = ['content']

    def __init__(self, model: type, admin_site: AdminSite | None) -> None:
        super().__init__(model, admin_site)
        self.list_display += ('used', 'running')

    @action(label='Generate', description='Prompt GPT to generate an article.')
    def generate(self, request: HttpRequest, obj: Generator):

        if obj.used:
            messages.warning(request, 'This prompt has already been used.')
            return

        if obj.running:
            messages.warning(request, 'This prompt is already running.')
            return

        obj.author = request.user
        obj.save()

        thread = Thread(target=generate_article, args=[obj], daemon=True)
        thread.start()

        messages.success(request, 'The generator has started.')

    change_actions = ['generate']
