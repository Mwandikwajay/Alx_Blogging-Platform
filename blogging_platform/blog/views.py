from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_200_OK,
    HTTP_403_FORBIDDEN,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Post, Category, Tag, Comment, PostRating
from .serializers import PostSerializer, UserSerializer, CategorySerializer, TagSerializer, CommentSerializer, PostRatingSerializer
from django.db.models import Q, Avg
from rest_framework.pagination import PageNumberPagination


# List or Create Posts
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])  # Public access to published posts
def list_or_create_posts(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            # Authenticated users see all their posts
            posts = Post.objects.filter(author=request.user)
        else:
            # Unauthenticated users see only published posts
            posts = Post.objects.filter(status='published')
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=HTTP_401_UNAUTHORIZED,
            )
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=HTTP_201_CREATED)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

# Retrieve, Update, Patch, or Delete a Post
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def post_detail(request, id):
    try:
        post = Post.objects.get(pk=id)

        # Restrict access to draft posts
        if post.status == 'draft' and post.author != request.user:
            return Response(
                {"error": "You do not have permission to view this draft post."},
                status=HTTP_403_FORBIDDEN,
            )

    except Post.DoesNotExist:
        return Response({"error": "Post not found"}, status=HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = PostSerializer(post)
        return Response(serializer.data, status=HTTP_200_OK)

    elif request.method in ['PUT', 'PATCH']:
        if post.author != request.user:
            return Response(
                {"error": "You do not have permission to edit this post."},
                status=HTTP_403_FORBIDDEN,
            )
        # For PATCH requests, allow partial updates
        partial = request.method == 'PATCH'
        serializer = PostSerializer(post, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        if post.author != request.user:
            return Response(
                {"error": "You do not have permission to delete this post."},
                status=HTTP_403_FORBIDDEN,
            )
        post.delete()
        return Response({"message": "Post deleted successfully"}, status=HTTP_204_NO_CONTENT)


# User Registration
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=HTTP_201_CREATED)
    return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


# User Login
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    if request.method != 'POST':
        return Response({"error": "Method not allowed"}, status=405)

    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({'error': 'Username and password are required'}, status=HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)
    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=HTTP_200_OK)
    return Response({'error': 'Invalid credentials'}, status=HTTP_400_BAD_REQUEST)


# Filter Posts by Category (Category ID)
@api_view(['GET'])
@permission_classes([AllowAny])  # Allow public access
def filter_posts_by_category(request, category_id):
    posts = Post.objects.filter(category_id=category_id)
    if not posts.exists():
        return Response({"error": "No posts found for this category"}, status=HTTP_404_NOT_FOUND)
    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data, status=HTTP_200_OK)


# Filter Posts by Tag (Tag Name)
@api_view(['GET'])
@permission_classes([AllowAny])  # Allow public access
def filter_posts_by_tag(request, tag_name):
    posts = Post.objects.filter(tags__name__icontains=tag_name)
    if not posts.exists():
        return Response({"error": "No posts found for this tag"}, status=HTTP_404_NOT_FOUND)
    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data, status=HTTP_200_OK)


# View Posts by Category Name
@api_view(['GET'])
@permission_classes([AllowAny])  # Allow public access
def posts_by_category(request, category_name):
    posts = Post.objects.filter(category__name=category_name)
    if not posts.exists():
        return Response({"error": f"No posts found for category '{category_name}'."}, status=HTTP_404_NOT_FOUND)
    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data, status=HTTP_200_OK)


# View Posts by Author Username
@api_view(['GET'])
@permission_classes([AllowAny])  # Allow public access
def posts_by_author(request, author_username):
    posts = Post.objects.filter(author__username=author_username)
    if not posts.exists():
        return Response({"error": f"No posts found for author '{author_username}'."}, status=HTTP_404_NOT_FOUND)
    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data, status=HTTP_200_OK)

