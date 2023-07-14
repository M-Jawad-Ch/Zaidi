from django.urls import path, re_path

from . import views

urlpatterns = [
    path("", views.index, name='main'),
    path("favicon.ico/", views.return_404),
    path("about-us/", views.about),
    path("<str:slug>/", views.get_category),
    re_path(r"^(?!image).*/(?P<post>.*)$", views.get_post_via_category),
]
