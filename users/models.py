from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings

class User(AbstractUser):
    class UserType(models.TextChoices):
        CUSTOMER = 'CUSTOMER', 'Customer'
        PROVIDER = 'PROVIDER', 'Service Provider'
    
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.CUSTOMER
    )
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'phone', 'user_type']

    def __str__(self):
        return self.email

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class BaseProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(class)s"
    )
    full_name = models.CharField(max_length=255)
    address = models.TextField()
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class CustomerProfile(BaseProfile):
    preferred_service_area = models.CharField(max_length=255, blank=True)
    preferred_communication = models.CharField(
        max_length=20,
        choices=[
            ('EMAIL', 'Email'),
            ('PHONE', 'Phone'),
            ('BOTH', 'Both')
        ],
        default='EMAIL'
    )

    def __str__(self):
        return f"Customer Profile - {self.full_name}"

class ServiceProviderProfile(BaseProfile):
    skills = models.ManyToManyField(Skill, related_name='service_providers')
    service_area = models.CharField(max_length=255)
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    availability = models.JSONField(default=dict)  # Store availability schedule as JSON
    required_tools = models.TextField(blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    business_registration_number = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Service Provider Profile - {self.full_name}"

    @property
    def review_stats(self):
        from services.models import Review
        reviews = Review.objects.filter(provider=self.user)
        total_reviews = reviews.count()
        
        if total_reviews == 0:
            return {
                'average_rating': 0.0,
                'total_reviews': 0,
                'rating_distribution': {
                    '5': 0, '4': 0, '3': 0, '2': 0, '1': 0
                }
            }
        
        # Calculate average rating
        average_rating = reviews.aggregate(
            avg_rating=models.Avg('rating')
        )['avg_rating'] or 0.0
        
        # Calculate rating distribution
        rating_distribution = dict(
            reviews.values_list('rating')
            .annotate(count=models.Count('rating'))
            .values_list('rating', 'count')
        )
        
        # Ensure all ratings are represented
        for i in range(1, 6):
            if i not in rating_distribution:
                rating_distribution[i] = 0
        
        return {
            'average_rating': round(float(average_rating), 1),
            'total_reviews': total_reviews,
            'rating_distribution': rating_distribution
        }

    @property
    def recent_reviews(self):
        from services.models import Review
        return Review.objects.filter(
            provider=self.user
        ).select_related('customer').order_by('-created_at')[:5]
