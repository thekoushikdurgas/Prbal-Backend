from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import ServiceCategory, ServiceSubCategory, Service, ServiceRequest

User = get_user_model()

class ServiceCategoryTestCase(APITestCase):
    """Test cases for Service Category endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='testpass123',
            user_type='admin',
            is_staff=True,
            is_superuser=True
        )
        
        self.regular_user = User.objects.create_user(
            username='user@test.com',
            email='user@test.com',
            password='testpass123',
            user_type='customer'
        )
        
        # Create test category
        self.category = ServiceCategory.objects.create(
            name='Test Category',
            description='Test category description',
            sort_order=1,
            is_active=True
        )
        
        # Setup authentication
        pass
    
    def test_list_categories_anonymous(self):
        """Test listing categories as anonymous user"""
        url = reverse('service-category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_list_categories_with_filters(self):
        """Test listing categories with active_only filter"""
        # Create inactive category
        ServiceCategory.objects.create(
            name='Inactive Category',
            description='Inactive category',
            is_active=False
        )
        
        url = reverse('service-category-list')
        response = self.client.get(url, {'active_only': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        response = self.client.get(url, {'active_only': 'false'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_get_category_detail(self):
        """Test retrieving category details"""
        url = reverse('service-category-detail', kwargs={'pk': self.category.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Category')
    
    def test_create_category_admin(self):
        """Test creating category as admin"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('service-category-list')
        data = {
            'name': 'New Category',
            'description': 'New category description',
            'sort_order': 2,
            'is_active': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ServiceCategory.objects.count(), 2)
    
    def test_create_category_unauthorized(self):
        """Test creating category as regular user (should fail)"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('service-category-list')
        data = {
            'name': 'New Category',
            'description': 'New category description'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_category_admin(self):
        """Test updating category as admin"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('service-category-detail', kwargs={'pk': self.category.id})
        data = {
            'name': 'Updated Category',
            'description': 'Updated description',
            'sort_order': 3,
            'is_active': True
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Updated Category')
    
    def test_partial_update_category_admin(self):
        """Test partially updating category as admin"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('service-category-detail', kwargs={'pk': self.category.id})
        data = {'description': 'Partially updated description'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()
        self.assertEqual(self.category.description, 'Partially updated description')
    
    def test_delete_category_admin(self):
        """Test deleting category as admin"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('service-category-detail', kwargs={'pk': self.category.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ServiceCategory.objects.count(), 0)
    
    def test_category_statistics_admin(self):
        """Test category statistics endpoint as admin"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('service-category-statistics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_categories', response.data)
        self.assertIn('category_statistics', response.data)
    
    def test_category_statistics_unauthorized(self):
        """Test category statistics endpoint as regular user (should fail)"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('service-category-statistics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ServiceSubCategoryTestCase(APITestCase):
    """Test cases for Service SubCategory endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='testpass123',
            user_type='admin',
            is_staff=True,
            is_superuser=True
        )
        
        self.regular_user = User.objects.create_user(
            username='user@test.com',
            email='user@test.com',
            password='testpass123',
            user_type='customer'
        )
        
        # Create test category and subcategory
        self.category = ServiceCategory.objects.create(
            name='Test Category',
            description='Test category description',
            is_active=True
        )
        
        self.subcategory = ServiceSubCategory.objects.create(
            category=self.category,
            name='Test SubCategory',
            description='Test subcategory description',
            sort_order=1,
            is_active=True
        )
        
        # Setup authentication  
        pass
    
    def test_list_subcategories_anonymous(self):
        """Test listing subcategories as anonymous user"""
        url = reverse('service-subcategory-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_list_subcategories_with_filters(self):
        """Test listing subcategories with filters"""
        # Create inactive subcategory
        ServiceSubCategory.objects.create(
            category=self.category,
            name='Inactive SubCategory',
            description='Inactive subcategory',
            is_active=False
        )
        
        url = reverse('service-subcategory-list')
        
        # Test active_only filter
        response = self.client.get(url, {'active_only': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test category filter
        response = self.client.get(url, {'category': self.category.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_get_subcategory_detail(self):
        """Test retrieving subcategory details"""
        url = reverse('service-subcategory-detail', kwargs={'pk': self.subcategory.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test SubCategory')
    
    def test_create_subcategory_admin(self):
        """Test creating subcategory as admin"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('service-subcategory-list')
        data = {
            'category': self.category.id,
            'name': 'New SubCategory',
            'description': 'New subcategory description',
            'sort_order': 2,
            'is_active': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ServiceSubCategory.objects.count(), 2)
    
    def test_create_subcategory_unauthorized(self):
        """Test creating subcategory as regular user (should fail)"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('service-subcategory-list')
        data = {
            'category': self.category.id,
            'name': 'New SubCategory',
            'description': 'New subcategory description'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_subcategory_admin(self):
        """Test updating subcategory as admin"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('service-subcategory-detail', kwargs={'pk': self.subcategory.id})
        data = {
            'category': self.category.id,
            'name': 'Updated SubCategory',
            'description': 'Updated description',
            'sort_order': 3,
            'is_active': True
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.subcategory.refresh_from_db()
        self.assertEqual(self.subcategory.name, 'Updated SubCategory')
    
    def test_partial_update_subcategory_admin(self):
        """Test partially updating subcategory as admin"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('service-subcategory-detail', kwargs={'pk': self.subcategory.id})
        data = {'description': 'Partially updated description'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.subcategory.refresh_from_db()
        self.assertEqual(self.subcategory.description, 'Partially updated description')
    
    def test_delete_subcategory_admin(self):
        """Test deleting subcategory as admin"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('service-subcategory-detail', kwargs={'pk': self.subcategory.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ServiceSubCategory.objects.count(), 0)
