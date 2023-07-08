from django.contrib import admin, messages
from django.http import HttpRequest

from threading import Thread
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


async def generate_article(object: Generator):
    object.running = True
    await object.asave()

    article = await generate(object.content)

    if article:
        image_prompt = generate_image_prompt(article.body)
        image = generate_image(image_prompt, slugify(article.title)[:30])

        if image:
            article.image = image
            article.save()

    object.running = False
    object.used = True if article else False
    await object.asave()


def thread_function(object: Generator):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(generate_article(object))
    loop.close()


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

        thread = Thread(target=thread_function, args=[obj], daemon=True)
        thread.start()

        messages.success(request, 'The generator has started.')

    change_actions = ['generate']