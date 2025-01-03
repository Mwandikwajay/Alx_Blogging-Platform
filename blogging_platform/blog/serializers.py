from django.utils.timezone import now
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Post, Category, Tag, Comment, PostRating

class PostSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    category = serializers.SlugRelatedField(slug_field='name', queryset=Category.objects.all(), required=False)
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    tags = serializers.SlugRelatedField(
        many=True, 
        slug_field='name',  # This must match the field in the Tag model
        queryset=Tag.objects.all(), 
        required=False
    )

    class Meta:
        model = Post
        fields = '__all__'

    # Custom validation for the title field
    def validate_title(self, value):
        if len(value) > 100:
            raise serializers.ValidationError("Title cannot exceed 100 characters.")
        if len(value.strip()) == 0:
            raise serializers.ValidationError("Title cannot be empty or whitespace.")
        return value

    # Custom validation for the content field
    def validate_content(self, value):
        if len(value.strip()) == 0:
            raise serializers.ValidationError("Content cannot be empty or whitespace.")
        if len(value) < 10:
            raise serializers.ValidationError("Content must be at least 10 characters long.")
        return value

    # Custom validation for tags
    def validate_tags(self, value):
        if value and len(value) > 5:
            raise serializers.ValidationError("You cannot assign more than 5 tags to a post.")
        return value

    # Overall validation for multiple fields
    def validate(self, data):
        # Skip validation for `category` if this is a partial update
        if self.partial and 'category' not in data:
            return data
        
        if data.get('category') is None:
            raise serializers.ValidationError({"category": "Category is required."})
        return data

    # Override the update method to handle status changes
    def update(self, instance, validated_data):
        # If status is updated to 'published', set the published_at field
        if validated_data.get('status') == 'published' and instance.status != 'published':
            validated_data['published_at'] = now()
        
        # If status is updated to 'draft', reset the published_at field
        elif validated_data.get('status') == 'draft' and instance.status != 'draft':
            validated_data['published_at'] = None

        return super().update(instance, validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

from rest_framework import serializers
from .models import Comment

class CommentSerializer(serializers.ModelSerializer):
    post = serializers.PrimaryKeyRelatedField(read_only=True)  # Automatically handled by the view
    author = serializers.StringRelatedField(read_only=True)    # Author is the authenticated user

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'created_at']
        
class PostRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostRating
        fields = ['post', 'rating']