# Publish Post
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def publish_post(request, id):
    try:
        post = Post.objects.get(pk=id, author=request.user)
        if post.status == 'published':
            return Response({"detail": "Post is already published."}, status=HTTP_400_BAD_REQUEST)
        post.publish()
        return Response({"detail": "Post published successfully."}, status=HTTP_200_OK)
    except Post.DoesNotExist:
        return Response({"error": "Post not found or not yours."}, status=HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([AllowAny])
def search_and_filter_posts(request):
    # Get query parameters
    search_query = request.query_params.get('q', '')
    author_name = request.query_params.get('author', '')
    category_name = request.query_params.get('category', '')
    published_date = request.query_params.get('published_date', '')
    tag_name = request.query_params.get('tag', '')

    # Base queryset: Only published posts
    posts = Post.objects.filter(status='published')

    # Apply search query
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(author__username__icontains=search_query)
        )

    # Filter by author
    if author_name:
        posts = posts.filter(author__username__iexact=author_name)

    # Filter by category
    if category_name:
        posts = posts.filter(category__name__iexact=category_name)

    # Filter by published date
    if published_date:
        posts = posts.filter(published_at__date=published_date)

    # Filter by tag
    if tag_name:
        posts = posts.filter(tags__name__iexact=tag_name)

    # Serialize and return results
    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data, status=HTTP_200_OK)

    # Pagination class for blog posts
class PostPagination(PageNumberPagination):
    page_size = 5  # Default number of posts per page
    page_size_query_param = 'page_size'  # Allow clients to set custom page size
    max_page_size = 50  # Maximum page size

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])  # Public access to published posts
def list_or_create_posts(request):
    if request.method == 'GET':
        # Base queryset: Only published posts
        if request.user.is_authenticated:
            posts = Post.objects.filter(author=request.user)
        else:
            posts = Post.objects.filter(status='published')

        # Sorting logic
        sort_by = request.query_params.get('sort_by', 'published_at')  # Default sort field
        if sort_by not in ['published_at', 'title', 'category']:
            sort_by = 'published_at'  # Fallback to default if invalid sort field provided

        # Handle category sorting specifically
        if sort_by == 'category':
            sort_by = 'category__name'  # Sort by the related field's name

        posts = posts.order_by(sort_by)

        # Apply pagination
        paginator = PostPagination()
        paginated_posts = paginator.paginate_queryset(posts, request)
        serializer = PostSerializer(paginated_posts, many=True)
        return paginator.get_paginated_response(serializer.data)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=HTTP_401_UNAUTHORIZED,
            )
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=HTTP_201_CREATED)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


# Create or List Comments for a Post
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])  # Anyone can view comments, only authenticated users can create
def comments_for_post(request, post_id):
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Post not found"}, status=HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        comments = Comment.objects.filter(post=post)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return Response({"error": "Authentication is required to add comments"}, status=HTTP_403_FORBIDDEN)

        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(post=post, author=request.user)
            return Response(serializer.data, status=HTTP_201_CREATED)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


# Update or Delete a Comment
@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def update_or_delete_comment(request, comment_id):
    try:
        comment = Comment.objects.get(pk=comment_id)
    except Comment.DoesNotExist:
        return Response({"error": "Comment not found"}, status=HTTP_404_NOT_FOUND)

    if comment.author != request.user:
        return Response({"error": "You do not have permission to modify this comment"}, status=HTTP_403_FORBIDDEN)

    if request.method == 'PUT':
        serializer = CommentSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        comment.delete()
        return Response({"message": "Comment deleted successfully"}, status=HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
        if request.user in post.likes.all():
            post.likes.remove(request.user)
            return Response({"message": "Post unliked successfully."}, status=200)
        else:
            post.likes.add(request.user)
            return Response({"message": "Post liked successfully."}, status=200)
    except Post.DoesNotExist:
        return Response({"error": "Post not found."}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rate_post(request, post_id):
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Post not found"}, status=HTTP_404_NOT_FOUND)

    # Extract the rating from the request
    rating_value = request.data.get('rating')
    if rating_value is None:
        return Response({"error": "Rating value is required"}, status=HTTP_400_BAD_REQUEST)

    try:
        # Ensure rating is an integer and within range (1-5)
        rating_value = int(rating_value)
        if rating_value < 1 or rating_value > 5:
            return Response({"error": "Rating must be between 1 and 5"}, status=HTTP_400_BAD_REQUEST)
    except ValueError:
        return Response({"error": "Rating must be an integer"}, status=HTTP_400_BAD_REQUEST)

    # Create or update the rating
    rating, created = PostRating.objects.get_or_create(
        post=post, user=request.user,
        defaults={'rating': rating_value}  # Set the default rating
    )
    if not created:
        # If the rating exists, update it
        rating.rating = rating_value
        rating.save()

    # Recalculate the average rating
    average_rating = PostRating.objects.filter(post=post).aggregate(avg_rating=Avg('rating'))['avg_rating']
    post.average_rating = average_rating
    post.save()

    return Response({"message": "Rating submitted successfully", "average_rating": average_rating}, status=HTTP_200_OK)