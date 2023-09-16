from django.contrib.sitemaps import Sitemap
from blog.models import Article, Category, ExtraPages


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
        return [article for article in Article.objects.all() if article.visible]

    def lastmod(self, obj: Article):
        return obj.modified.date()


class CategorySiteMap(Sitemap):
    changefreg = "daily"
    priority = 0.5

    def items(self):
        return [category for category in Category.objects.all() if category.visible]


class PagesSiteMap(Sitemap):
    changefreg = "never"
    priority = 0.5

    def items(self):
        return [page for page in ExtraPages.objects.all() if page.visible]
