from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Category name
    description = models.TextField(blank=True, null=True)  # Optional description

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)  # Tag name

    def __str__(self):
        return self.name


class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE)  # Author field
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)  # Post category
    tags = models.ManyToManyField(Tag, blank=True)  # Many-to-many relation with Tag
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(blank=True, null=True)  # Optional published date
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')  # New status field
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    average_rating = models.FloatField(default=0.0)

    def publish(self):
        """Publish the post and set the published date."""
        self.status = 'published'
        self.published_at = now()
        self.save()

    def __str__(self):
        return self.title

class Comment(models.Model):
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"

class PostRating(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()  # 1 to 5