"""
Serializers for accounts app.
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from apps.core.models import User, UserProfile, UserApiKey
import secrets


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    
    class Meta:
        model = UserProfile
        fields = [
            'company_name', 'website', 'timezone', 'language',
            'email_notifications', 'whatsapp_notifications',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)
    has_active_subscription = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone',
            'is_verified', 'is_active', 'created_at', 'updated_at',
            'profile', 'full_name', 'has_active_subscription'
        ]
        read_only_fields = [
            'id', 'is_verified', 'is_active', 'created_at', 'updated_at'
        ]


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone',
            'password', 'password_confirm'
        ]
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value
    
    def create(self, validated_data):
        """Create new user."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate_email(self, value):
        """Validate email exists."""
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""
    
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        """Validate new password confirmation."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match.")
        return attrs


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""
    
    profile = UserProfileSerializer()
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'profile'
        ]
    
    def update(self, instance, validated_data):
        """Update user and profile data."""
        profile_data = validated_data.pop('profile', {})
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update profile fields
        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance


class VerifyEmailSerializer(serializers.Serializer):
    """Serializer for email verification."""
    
    uidb64 = serializers.CharField()
    token = serializers.CharField()


class UserApiKeySerializer(serializers.ModelSerializer):
    """Serializer for UserApiKey model."""
    
    class Meta:
        model = UserApiKey
        fields = [
            'id', 'name', 'key', 'is_active', 'last_used_at',
            'usage_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'key', 'last_used_at', 'usage_count', 
            'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        """Create new API key with auto-generated key."""
        validated_data['key'] = secrets.token_urlsafe(32)
        return super().create(validated_data)


class UserStatsSerializer(serializers.Serializer):
    """Serializer for user statistics."""
    
    whatsapp_instances = serializers.IntegerField()
    scheduled_messages = serializers.IntegerField()
    message_templates = serializers.IntegerField()
    total_messages_sent = serializers.IntegerField()
    messages_sent_this_month = serializers.IntegerField()


class SubscriptionInfoSerializer(serializers.Serializer):
    """Serializer for subscription information."""
    
    plan_name = serializers.CharField()
    status = serializers.CharField()
    current_period_end = serializers.DateTimeField()
    messages_sent_this_month = serializers.IntegerField()
    messages_limit = serializers.IntegerField()
    usage_percentage = serializers.FloatField()


class DashboardSerializer(serializers.Serializer):
    """Serializer for dashboard data."""
    
    user = UserSerializer()
    statistics = UserStatsSerializer()
    subscription = SubscriptionInfoSerializer(allow_null=True)