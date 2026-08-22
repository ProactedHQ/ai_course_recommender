from rest_framework import serializers
from .models import BlogLike, BlogView
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name')

class BlogStatsSerializer(serializers.Serializer):
    likes_count = serializers.IntegerField()
    views_count = serializers.IntegerField()
    is_liked_by_user = serializers.BooleanField()
    viewers = UserSimpleSerializer(many=True)
    likers = UserSimpleSerializer(many=True)
