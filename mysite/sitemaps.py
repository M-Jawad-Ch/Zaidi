from django.contrib.sitemaps import Sitemap
from blog.models import Article, Category


from django.urls import reverse


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "daily"

    def items(self):
        return ["main"]

    def location(self, item):
        return reverse(item)


class ArticleSiteMap(Sitemap):
    changefreq = "never"
    priority = 0.5

    def items(self):
        return Article.objects.all()

    def lastmod(self, obj: Article):
        return obj.modified.date()


class CategorySiteMap(Sitemap):
    changefreg = "daily"
    priority = 0.5

    def items(self):
        return Category.objects.all()
