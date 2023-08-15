from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth.models import User


from datetime import datetime
from json import dumps, loads
from openai import Embedding
from threading import Thread

import numpy
import re


def embed(content: str):
    for _ in range(5):
        res = Embedding.create(
            input=content,
            model="text-embedding-ada-002"
        )

        return res['data'][0]['embedding']


class Image(models.Model):
    name = models.CharField(primary_key=True, max_length=100)
    image = models.ImageField(upload_to='images/')
    timestamp = models.DateTimeField(auto_now_add=True)
    html = models.TextField()
    alt = models.CharField(max_length=200, blank=True)

    def get_absolute_url(self):
        return f'/images/{self.image.name}' if not re.match('images', self.image.name) else f'/{self.image.name}'

    def save(self, *args, **kwargs):
        self.html = f'<img src="{self.get_absolute_url()}" alt="{self.alt}">'
        super(Image, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'A - Image'


class ExtraPages(models.Model):
    slug = models.SlugField(max_length=100, unique=True)
    title = models.CharField(max_length=100, blank=True)
    image = models.ForeignKey(
        Image, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField(blank=True)
    visible = models.BooleanField(default=False)
    description = models.CharField(max_length=300, blank=True)

    def name(self):
        return re.sub('-', ' ', self.slug).title()

    class Meta:
        verbose_name = 'A - Extra Pages'
        verbose_name_plural = 'A - Extra Pages'

    def get_absolute_url(self):
        return f'/{self.slug}/'


class Category(models.Model):
    slug = models.SlugField(max_length=100, primary_key=True, default='NULL')
    name = models.CharField(max_length=100, unique=True)
    embedding = models.TextField()
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    title = models.CharField(max_length=200)
    visible = models.BooleanField(default=False)

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

    def isPointedBy(self):
        return True if Article.objects.filter(category=self, visible=True).first() else False

    def __str__(self) -> str:
        return str(self.name)

    def get_absolute_url(self):
        return f'/categories/{self.slug}/'

    class Meta:
        verbose_name = 'A - Category'
        verbose_name_plural = 'A - Categories'


class Rss(models.Model):
    url = models.TextField()

    def __str__(self):
        return self.url

    class Meta:
        verbose_name = 'A - Rss Link'


class Used(models.Model):
    url = models.TextField()

    def __str__(self) -> str:
        return self.url

    class Meta:
        verbose_name = 'B - Used Rss Link'


class Article(models.Model):
    slug = models.SlugField(unique=True, max_length=100, primary_key=True)
    title = models.CharField(max_length=100)
    date = models.DateField(auto_now_add=True)
    body = models.TextField()
    summary = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now_add=True)
    visible = models.BooleanField(default=False)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    rss = models.ForeignKey(Rss, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'A - Article'

    image = models.ForeignKey(
        Image, on_delete=models.SET_NULL, null=True, blank=True)

    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True)

    embedding = models.TextField()

    def save(self, *args, **kwargs):
        try:
            old = Article.objects.get(pk=self.slug)
        except Article.DoesNotExist as e:
            old = None

        self.modified = datetime.now(tz=timezone.utc)

        if not self.embedding or self.body != old.body:
            self.embedding = dumps(embed(self.body))
            assign_category(self)

        super(Article, self).save(*args, **kwargs)

        new_category = self.category

        if old and old.category != self.category:
            old_category = old.category

            old_category.visible = old_category.isPointedBy()
            old_category.save()

        new_category.visible = new_category.isPointedBy()
        new_category.save()

    def __str__(self):
        if self.title:
            return self.title

        if self.slug:
            return self.slug

    def get_absolute_url(self):
        return f'/{self.category.slug}/{self.slug}/' if self.category else '/'


class Comment(models.Model):
    text = models.TextField()
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.text[:50]

    class Meta:
        verbose_name = 'A - Comment'


class ImageGenerator(models.Model):
    name = models.CharField(max_length=200)
    prompt = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)
    running = models.BooleanField(default=False)
    image = models.ForeignKey(
        Image, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.prompt[:100]

    class Meta:
        verbose_name = 'B - Image Generator'


class Contact(models.Model):
    first_name = models.CharField(max_length=300)
    last_name = models.CharField(max_length=300)
    email = models.EmailField()
    comments = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name} : {self.comments[:30]}'

    class Meta:
        verbose_name = 'A - Contact'


class Generator(models.Model):
    id = models.AutoField(primary_key=True)
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)
    running = models.BooleanField(default=False)
    article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    rss = models.ForeignKey(Rss, on_delete=models.SET_NULL, null=True)

    def __str__(self) -> str:
        return self.content[:100]

    class Meta:
        verbose_name = 'B - Article Generator'


class Index(models.Model):
    image = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    notification_receiver_email = models.EmailField(blank=True)
    notification_sender_email = models.EmailField(blank=True)
    notification_sender_email_password = models.CharField(
        max_length=300, blank=True)

    heading = models.CharField(max_length=300)
    image_text = models.CharField(max_length=500)
    body = models.TextField()
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=500)
    articles_generated_per_day = models.IntegerField(default=3)

    def __str__(self) -> str:
        return "Index Page"

    class Meta:
        verbose_name = 'A - Index'
        verbose_name_plural = 'A - Index'


def difference(vec1, vec2):
    return ((numpy.array(vec1) - numpy.array(vec2)) ** 2).sum()


def assign_category(article: Article):
    if not article.embedding:
        article.embedding = embed(article.body)

    categories = Category.objects.all()
    categories = [
        category for category in categories if loads(category.embedding)]

    categories = [
        (
            category,
            difference(loads(article.embedding), loads(category.embedding))
        ) for category in categories]

    categories.sort(key=lambda x: x[1])

    article.category = categories[0][0]

    return article
