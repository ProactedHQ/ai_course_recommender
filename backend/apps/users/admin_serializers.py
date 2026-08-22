from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_active', 'is_staff', 'subscription_tier',
            'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'email', 'username', 'date_joined', 'last_login']
