from typing import Any, Optional, Type
from django.contrib import admin, messages
from django.contrib.admin.sites import AdminSite
from django.http import HttpRequest

from threading import Thread
from asgiref.sync import sync_to_async
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
    pass


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

    def save_model(self, request: Any, obj: Image, form: Any, change: Any) -> None:
        obj.name = slugify(obj.name)
        obj.html = f'<img src="/{obj.image.name}">'
        return super().save_model(request, obj, form, change)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    readonly_fields = ('first_name', 'last_name', 'comments', 'email')


@admin.register(ImageGenerator)
class ImageGeneratorAdmin(DjangoObjectActions, admin.ModelAdmin):
    date_hierarchy = "date"
    empty_value_display = "-empty-"
    readonly_fields = ('date', 'used', 'running', 'image')
    list_display = ['prompt', 'used', 'running']

    change_actions = ['_start_image_generation']

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

    idx: int = randrange(len(description_and_links))
    link: str = description_and_links[idx]
    del description_and_links
    del used_links

    desc = scrape([link])[0]['text']

    generator = Generator(content=desc)

    def callback():
        used_link = Used(url=link)
        used_link.save()

    generate_article(generator, callback)


@admin.register(Rss)
class RssAdmin(DjangoObjectActions, admin.ModelAdmin):
    @action(label='Generate Article', description='Generate Articles using the Rss feeds')
    def start_article_generation(self, req: HttpRequest, object: Rss):
        thread = Thread(target=generate_thread_func,
                        daemon=True, args=[object])
        thread.start()

        messages.success(req, 'The generator has started.')

    change_actions = ['start_article_generation']


@admin.register(Used)
class UsedAdmin(admin.ModelAdmin):
    pass


@admin.action(description="Publish selected")
def publish(modeladmin, request, queryset):
    queryset.update(visible=True)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    date_hierarchy = "date"
    empty_value_display = "-empty-"
    readonly_fields = ('date', 'timestamp', 'modified', 'slug')
    list_display = ['title', 'visible', 'category', 'timestamp']
    ordering = ['-timestamp']
    exclude = ('embedding',)
    actions = [publish]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    exclude = ('embedding',)
    pass


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
