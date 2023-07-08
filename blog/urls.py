from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name='main'),
    path("favicon.ico/", views.return_404),
    path("post/<str:slug>/", views.get_post),
    path("<str:slug>/", views.get_category),
    path("<str:category>/<str:post>/", views.get_post_via_category),
]
