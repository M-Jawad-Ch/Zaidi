from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name='main'),
    path("favicon.ico/", views.return_404),
    path("posts/<str:slug>", views.get_post),
    path("<str:slug>/", views.get_category),
]
