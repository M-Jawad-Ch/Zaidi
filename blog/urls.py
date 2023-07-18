from django.urls import path, re_path

from . import views

urlpatterns = [
    path("", views.index, name='main'),
    path("favicon.ico/", views.return_404),
    path("about-us/", views.about),
    path("contact-us/", views.contact),
    path("contact/", views.add_contact),
    path("<str:slug>/", views.get_category),
    re_path(r"(?P<category>^(?!image).*)/(?P<post>.*)/comment", views.comment),
    re_path(r"(?P<category>^(?!image).*)/(?P<post>.*)$", views.get_post),
]
