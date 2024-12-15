from django.urls import path
from .views import list_posts, create_post

urlpatterns = [
    path('posts/', list_posts, name='list-posts'),
    path('posts/', create_post, name='create-post'),
]
