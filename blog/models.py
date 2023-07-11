from django.db import models
from django.utils.text import slugify
from django.contrib.sitemaps import ping_google
from django.utils import timezone
from django.conf import settings

from datetime import datetime
from json import dumps, loads
from openai import Embedding
from threading import Thread

import numpy

def embed(content:str):
    for _ in range(5):
        res = Embedding.create(
            input=content,
            model="text-embedding-ada-002"
        )

        return res['data'][0]['embedding']    

class Category(models.Model):
    slug = models.SlugField(max_length=100, primary_key=True, default='NULL')
    name = models.CharField(max_length=100, unique=True)
    embedding = models.TextField()

    def save(self, *args, **kwargs):
        try:
            old = Category.objects.get(pk=self.slug)
        except Category.DoesNotExist as e:
            pass

        self.slug = slugify(self.name)

        def _embed():
            if not self.embedding or self.slug != old.slug:
                self.embedding = dumps(embed(self.name))
                self.save()
        
        thread = Thread(target=_embed, daemon=True)
        thread.start()

        super(Category, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return str(self.name)

    def get_absolute_url(self):
        return f'/{self.slug}'

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'


class Rss(models.Model):
    url = models.TextField()

    def __str__(self):
        return self.url
    
    class Meta:
        verbose_name = 'Rss Link'
        verbose_name_plural = 'Rss Links'



class Used(models.Model):
    url = models.TextField()

    def __str__(self) -> str:
        return self.url
    
    class Meta:
        verbose_name = 'Used Rss Link'
        verbose_name_plural = 'Used Rss Links'
        

class Image(models.Model):
    name = models.CharField(primary_key=True, max_length=100)
    image = models.ImageField(upload_to='images/')

    def __str__(self):
        return self.name

class Article(models.Model):
    slug = models.SlugField(unique=True, max_length=100, primary_key=True)
    title = models.CharField(max_length=100)
    date = models.DateField(auto_now_add=True)
    body = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now_add=True)

    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)

    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True)
    
    embedding = models.TextField()

    def save(self, *args, **kwargs):
        try:
            old = Article.objects.get(pk=self.slug)
        except Article.DoesNotExist as e:
            pass

        self.modified = datetime.now(tz=timezone.utc)

        if not self.embedding or self.body != old.body:
            self.embedding = dumps(embed(self.body))
            assign_category(self)

        super(Article, self).save(*args, **kwargs)

        if not settings.DEBUG:
            try:
                ping_google('/sitemap.xml')
            except Exception as e:
                print(e)
                pass

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f'/{self.category.slug}/{self.slug}' if self.category else '/'

class ImageGenerator(models.Model):
    name = models.CharField(max_length=200)
    prompt = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)
    running = models.BooleanField(default=False)
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.prompt[:100]
    
    class Meta:
        verbose_name = 'Image Generator'
        verbose_name_plural = 'Image Generators'

class Generator(models.Model):
    id = models.AutoField(primary_key=True)
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)
    running = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.content[:100]
    
    class Meta:
        verbose_name = 'Article Generator'
        verbose_name_plural = 'Article Generators'




def difference(vec1, vec2):
    return ((numpy.array(vec1) - numpy.array(vec2)) ** 2).sum()


def assign_category(article:Article):
    if not article.embedding:
        article.embedding = embed(article.body)

    categories = Category.objects.all()
    categories = [category for category in categories if loads(category.embedding)]

    categories = [ 
        (
            category,
            difference(loads(article.embedding), loads(category.embedding))
        ) for category in categories ]
    
    categories.sort( key=lambda x: x[1] )

    article.category = categories[0][0]

    return article