from typing import Optional, Type
from django.contrib import admin, messages
from django.contrib.admin.sites import AdminSite
from django.http import HttpRequest

from threading import Thread
from asgiref.sync import sync_to_async
from random import randrange

import asyncio
import requests

from django_object_actions import DjangoObjectActions, action
from django.utils.text import slugify

from .models import Article, Generator, Category, Image, Rss, Used, ImageGenerator
from .openai_handler import generate, generate_image_prompt, generate_image, summarize
from .rss_handler import get_descriptions_and_links
from .scrapingHandler import scrape

# Register your models here.
@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    pass

@admin.register(ImageGenerator)
class ImageGeneratorAdmin(DjangoObjectActions, admin.ModelAdmin):
    date_hierarchy = "date"
    empty_value_display = "-empty-"
    readonly_fields = ('date', 'used', 'running')
    list_display = ['prompt','used', 'running']

    change_actions = ['_start_image_generation']

    @action(label='Generate Image', description='Generate Image using DALL-E 2')
    def _start_image_generation(self, req:HttpRequest, object: ImageGenerator):
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

@admin.register(Rss)
class RssAdmin(DjangoObjectActions, admin.ModelAdmin):
    @action(label='Generate Article', description='Generate Articles using the Rss feeds')
    def start_article_generation(self, req:HttpRequest, object: Rss):
        def generate():
            for _ in range(5):
                try:
                    res = requests.get(object.url)
                    if res.status_code == 200: break
                except Exception as e:
                    print(e)

            description_and_links = get_descriptions_and_links(res.text)

            used_links = [ x.url for x in Used.objects.all() ]
            description_and_links = [ x for x in description_and_links if x not in used_links ]

            idx:int = randrange(len(description_and_links))
            link:str = description_and_links[idx]
            del description_and_links; del used_links

            desc = scrape([link])[0]['text']

            generator = Generator(content=desc)

            def callback():
                used_link = Used(url=link)
                used_link.save()
            
            generate_article(generator, callback)
        
        thread = Thread(target=generate, daemon=True)
        thread.start()

        messages.success(req, 'The generator has started.')
    
    change_actions = ['start_article_generation']

@admin.register(Used)
class UsedAdmin(admin.ModelAdmin):
    pass
        




@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    date_hierarchy = "date"
    empty_value_display = "-empty-"
    readonly_fields = ('date', 'timestamp', 'modified', 'slug')
    list_display = ['title', 'category', 'timestamp']
    ordering = ['-timestamp']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


def generate_article(object: Generator, do_summarize=False,callback = None):
    object.running = True
    object.save()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    object.content = loop.run_until_complete(summarize(object.content))
    object.save()

    article = loop.run_until_complete(generate(object.content))

    if article:
        image_prompt = loop.run_until_complete(generate_image_prompt(article.body))
        image = generate_image(image_prompt, slugify(article.title)[:30])

        if image:
            article.image = image
            article.save()
        else:
            print('No Image')

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
    readonly_fields = ('date', 'used', 'running')

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

        thread = Thread(target=generate_article, args=[obj], daemon=True)
        thread.start()

        messages.success(request, 'The generator has started.')

    change_actions = ['generate']