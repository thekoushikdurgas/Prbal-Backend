from django.db import models
from django.conf import settings
import uuid
from services.models import ServiceCategory

# Create your models here.
class ProductCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    icon = models.ImageField(upload_to='product_category_icons/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Product Category'
        verbose_name_plural = 'Product Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Product(models.Model):
    """Represents products or pre-packaged services available in the marketplace"""
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('pending', 'Pending Approval'),
        ('inactive', 'Inactive'),
        ('out_of_stock', 'Out of Stock'),
    )
    
    PRODUCT_TYPE_CHOICES = (
        ('physical', 'Physical Product'),
        ('digital', 'Digital Product'),
        ('subscription', 'Subscription'),
        ('packaged_service', 'Packaged Service'),
    )
    
    # Primary key and relationship fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier for the product")
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products', help_text="User selling this product")
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products', help_text="Product category")
    related_service_category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, related_name='related_products', null=True, blank=True, help_text="Related service category if applicable")
    
    # Basic product information
    name = models.CharField(max_length=200, help_text="Product name")
    description = models.TextField(help_text="Product description")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Product price")
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Discounted price if applicable")
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, help_text="Type of product")
    
    # Inventory management
    stock_quantity = models.IntegerField(default=0, help_text="Available quantity in stock")
    
    # Media and details
    images = models.JSONField(default=list, blank=True, help_text='List of image URLs')
    features = models.JSONField(default=list, blank=True, help_text='List of product features')
    specifications = models.JSONField(default=dict, blank=True, help_text='Product specifications as key-value pairs')
    
    # Status and visibility
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', help_text="Current status of the product")
    is_featured = models.BooleanField(default=False, help_text="Whether product is featured in the marketplace")
    
    # Ratings and reviews
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0, help_text="Average rating for the product")
    reviews_count = models.PositiveIntegerField(default=0, help_text="Count of reviews for the product")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
    
    def __str__(self):
        return self.name
