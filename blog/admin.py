from django.contrib import admin, messages
from django.http import HttpRequest

from threading import Thread
from asgiref.sync import sync_to_async
import asyncio

from django_object_actions import DjangoObjectActions, action
from django.utils.text import slugify

from .models import Article, Generator, Category, Image
from .openai_handler import generate, generate_image_prompt, generate_image


# Register your models here.
@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    pass


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    date_hierarchy = "date"
    empty_value_display = "-empty-"
    readonly_fields = ('date', 'timestamp', 'modified', 'slug')
    list_display = ['title', 'category', 'timestamp']
    ordering = ['-timestamp']

def generate_article(object: Generator):
    object.running = True
    object.save()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    article = loop.run_until_complete(generate(object.content))

    if article:
        image_prompt = loop.run_until_complete(generate_image_prompt(article.body))
        image = generate_image(image_prompt, slugify(article.title)[:30])

        if image:
            article.image = image
            article.save()

    loop.close()

    object.running = False
    object.used = True if article else False
    object.save()



@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Generator)
class GeneratorAdmin(DjangoObjectActions, admin.ModelAdmin):
    date_hierarchy = "date"
    empty_value_display = "-empty-"
    readonly_fields = ('date', 'used', 'running')
    list_display = ['content', 'used', 'running']

    @action(label='Generate', description='Prompt GPT to generate an article.')
    def generate(self, request: HttpRequest, obj: Generator):
        if obj.used:
            messages.warning(request, 'This prompt has already been used.')
            return

        if obj.running:
            messages.warning(request, 'This prompt is already running.')
            return

        thread = Thread(target=generate_article, args=[obj], daemon=True)
        thread.start()

        messages.success(request, 'The generator has started.')

    change_actions = ['generate']