from django.urls import path, re_path
from . import views

urlpatterns = [
    path("", views.index, name='main'),
    path("favicon.ico/", views.return_404),
    path("contact/", views.add_contact),
    path('contact-us/', views.contact),
    path('<str:extra_page>/', views.extra_page),
    path("categories/<str:slug>/", views.get_category),
    re_path(r"(?P<category>^(?!image).*)/(?P<post>.*)/comment", views.comment),
    re_path(r"(?P<category>^(?!image).*)/(?P<post>.*)/$", views.get_post),
]
