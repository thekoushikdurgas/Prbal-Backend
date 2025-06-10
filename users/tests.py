from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .tokens import CustomRefreshToken

User = get_user_model()


class UserTypeViewTestCase(APITestCase):
    """Test cases for the UserTypeView endpoint"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users of different types
        self.customer_user = User.objects.create_user(
            username='testcustomer',
            email='customer@test.com',
            user_type='customer'
        )
        self.customer_user.set_pin('1234')
        self.customer_user.save()
        
        self.provider_user = User.objects.create_user(
            username='testprovider',
            email='provider@test.com',
            user_type='provider'
        )
        self.provider_user.set_pin('5678')
        self.provider_user.save()
        
        self.admin_user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            user_type='admin',
            is_staff=True
        )
        self.admin_user.set_pin('9999')
        self.admin_user.save()
        
        self.user_type_url = reverse('user-type')
    
    def get_auth_header(self, user):
        """Helper method to get authentication header for a user"""
        refresh = CustomRefreshToken.for_user(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}
    
    def test_customer_user_type_detection(self):
        """Test user type detection for customer user"""
        auth_header = self.get_auth_header(self.customer_user)
        response = self.client.get(self.user_type_url, **auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['user_type'], 'customer')
        self.assertEqual(response.data['data']['user_type_display'], 'Customer')
        self.assertTrue(response.data['data']['is_customer'])
        self.assertFalse(response.data['data']['is_provider'])
        self.assertFalse(response.data['data']['is_admin'])
        self.assertIn('Customer', response.data['message'])
    
    def test_provider_user_type_detection(self):
        """Test user type detection for provider user"""
        auth_header = self.get_auth_header(self.provider_user)
        response = self.client.get(self.user_type_url, **auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['user_type'], 'provider')
        self.assertEqual(response.data['data']['user_type_display'], 'Service Provider')
        self.assertFalse(response.data['data']['is_customer'])
        self.assertTrue(response.data['data']['is_provider'])
        self.assertFalse(response.data['data']['is_admin'])
        self.assertIn('Service Provider', response.data['message'])
    
    def test_admin_user_type_detection(self):
        """Test user type detection for admin user"""
        auth_header = self.get_auth_header(self.admin_user)
        response = self.client.get(self.user_type_url, **auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['user_type'], 'admin')
        self.assertEqual(response.data['data']['user_type_display'], 'Administrator')
        self.assertFalse(response.data['data']['is_customer'])
        self.assertFalse(response.data['data']['is_provider'])
        self.assertTrue(response.data['data']['is_admin'])
        self.assertIn('Administrator', response.data['message'])
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied"""
        response = self.client.get(self.user_type_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_response_structure(self):
        """Test that response has correct structure"""
        auth_header = self.get_auth_header(self.customer_user)
        response = self.client.get(self.user_type_url, **auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check main response structure
        self.assertIn('data', response.data)
        self.assertIn('message', response.data)
        self.assertIn('status', response.data)
        
        # Check data structure
        data = response.data['data']
        expected_fields = [
            'user_id', 'username', 'user_type', 'user_type_display',
            'is_customer', 'is_provider', 'is_admin'
        ]
        for field in expected_fields:
            self.assertIn(field, data)
    
    def test_user_id_and_username_in_response(self):
        """Test that user ID and username are correctly returned"""
        auth_header = self.get_auth_header(self.customer_user)
        response = self.client.get(self.user_type_url, **auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['user_id'], str(self.customer_user.id))
        self.assertEqual(response.data['data']['username'], self.customer_user.username)


class UserTypeUtilityTestCase(TestCase):
    """Test cases for user type related utility functions"""
    
    def setUp(self):
        """Set up test data"""
        self.customer_user = User.objects.create_user(
            username='customer',
            email='customer@test.com',
            user_type='customer'
        )
        
        self.provider_user = User.objects.create_user(
            username='provider',
            email='provider@test.com',
            user_type='provider'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            user_type='admin'
        )
    
    def test_get_user_type_display(self):
        """Test get_user_type_display method"""
        self.assertEqual(self.customer_user.get_user_type_display(), 'Customer')
        self.assertEqual(self.provider_user.get_user_type_display(), 'Service Provider')
        self.assertEqual(self.admin_user.get_user_type_display(), 'Administrator')
    
    def test_user_type_choices(self):
        """Test that user type choices are correct"""
        choices = dict(User.USER_TYPE_CHOICES)
        self.assertEqual(choices['customer'], 'Customer')
        self.assertEqual(choices['provider'], 'Service Provider')
        self.assertEqual(choices['admin'], 'Administrator')
