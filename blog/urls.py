from django.urls import path, re_path
from django.http import HttpResponseRedirect as redirect
from . import views

urlpatterns = [
    path("", views.index, name='main'),
    path("favicon.ico/", views.return_404),
    path("contact/", views.add_contact),

    path('<str:extra_page>/', views.extra_page),
    path(
        '<str:extra_page>',
        lambda req, extra_page: redirect(f'/{extra_page}/')
    ),


    path("categories/<str:slug>/", views.get_category),
    path(
        "categories/<str:slug>",
        lambda req, slug: redirect(f'/categories/{slug}/')
    ),

    re_path(r"(?P<category>^(?!image).*)/(?P<post>.*)/comment", views.comment),

    re_path(r"(?P<category>^(?!image).*)/(?P<post>.*)/$", views.get_post),
    re_path(
        r"(?P<category>^(?!image).*)/(?P<post>.*)$",
        lambda req, category, post: redirect(f'/{category}/{post}/')
    ),
]
