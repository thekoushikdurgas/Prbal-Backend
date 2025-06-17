from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .tokens import CustomRefreshToken
from .models import AccessToken

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


class UserAccessTokenRevokeAllViewTestCase(APITestCase):
    """Test cases for the UserAccessTokenRevokeAllView endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            user_type='customer'
        )
        self.user.set_pin('1234')
        self.user.save()
        
        self.revoke_all_url = reverse('user-tokens-revoke-all')
        
        # Create multiple access tokens for the user
        self.token1 = AccessToken.objects.create(
            user=self.user,
            token_jti='token1',
            device_type='web',
            device_name='Chrome Browser',
            ip_address='192.168.1.1'
        )
        self.token2 = AccessToken.objects.create(
            user=self.user,
            token_jti='token2',
            device_type='mobile',
            device_name='iPhone App',
            ip_address='192.168.1.2'
        )
        self.token3 = AccessToken.objects.create(
            user=self.user,
            token_jti='token3',
            device_type='desktop',
            device_name='Desktop App',
            ip_address='192.168.1.3'
        )
        
        # Create one inactive token that should not be affected
        self.inactive_token = AccessToken.objects.create(
            user=self.user,
            token_jti='inactive_token',
            device_type='tablet',
            device_name='iPad App',
            ip_address='192.168.1.4',
            is_active=False
        )
    
    def get_auth_header(self, user):
        """Helper method to get authentication header for a user"""
        refresh = CustomRefreshToken.for_user(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}
    
    def test_revoke_all_tokens_success(self):
        """Test successful revocation of all active tokens"""
        auth_header = self.get_auth_header(self.user)
        response = self.client.post(self.revoke_all_url, **auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['revoked_count'], 3)
        self.assertIn('All active tokens revoked successfully', response.data['message'])
        
        # Verify all active tokens are now inactive
        self.token1.refresh_from_db()
        self.token2.refresh_from_db()
        self.token3.refresh_from_db()
        self.inactive_token.refresh_from_db()
        
        self.assertFalse(self.token1.is_active)
        self.assertFalse(self.token2.is_active)
        self.assertFalse(self.token3.is_active)
        self.assertFalse(self.inactive_token.is_active)  # Should remain inactive
    
    def test_revoke_all_tokens_no_active_tokens(self):
        """Test revoke all when user has no active tokens"""
        # Mark all tokens as inactive first
        AccessToken.objects.filter(user=self.user).update(is_active=False)
        
        auth_header = self.get_auth_header(self.user)
        response = self.client.post(self.revoke_all_url, **auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['revoked_count'], 0)
        self.assertIn('No active tokens to revoke', response.data['message'])
    
    def test_revoke_all_tokens_unauthenticated(self):
        """Test that unauthenticated requests are denied"""
        response = self.client.post(self.revoke_all_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_revoke_all_tokens_only_affects_current_user(self):
        """Test that revoking all tokens only affects the authenticated user's tokens"""
        # Create another user with tokens
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@test.com',
            user_type='provider'
        )
        other_user.set_pin('5678')
        other_user.save()
        
        other_token = AccessToken.objects.create(
            user=other_user,
            token_jti='other_token',
            device_type='web',
            device_name='Other Browser',
            ip_address='192.168.1.5'
        )
        
        # Revoke all tokens for the first user
        auth_header = self.get_auth_header(self.user)
        response = self.client.post(self.revoke_all_url, **auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['revoked_count'], 3)
        
        # Verify other user's token is still active
        other_token.refresh_from_db()
        self.assertTrue(other_token.is_active)
    
    def test_response_structure(self):
        """Test that response has correct structure"""
        auth_header = self.get_auth_header(self.user)
        response = self.client.post(self.revoke_all_url, **auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        self.assertIn('message', response.data)
        self.assertIn('revoked_count', response.data)
        self.assertIsInstance(response.data['revoked_count'], int)


class UserSearchByPhoneViewTestCase(APITestCase):
    """Test cases for the UserSearchByPhoneView endpoint - both GET and POST methods"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users with different phone numbers
        self.customer_user = User.objects.create_user(
            username='customer1',
            email='customer1@test.com',
            phone_number='+1234567890',
            user_type='customer'
        )
        
        self.provider_user = User.objects.create_user(
            username='provider1',
            email='provider1@test.com',
            phone_number='+1987654321',
            user_type='provider'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin1',
            email='admin1@test.com',
            phone_number='+1555123456',
            user_type='admin',
            is_staff=True
        )
        
        # User without phone number
        self.user_no_phone = User.objects.create_user(
            username='nophone',
            email='nophone@test.com',
            user_type='customer'
        )
        
        self.search_by_phone_url = reverse('user-search-by-phone')
    
    def test_get_search_by_phone_exact_match(self):
        """Test GET method with exact phone number match"""
        response = self.client.get(f"{self.search_by_phone_url}?phone_number={self.customer_user.phone_number}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('User found with exact phone match', response.data['message'])
        self.assertEqual(response.data['data']['user']['id'], str(self.customer_user.id))
        self.assertEqual(response.data['data']['search_details']['match_type'], 'exact')
    
    def test_get_search_by_phone_partial_match(self):
        """Test GET method with partial phone number match"""
        # Search with partial phone number
        partial_phone = self.provider_user.phone_number[-4:]  # Last 4 digits
        response = self.client.get(f"{self.search_by_phone_url}?phone_number={partial_phone}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('user(s) with similar phone numbers', response.data['message'])
        self.assertEqual(response.data['data']['search_details']['match_type'], 'partial')
        self.assertGreater(len(response.data['data']['users']), 0)
    
    def test_get_search_by_phone_no_match(self):
        """Test GET method with no phone number match"""
        response = self.client.get(f"{self.search_by_phone_url}?phone_number=+9999999999")
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['status'], 'error')
        self.assertIn('No users found', response.data['message'])
    
    def test_get_search_by_phone_missing_parameter(self):
        """Test GET method without phone number parameter"""
        response = self.client.get(self.search_by_phone_url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
        self.assertIn('Phone number is required as a query parameter', response.data['message'])
        self.assertIn('example_usage', response.data['data'])
    
    def test_post_search_by_phone_exact_match(self):
        """Test POST method with exact phone number match"""
        data = {'phone_number': self.provider_user.phone_number}
        response = self.client.post(self.search_by_phone_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('User found with exact phone match', response.data['message'])
        self.assertEqual(response.data['data']['user']['id'], str(self.provider_user.id))
        self.assertEqual(response.data['data']['search_details']['match_type'], 'exact')
    
    def test_post_search_by_phone_missing_data(self):
        """Test POST method without phone number in request body"""
        response = self.client.post(self.search_by_phone_url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
        self.assertIn('Phone number is required in request body', response.data['message'])
        self.assertIn('example_usage', response.data['data'])
    
    def test_search_returns_correct_serializer_data(self):
        """Test that search returns appropriate user data based on user type"""
        # Test customer user data
        response = self.client.get(f"{self.search_by_phone_url}?phone_number={self.customer_user.phone_number}")
        customer_data = response.data['data']['user']
        
        expected_customer_fields = ['id', 'username', 'first_name', 'last_name', 'profile_picture',
                                  'bio', 'location', 'user_type', 'is_verified', 'created_at']
        for field in expected_customer_fields:
            self.assertIn(field, customer_data)
        
        # Test provider user data (should have additional fields)
        response = self.client.get(f"{self.search_by_phone_url}?phone_number={self.provider_user.phone_number}")
        provider_data = response.data['data']['user']
        
        expected_provider_fields = expected_customer_fields + ['rating', 'skills', 'total_bookings', 'services_count']
        for field in expected_provider_fields:
            self.assertIn(field, provider_data)
    
    def test_unauthenticated_access_allowed(self):
        """Test that unauthenticated users can access the endpoint"""
        # GET method
        response = self.client.get(f"{self.search_by_phone_url}?phone_number={self.customer_user.phone_number}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # POST method
        data = {'phone_number': self.provider_user.phone_number}
        response = self.client.post(self.search_by_phone_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_authenticated_access_also_works(self):
        """Test that authenticated users can also access the endpoint"""
        # Create an authenticated user
        auth_user = User.objects.create_user(
            username='authuser',
            email='auth@test.com',
            user_type='customer'
        )
        self.client.force_authenticate(user=auth_user)
        
        # GET method
        response = self.client.get(f"{self.search_by_phone_url}?phone_number={self.customer_user.phone_number}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # POST method
        data = {'phone_number': self.provider_user.phone_number}
        response = self.client.post(self.search_by_phone_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_search_response_structure(self):
        """Test that both GET and POST methods return standardized response structure"""
        # GET method
        response = self.client.get(f"{self.search_by_phone_url}?phone_number={self.customer_user.phone_number}")
        self.assertIn('message', response.data)
        self.assertIn('data', response.data)
        self.assertIn('time', response.data)
        self.assertIn('statusCode', response.data)
        self.assertIn('search_details', response.data['data'])
        
        # POST method
        data = {'phone_number': self.provider_user.phone_number}
        response = self.client.post(self.search_by_phone_url, data, format='json')
        self.assertIn('message', response.data)
        self.assertIn('data', response.data)
        self.assertIn('time', response.data)
        self.assertIn('statusCode', response.data)
        self.assertIn('search_details', response.data['data'])


class UserTypeChangeViewTestCase(APITestCase):
    """Test cases for the UserTypeChangeView endpoint"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users of different types
        self.customer_user = User.objects.create_user(
            username='testcustomer',
            email='customer@test.com',
            phone_number='+1234567890',
            user_type='customer'
        )
        self.customer_user.set_pin('1234')
        self.customer_user.save()
        
        self.provider_user = User.objects.create_user(
            username='testprovider',
            email='provider@test.com',
            phone_number='+1987654321',
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
        
        # Customer without phone number for validation tests
        self.customer_no_phone = User.objects.create_user(
            username='customernophones',
            email='nophone@test.com',
            user_type='customer'
        )
        self.customer_no_phone.set_pin('1111')
        self.customer_no_phone.save()
        
        self.user_type_change_url = reverse('user-type-change')
    
    def get_auth_header(self, user):
        """Helper method to get authentication header for a user"""
        refresh = CustomRefreshToken.for_user(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}
    
    def test_get_user_type_change_info_customer(self):
        """Test getting user type change info for customer"""
        auth_header = self.get_auth_header(self.customer_user)
        response = self.client.get(self.user_type_change_url, **auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        data = response.data['data']
        self.assertEqual(data['current_type'], 'customer')
        self.assertEqual(data['current_type_display'], 'Customer')
        
        # Check available changes
        available_changes = data['available_changes']
        self.assertEqual(len(available_changes), 1)
        self.assertEqual(available_changes[0]['type'], 'provider')
        self.assertEqual(available_changes[0]['display'], 'Service Provider')
    
    def test_change_customer_to_provider_success(self):
        """Test successful change from customer to provider"""
        auth_header = self.get_auth_header(self.customer_user)
        data = {
            'to': 'provider',
            'reason': 'Want to offer services'
        }
        
        response = self.client.post(self.user_type_change_url, data, **auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['from'], 'customer')
        self.assertEqual(response.data['to'], 'provider')
        self.assertEqual(response.data['status'], 'success')
        
        # Verify user type changed in database
        self.customer_user.refresh_from_db()
        self.assertEqual(self.customer_user.user_type, 'provider')
    
    def test_change_to_same_type_fails(self):
        """Test that changing to same type fails"""
        auth_header = self.get_auth_header(self.customer_user)
        data = {'to': 'customer'}
        
        response = self.client.post(self.user_type_change_url, data, **auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You are already a', str(response.data))
    
    def test_customer_to_provider_requires_phone(self):
        """Test that customer to provider change requires phone number"""
        auth_header = self.get_auth_header(self.customer_no_phone)
        data = {'to': 'provider'}
        
        response = self.client.post(self.user_type_change_url, data, **auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Phone number is required', str(response.data))
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied"""
        response = self.client.get(self.user_type_change_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.client.post(self.user_type_change_url, {'to': 'provider'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_change_provider_to_customer_success(self):
        """Test successful change from provider to customer - preserves provider data"""
        # Set up provider with some data
        self.provider_user.skills = {'programming': 'Python', 'design': 'UI/UX'}
        self.provider_user.rating = 4.5
        self.provider_user.total_bookings = 25
        self.provider_user.save()
        
        auth_header = self.get_auth_header(self.provider_user)
        data = {
            'to': 'customer',
            'reason': 'Want to focus on being a customer for now'
        }
        
        response = self.client.post(self.user_type_change_url, data, **auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['from'], 'provider')
        self.assertEqual(response.data['to'], 'customer')
        
        # Verify user type changed but provider data is preserved
        self.provider_user.refresh_from_db()
        self.assertEqual(self.provider_user.user_type, 'customer')
        # Provider data should be preserved since user can be both
        self.assertEqual(self.provider_user.skills, {'programming': 'Python', 'design': 'UI/UX'})
        self.assertEqual(self.provider_user.rating, 4.5)
        self.assertEqual(self.provider_user.total_bookings, 25)
    
    def test_customer_with_provider_history_keeps_data(self):
        """Test that customer with provider history keeps their provider data when switching back"""
        # Set up customer who previously was a provider (has provider data)
        self.customer_user.skills = {'cooking': 'Italian cuisine', 'cleaning': 'Deep cleaning'}
        self.customer_user.rating = 4.8
        self.customer_user.total_bookings = 15
        self.customer_user.save()
        
        auth_header = self.get_auth_header(self.customer_user)
        data = {
            'to': 'provider',
            'reason': 'Want to start providing services again'
        }
        
        response = self.client.post(self.user_type_change_url, data, **auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['from'], 'customer')
        self.assertEqual(response.data['to'], 'provider')
        
        # Verify user type changed and previous provider data is preserved
        self.customer_user.refresh_from_db()
        self.assertEqual(self.customer_user.user_type, 'provider')
        # Should keep existing provider data
        self.assertEqual(self.customer_user.skills, {'cooking': 'Italian cuisine', 'cleaning': 'Deep cleaning'})
        self.assertEqual(self.customer_user.rating, 4.8)
        self.assertEqual(self.customer_user.total_bookings, 15)
    
    def test_new_customer_to_provider_initializes_empty_skills(self):
        """Test that new customer (no provider history) gets empty skills when becoming provider"""
        # Ensure customer has no skills set (None)
        self.customer_user.skills = None
        self.customer_user.save()
        
        auth_header = self.get_auth_header(self.customer_user)
        data = {
            'to': 'provider',
            'reason': 'Want to start providing services'
        }
        
        response = self.client.post(self.user_type_change_url, data, **auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify user type changed and skills initialized as empty dict
        self.customer_user.refresh_from_db()
        self.assertEqual(self.customer_user.user_type, 'provider')
        self.assertEqual(self.customer_user.skills, {})
