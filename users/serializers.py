from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Skill, CustomerProfile, ServiceProviderProfile

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'phone', 'user_type', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class UserProfileSerializer(serializers.ModelSerializer):
    """Basic user profile serializer with minimal information"""
    full_name = serializers.SerializerMethodField()
    user_type = serializers.CharField(read_only=True)
    profile_image = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'email', 'phone',
            'user_type', 'profile_image', 'is_verified'
        ]
        read_only_fields = ['email', 'is_verified']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.email

class UserSimpleSerializer(serializers.ModelSerializer):
    """Minimal user information serializer"""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'full_name', 'user_type']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.email

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'

class CustomerProfileSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = CustomerProfile
        fields = '__all__'
        read_only_fields = ['user']

class ServiceProviderProfileSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    skill_ids = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(),
        many=True,
        write_only=True,
        source='skills'
    )
    review_stats = serializers.SerializerMethodField()
    recent_reviews = serializers.SerializerMethodField()

    class Meta:
        model = ServiceProviderProfile
        fields = '__all__'
        read_only_fields = ['user']

    def get_review_stats(self, obj):
        return obj.review_stats

    def get_recent_reviews(self, obj):
        from services.serializers import ReviewListSerializer
        reviews = obj.recent_reviews
        return ReviewListSerializer(reviews, many=True).data

class ProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['profile_image'] 