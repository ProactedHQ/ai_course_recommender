from rest_framework import serializers
from .models import CustomUser # SubscriptionTransaction removed

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone_number', 'is_student', 'subscription_tier')
        read_only_fields = ('id', 'username', 'email', 'is_student', 'subscription_tier')

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('phone_number',)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'is_student')

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password'],
            is_student=validated_data.get('is_student', True)
        )
        return user

class SubscriptionUpgradeSerializer(serializers.Serializer):
    target_tier = serializers.ChoiceField(choices=CustomUser.SUBSCRIPTION_TIERS)
    phone_number = serializers.CharField(max_length=15)

    def validate_phone_number(self, value):
        # Basic validation to ensure it looks like a Kenyan phone number
        # We'll normalize it in the utility
        import re
        if not re.match(r'^(?:254|\+254|0)?(7|1)\d{8}$', value):
            raise serializers.ValidationError("Please enter a valid M-Pesa phone number.")
        return value


"""
class SubscriptionTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionTransaction
        fields = '__all__'
"""
