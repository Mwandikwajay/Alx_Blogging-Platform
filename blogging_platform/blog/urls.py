from django.urls import path
from django.views.generic import TemplateView
from .views import (
    list_or_create_posts,
    post_detail,
    register_user,
    login_user,
    filter_posts_by_category,
    filter_posts_by_tag,
    posts_by_category,
    posts_by_author,
    publish_post,
    search_and_filter_posts,
    comments_for_post,
    update_or_delete_comment,
    like_post,
    rate_post, 
)

urlpatterns = [
    # API Endpoints
    path('api/posts/', list_or_create_posts, name='list-or-create-posts'),
    path('api/posts/<int:id>/', post_detail, name='post-detail'),
    path('api/register/', register_user, name='register-user'),
    path('api/login/', login_user, name='login-user'),
    path('api/posts/category/<int:category_id>/', filter_posts_by_category, name='filter_posts_by_category'),
    path('api/posts/tag/<str:tag_name>/', filter_posts_by_tag, name='filter_posts_by_tag'),
    path('api/posts/category-name/<str:category_name>/', posts_by_category, name='posts-by-category'),
    path('api/posts/author/<str:author_username>/', posts_by_author, name='posts-by-author'),
    path('api/posts/<int:id>/publish/', publish_post, name='publish-post'),
    path('api/posts/search/', search_and_filter_posts, name='search-and-filter-posts'),
    path('api/posts/<int:post_id>/comments/', comments_for_post, name='post-comments'), 
    path('api/comments/<int:comment_id>/', update_or_delete_comment, name='comment-detail'), 
    path('api/posts/<int:post_id>/like/', like_post, name='like-post'),
    path('api/posts/<int:post_id>/rate/', rate_post, name='rate-post'),

    # Template Endpoints
    path('create-post/', TemplateView.as_view(template_name='create_post.html'), name='create-post'),
    path('update-post/<int:id>/', TemplateView.as_view(template_name='update_post.html'), name='update-post'),
    path('delete-post/', TemplateView.as_view(template_name='delete_post.html'), name='delete-post'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
]
