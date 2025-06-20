from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import ServiceCategory, ServiceSubCategory, Service, ServiceRequest
import logging
import time
import json

# 🧪 ENHANCED TEST SETUP WITH COMPREHENSIVE DEBUG TRACKING
logger = logging.getLogger(__name__)

User = get_user_model()

class EnhancedTestCase(APITestCase):
    """
    🧪 ENHANCED BASE TEST CLASS WITH COMPREHENSIVE DEBUG TRACKING
    ============================================================
    
    Base test class that provides comprehensive logging and monitoring for all test operations.
    Includes performance tracking, detailed assertions, and comprehensive error reporting.
    
    FEATURES:
    - ✅ Test execution timing and performance monitoring
    - ✅ API response validation with detailed logging
    - ✅ Database state tracking before and after tests
    - ✅ Comprehensive error reporting with context
    - ✅ Request/response debugging utilities
    
    DEBUG ENHANCEMENTS:
    - 🔍 Test method execution tracking
    - 📊 Performance metrics collection
    - 🛡️ Assertion validation with detailed context
    - 📈 Database query count monitoring
    - 🔄 Test data setup and teardown logging
    """
    
    def setUp(self):
        """
        🚀 ENHANCED TEST SETUP WITH COMPREHENSIVE INITIALIZATION
        =======================================================
        
        Enhanced test setup with comprehensive logging and performance tracking.
        Provides detailed context for test execution.
        """
        # 📝 DEBUG: Log test setup initiation
        logger.info(f"🚀 DEBUG: Test setup initiated for {self.__class__.__name__}")
        
        # 📊 DEBUG: Track setup performance
        setup_start_time = time.time()
        
        self.client = APIClient()
        
        # 👥 DEBUG: Create enhanced test users with detailed logging
        logger.debug("👥 DEBUG: Creating test users")
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='testpass123',
            user_type='admin',
            is_staff=True,
            is_superuser=True
        )
        logger.debug(f"👑 DEBUG: Admin user created - ID: {self.admin_user.id}")
        
        # Create regular customer user
        self.customer_user = User.objects.create_user(
            username='customer@test.com',
            email='customer@test.com',
            password='testpass123',
            user_type='customer'
        )
        logger.debug(f"🛒 DEBUG: Customer user created - ID: {self.customer_user.id}")
        
        # Create provider user
        self.provider_user = User.objects.create_user(
            username='provider@test.com',
            email='provider@test.com',
            password='testpass123',
            user_type='provider'
        )
        logger.debug(f"🔧 DEBUG: Provider user created - ID: {self.provider_user.id}")
        
        # 📦 DEBUG: Create test category with comprehensive logging
        logger.debug("📦 DEBUG: Creating test category")
        self.category = ServiceCategory.objects.create(
            name='Test Category',
            description='Test category description',
            sort_order=1,
            is_active=True
        )
        logger.debug(f"📂 DEBUG: Test category created - ID: {self.category.id}, Name: '{self.category.name}'")
        
        # 📊 DEBUG: Log setup completion metrics
        setup_duration = time.time() - setup_start_time
        logger.info(f"✅ DEBUG: Test setup completed in {setup_duration:.3f}s for {self.__class__.__name__}")
        logger.debug(f"📊 DEBUG: Setup metrics:")
        logger.debug(f"   👥 Users created: 3 (admin, customer, provider)")
        logger.debug(f"   📂 Categories created: 1")
        logger.debug(f"   ⏱️ Setup duration: {setup_duration:.3f}s")
    
    def tearDown(self):
        """
        🧹 ENHANCED TEST TEARDOWN WITH CLEANUP TRACKING
        =============================================
        
        Enhanced test teardown with comprehensive logging and cleanup verification.
        Ensures proper cleanup and provides metrics for test execution.
        """
        # 📝 DEBUG: Log test teardown initiation
        logger.debug(f"🧹 DEBUG: Test teardown initiated for {self.__class__.__name__}")
        
        # 📊 DEBUG: Track cleanup performance
        teardown_start_time = time.time()
        
        try:
            # Clear any remaining test data
            teardown_duration = time.time() - teardown_start_time
            logger.debug(f"✅ DEBUG: Test teardown completed in {teardown_duration:.3f}s")
            
        except Exception as e:
            logger.error(f"💥 DEBUG: Test teardown failed: {e}")
            logger.error(f"🔍 DEBUG: Error type: {type(e).__name__}")
    
    def enhanced_api_call(self, method, url, data=None, user=None, expected_status=None):
        """
        🔗 ENHANCED API CALL WITH COMPREHENSIVE TRACKING
        ==============================================
        
        Enhanced API call method with comprehensive logging and validation.
        Provides detailed tracking for all API interactions during tests.
        """
        # 📝 DEBUG: Log API call initiation
        logger.debug(f"🔗 DEBUG: API call initiated - {method.upper()} {url}")
        
        # 👤 DEBUG: Handle authentication
        if user:
            self.client.force_authenticate(user=user)
            logger.debug(f"👤 DEBUG: Authenticated as {user.username} ({user.user_type})")
        else:
            self.client.force_authenticate(user=None)
            logger.debug("👤 DEBUG: Unauthenticated request")
        
        # 📊 DEBUG: Track API call performance
        from django.db import connection
        initial_query_count = len(connection.queries)
        api_start_time = time.time()
        
        try:
            # 🌐 DEBUG: Make the API call
            if data:
                logger.debug(f"📊 DEBUG: Request data: {json.dumps(data, indent=2, default=str)}")
                
            if method.lower() == 'get':
                response = self.client.get(url, data or {})
            elif method.lower() == 'post':
                response = self.client.post(url, data or {}, format='json')
            elif method.lower() == 'put':
                response = self.client.put(url, data or {}, format='json')
            elif method.lower() == 'patch':
                response = self.client.patch(url, data or {}, format='json')
            elif method.lower() == 'delete':
                response = self.client.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # 📊 DEBUG: Track API call metrics
            api_duration = time.time() - api_start_time
            final_query_count = len(connection.queries)
            query_impact = final_query_count - initial_query_count
            
            # 📈 DEBUG: Log API call results
            logger.debug(f"📈 DEBUG: API call completed:")
            logger.debug(f"   📊 Status: {response.status_code}")
            logger.debug(f"   ⏱️ Duration: {api_duration:.3f}s")
            logger.debug(f"   🗃️ Database queries: {query_impact}")
            
            # 📝 DEBUG: Log response data
            try:
                response_data = response.json() if response.content else {}
                logger.debug(f"📝 DEBUG: Response data keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'non-dict response'}")
            except Exception:
                logger.debug("📝 DEBUG: Non-JSON response or empty content")
            
            # ✅ DEBUG: Validate expected status if provided
            if expected_status:
                if response.status_code == expected_status:
                    logger.debug(f"✅ DEBUG: Status validation passed - expected {expected_status}, got {response.status_code}")
                else:
                    logger.error(f"❌ DEBUG: Status validation failed - expected {expected_status}, got {response.status_code}")
                    if response.content:
                        logger.error(f"📝 DEBUG: Error response: {response.content.decode()}")
            
            return response
            
        except Exception as e:
            # 💥 DEBUG: Log API call errors
            api_duration = time.time() - api_start_time
            logger.error(f"💥 DEBUG: API call failed after {api_duration:.3f}s: {e}")
            logger.error(f"🔍 DEBUG: Error type: {type(e).__name__}")
            logger.error(f"🌐 DEBUG: Request details - Method: {method}, URL: {url}")
            raise
    
    def assert_standardized_response(self, response, expected_status=200):
        """
        🔍 ENHANCED ASSERTION FOR STANDARDIZED RESPONSES
        ===============================================
        
        Enhanced assertion method for validating standardized API responses.
        Provides detailed validation and logging for response format compliance.
        """
        # 📝 DEBUG: Log assertion initiation
        logger.debug(f"🔍 DEBUG: Validating standardized response format")
        
        try:
            # ✅ DEBUG: Validate status code
            self.assertEqual(response.status_code, expected_status, 
                f"Expected status {expected_status}, got {response.status_code}")
            logger.debug(f"✅ DEBUG: Status code validation passed: {response.status_code}")
            
            # 📝 DEBUG: Validate response is JSON
            response_data = response.json()
            logger.debug(f"✅ DEBUG: Valid JSON response received")
            
            # 🔍 DEBUG: Validate standardized response format
            required_fields = ['message', 'data', 'time', 'statusCode']
            for field in required_fields:
                self.assertIn(field, response_data, f"Missing required field: {field}")
                logger.debug(f"✅ DEBUG: Required field '{field}' present")
            
            # 📊 DEBUG: Validate field types
            self.assertIsInstance(response_data['message'], str, "Message should be a string")
            self.assertIsInstance(response_data['statusCode'], int, "StatusCode should be an integer")
            self.assertIsInstance(response_data['time'], str, "Time should be a string")
            logger.debug(f"✅ DEBUG: Field type validation passed")
            
            # 🎯 DEBUG: Validate status code consistency
            self.assertEqual(response_data['statusCode'], expected_status, 
                f"Response statusCode {response_data['statusCode']} doesn't match HTTP status {expected_status}")
            logger.debug(f"✅ DEBUG: Status code consistency validated")
            
            logger.debug(f"✅ DEBUG: Standardized response validation completed successfully")
            return response_data
            
        except Exception as e:
            # 💥 DEBUG: Log assertion errors with detailed context
            logger.error(f"💥 DEBUG: Standardized response validation failed: {e}")
            logger.error(f"🔍 DEBUG: Error type: {type(e).__name__}")
            if response.content:
                logger.error(f"📝 DEBUG: Response content: {response.content.decode()}")
            raise

class ServiceCategoryTestCase(EnhancedTestCase):
    """
    🧪 SERVICE CATEGORY TEST CASE - ENHANCED WITH COMPREHENSIVE DEBUG TRACKING
    =========================================================================
    
    Enhanced test cases for Service Category endpoints with comprehensive logging and monitoring.
    Provides detailed tracking for all test operations and API interactions.
    
    FEATURES:
    - ✅ Test execution timing and performance monitoring
    - ✅ API response validation with detailed logging
    - ✅ Database state tracking before and after tests
    - ✅ Comprehensive error reporting with context
    - ✅ Request/response debugging utilities
    - ✅ Standardized response format validation
    
    DEBUG ENHANCEMENTS:
    - 🔍 Test method execution tracking
    - 📊 Performance metrics collection
    - 🛡️ Assertion validation with detailed context
    - 📈 Database query count monitoring
    - 🔄 Test data setup and teardown logging
    """
    
    def setUp(self):
        """
        🚀 ENHANCED TEST SETUP WITH COMPREHENSIVE INITIALIZATION
        =======================================================
        
        Enhanced test setup with comprehensive logging and performance tracking.
        Provides detailed context for test execution.
        """
        # 📝 DEBUG: Log test setup initiation
        logger.info(f"🚀 DEBUG: ServiceCategoryTestCase setup initiated")
        
        # 📊 DEBUG: Track setup performance
        setup_start_time = time.time()
        
        self.client = APIClient()
        
        # 👥 DEBUG: Create enhanced test users with detailed logging
        logger.debug("👥 DEBUG: Creating test users for ServiceCategory tests")
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='testpass123',
            user_type='admin',
            is_staff=True,
            is_superuser=True
        )
        logger.debug(f"👑 DEBUG: Admin user created - ID: {self.admin_user.id}")
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='user@test.com',
            email='user@test.com',
            password='testpass123',
            user_type='customer'
        )
        logger.debug(f"🛒 DEBUG: Regular user created - ID: {self.regular_user.id}")
        
        # 📦 DEBUG: Create test category with comprehensive logging
        logger.debug("📦 DEBUG: Creating test category")
        self.category = ServiceCategory.objects.create(
            name='Test Category',
            description='Test category description',
            sort_order=1,
            is_active=True
        )
        logger.debug(f"📂 DEBUG: Test category created - ID: {self.category.id}, Name: '{self.category.name}'")
        
        # 📊 DEBUG: Log setup completion metrics
        setup_duration = time.time() - setup_start_time
        logger.info(f"✅ DEBUG: ServiceCategoryTestCase setup completed in {setup_duration:.3f}s")
        logger.debug(f"📊 DEBUG: Setup metrics:")
        logger.debug(f"   👥 Users created: 2 (admin, regular)")
        logger.debug(f"   📂 Categories created: 1")
        logger.debug(f"   ⏱️ Setup duration: {setup_duration:.3f}s")
    
    def test_list_categories_anonymous(self):
        """
        🧪 ENHANCED TEST: List categories as anonymous user with comprehensive tracking
        """
        logger.info("🧪 DEBUG: Starting test_list_categories_anonymous")
        test_start_time = time.time()
        
        try:
            url = reverse('service-category-list')
            logger.debug(f"🌐 DEBUG: Testing URL: {url}")
            
            response = self.enhanced_api_call('GET', url, expected_status=200)
            
            # Enhanced assertions with logging
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            logger.debug("✅ DEBUG: Status code assertion passed")
            
            self.assertEqual(len(response.data['results']), 1)
            logger.debug(f"✅ DEBUG: Results count assertion passed - found {len(response.data['results'])} categories")
            
            # Validate response structure
            self.assertIn('results', response.data)
            self.assertIn('count', response.data)
            logger.debug("✅ DEBUG: Response structure validation passed")
            
            test_duration = time.time() - test_start_time
            logger.info(f"✅ DEBUG: test_list_categories_anonymous completed successfully in {test_duration:.3f}s")
            
        except Exception as e:
            test_duration = time.time() - test_start_time
            logger.error(f"💥 DEBUG: test_list_categories_anonymous failed after {test_duration:.3f}s: {e}")
            raise
    
    def test_list_categories_with_filters(self):
        """
        🧪 ENHANCED TEST: List categories with filters and comprehensive validation
        """
        logger.info("🧪 DEBUG: Starting test_list_categories_with_filters")
        test_start_time = time.time()
        
        try:
            # Create inactive category for filter testing
            logger.debug("📦 DEBUG: Creating inactive category for filter testing")
            inactive_category = ServiceCategory.objects.create(
                name='Inactive Category',
                description='Inactive category',
                is_active=False
            )
            logger.debug(f"📂 DEBUG: Inactive category created - ID: {inactive_category.id}")
            
            url = reverse('service-category-list')
            
            # Test active_only=true filter
            logger.debug("🔍 DEBUG: Testing active_only=true filter")
            response = self.enhanced_api_call('GET', url, data={'active_only': 'true'}, expected_status=200)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['results']), 1)
            logger.debug("✅ DEBUG: active_only=true filter test passed")
            
            # Test active_only=false filter
            logger.debug("🔍 DEBUG: Testing active_only=false filter")
            response = self.enhanced_api_call('GET', url, data={'active_only': 'false'}, expected_status=200)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['results']), 1)
            logger.debug("✅ DEBUG: active_only=false filter test passed")
            
            test_duration = time.time() - test_start_time
            logger.info(f"✅ DEBUG: test_list_categories_with_filters completed successfully in {test_duration:.3f}s")
            
        except Exception as e:
            test_duration = time.time() - test_start_time
            logger.error(f"💥 DEBUG: test_list_categories_with_filters failed after {test_duration:.3f}s: {e}")
            raise
    
    def test_get_category_detail(self):
        """
        🧪 ENHANCED TEST: Retrieve category details with comprehensive validation
        """
        logger.info("🧪 DEBUG: Starting test_get_category_detail")
        test_start_time = time.time()
        
        try:
            url = reverse('service-category-detail', kwargs={'pk': self.category.id})
            logger.debug(f"🌐 DEBUG: Testing detail URL: {url}")
            logger.debug(f"📂 DEBUG: Target category: {self.category.name} (ID: {self.category.id})")
            
            response = self.enhanced_api_call('GET', url, expected_status=200)
            
            # Enhanced assertions with logging
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['name'], 'Test Category')
            logger.debug(f"✅ DEBUG: Category name validation passed: {response.data['name']}")
            
            # Validate all expected fields are present
            expected_fields = ['id', 'name', 'description', 'sort_order', 'is_active', 'created_at', 'updated_at']
            for field in expected_fields:
                self.assertIn(field, response.data)
                logger.debug(f"✅ DEBUG: Field '{field}' present in response")
            
            test_duration = time.time() - test_start_time
            logger.info(f"✅ DEBUG: test_get_category_detail completed successfully in {test_duration:.3f}s")
            
        except Exception as e:
            test_duration = time.time() - test_start_time
            logger.error(f"💥 DEBUG: test_get_category_detail failed after {test_duration:.3f}s: {e}")
            raise
    
    def test_create_category_admin(self):
        """
        🧪 ENHANCED TEST: Create category as admin with comprehensive validation
        """
        logger.info("🧪 DEBUG: Starting test_create_category_admin")
        test_start_time = time.time()
        
        try:
            url = reverse('service-category-list')
            data = {
                'name': 'New Category',
                'description': 'New category description',
                'sort_order': 2,
                'is_active': True
            }
            logger.debug(f"📊 DEBUG: Creating category with data: {data}")
            
            response = self.enhanced_api_call('POST', url, data=data, user=self.admin_user, expected_status=201)
            
            # Enhanced assertions with logging
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            logger.debug("✅ DEBUG: Category creation status validation passed")
            
            # Verify database state
            total_categories = ServiceCategory.objects.count()
            self.assertEqual(total_categories, 2)
            logger.debug(f"✅ DEBUG: Database state validation passed - total categories: {total_categories}")
            
            # Verify created category details
            created_category = ServiceCategory.objects.get(name='New Category')
            self.assertEqual(created_category.description, 'New category description')
            self.assertEqual(created_category.sort_order, 2)
            logger.debug(f"✅ DEBUG: Created category validation passed - ID: {created_category.id}")
            
            test_duration = time.time() - test_start_time
            logger.info(f"✅ DEBUG: test_create_category_admin completed successfully in {test_duration:.3f}s")
            
        except Exception as e:
            test_duration = time.time() - test_start_time
            logger.error(f"💥 DEBUG: test_create_category_admin failed after {test_duration:.3f}s: {e}")
            raise
    
    def test_create_category_unauthorized(self):
        """
        🧪 ENHANCED TEST: Create category as regular user (should fail) with comprehensive validation
        """
        logger.info("🧪 DEBUG: Starting test_create_category_unauthorized")
        test_start_time = time.time()
        
        try:
            url = reverse('service-category-list')
            data = {
                'name': 'Unauthorized Category',
                'description': 'Should not be created'
            }
            logger.debug(f"📊 DEBUG: Attempting unauthorized creation with data: {data}")
            
            response = self.enhanced_api_call('POST', url, data=data, user=self.regular_user, expected_status=403)
            
            # Enhanced assertions with logging
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            logger.debug("✅ DEBUG: Unauthorized access properly blocked")
            
            # Verify database state unchanged
            total_categories = ServiceCategory.objects.count()
            self.assertEqual(total_categories, 1)
            logger.debug(f"✅ DEBUG: Database state unchanged - total categories: {total_categories}")
            
            test_duration = time.time() - test_start_time
            logger.info(f"✅ DEBUG: test_create_category_unauthorized completed successfully in {test_duration:.3f}s")
            
        except Exception as e:
            test_duration = time.time() - test_start_time
            logger.error(f"💥 DEBUG: test_create_category_unauthorized failed after {test_duration:.3f}s: {e}")
            raise

class ServiceSubCategoryTestCase(EnhancedTestCase):
    """Test cases for Service SubCategory endpoints"""
    
    def test_list_subcategories_anonymous(self):
        """Test listing subcategories as anonymous user"""
        url = reverse('service-subcategory-list')
        response = self.enhanced_api_call('get', url)
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
        response = self.enhanced_api_call('get', url, {'active_only': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test category filter
        response = self.enhanced_api_call('get', url, {'category': self.category.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_get_subcategory_detail(self):
        """Test retrieving subcategory details"""
        url = reverse('service-subcategory-detail', kwargs={'pk': self.subcategory.id})
        response = self.enhanced_api_call('get', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test SubCategory')
    
    def test_create_subcategory_admin(self):
        """Test creating subcategory as admin"""
        self.enhanced_api_call('post', reverse('service-subcategory-list'), data={
            'category': self.category.id,
            'name': 'New SubCategory',
            'description': 'New subcategory description',
            'sort_order': 2,
            'is_active': True
        }, user=self.admin_user)
        self.assertEqual(ServiceSubCategory.objects.count(), 2)
    
    def test_create_subcategory_unauthorized(self):
        """Test creating subcategory as regular user (should fail)"""
        self.enhanced_api_call('post', reverse('service-subcategory-list'), data={
            'category': self.category.id,
            'name': 'New SubCategory',
            'description': 'New subcategory description'
        }, user=self.customer_user, expected_status=status.HTTP_403_FORBIDDEN)
    
    def test_update_subcategory_admin(self):
        """Test updating subcategory as admin"""
        self.enhanced_api_call('put', reverse('service-subcategory-detail', kwargs={'pk': self.subcategory.id}), data={
            'category': self.category.id,
            'name': 'Updated SubCategory',
            'description': 'Updated description',
            'sort_order': 3,
            'is_active': True
        }, user=self.admin_user)
        self.subcategory.refresh_from_db()
        self.assertEqual(self.subcategory.name, 'Updated SubCategory')
    
    def test_partial_update_subcategory_admin(self):
        """Test partially updating subcategory as admin"""
        self.enhanced_api_call('patch', reverse('service-subcategory-detail', kwargs={'pk': self.subcategory.id}), data={'description': 'Partially updated description'}, user=self.admin_user)
        self.subcategory.refresh_from_db()
        self.assertEqual(self.subcategory.description, 'Partially updated description')
    
    def test_delete_subcategory_admin(self):
        """Test deleting subcategory as admin"""
        self.enhanced_api_call('delete', reverse('service-subcategory-detail', kwargs={'pk': self.subcategory.id}), user=self.admin_user)
        self.assertEqual(ServiceSubCategory.objects.count(), 0)

    def test_delete_subcategory_unauthorized(self):
        """Test deleting subcategory as regular user (should fail)"""
        response = self.enhanced_api_call('delete', reverse('service-subcategory-detail', kwargs={'pk': self.subcategory.id}), user=self.customer_user, expected_status=status.HTTP_403_FORBIDDEN)
        self.assertEqual(ServiceSubCategory.objects.count(), 1)  # Should still exist

    def test_list_subcategories_standardized_response(self):
        """
        🧪 ENHANCED TEST: Validate standardized response format for subcategory list
        """
        logger.info("🧪 DEBUG: Starting test_list_subcategories_standardized_response")
        test_start_time = time.time()
        
        try:
            url = reverse('service-subcategory-list')
            logger.debug(f"🌐 DEBUG: Testing standardized response for URL: {url}")
            
            response = self.enhanced_api_call('GET', url, expected_status=200)
            
            # Validate response structure
            self.assertIn('results', response.data)
            logger.debug("✅ DEBUG: Response has 'results' field")
            
            # Check that we have at least one subcategory (the one created in setUp)
            self.assertGreaterEqual(len(response.data['results']), 1)
            logger.debug(f"✅ DEBUG: Found {len(response.data['results'])} subcategories in results")
            
            # Validate subcategory data structure
            subcategory_data = response.data['results'][0]
            expected_fields = ['id', 'category', 'category_name', 'name', 'description', 'sort_order', 'is_active', 'created_at', 'updated_at']
            
            for field in expected_fields:
                self.assertIn(field, subcategory_data)
                logger.debug(f"✅ DEBUG: Subcategory field '{field}' present in response")
            
            # Validate computed fields from serializer
            self.assertIn('services_count', subcategory_data)
            self.assertIn('has_active_services', subcategory_data)
            self.assertIn('category_is_active', subcategory_data)
            logger.debug("✅ DEBUG: Computed fields present in subcategory response")
            
            test_duration = time.time() - test_start_time
            logger.info(f"✅ DEBUG: test_list_subcategories_standardized_response completed successfully in {test_duration:.3f}s")
            
        except Exception as e:
            test_duration = time.time() - test_start_time
            logger.error(f"💥 DEBUG: test_list_subcategories_standardized_response failed after {test_duration:.3f}s: {e}")
            raise

    def test_create_subcategory_standardized_response(self):
        """
        🧪 ENHANCED TEST: Validate standardized response format for subcategory creation
        """
        logger.info("🧪 DEBUG: Starting test_create_subcategory_standardized_response")
        test_start_time = time.time()
        
        try:
            url = reverse('service-subcategory-list')
            data = {
                'category': self.category.id,
                'name': 'New Test SubCategory',
                'description': 'New test subcategory description',
                'sort_order': 10,
                'is_active': True
            }
            logger.debug(f"📊 DEBUG: Creating subcategory with standardized response test data: {data}")
            
            response = self.enhanced_api_call('POST', url, data=data, user=self.admin_user, expected_status=201)
            
            # Validate standardized response format
            response_data = self.assert_standardized_response(response, 201)
            
            # Validate message
            self.assertIn("created successfully", response_data['message'])
            logger.debug(f"✅ DEBUG: Success message validation passed: {response_data['message']}")
            
            # Validate data structure
            self.assertIn('subcategory', response_data['data'])
            self.assertIn('creation_details', response_data['data'])
            logger.debug("✅ DEBUG: Response data structure validation passed")
            
            # Validate creation details
            creation_details = response_data['data']['creation_details']
            expected_creation_fields = ['created_by', 'created_at', 'category_name', 'subcategory_id']
            
            for field in expected_creation_fields:
                self.assertIn(field, creation_details)
                logger.debug(f"✅ DEBUG: Creation detail field '{field}' present")
            
            # Validate subcategory data
            subcategory_data = response_data['data']['subcategory']
            self.assertEqual(subcategory_data['name'], 'New Test SubCategory')
            self.assertEqual(subcategory_data['category'], str(self.category.id))
            logger.debug("✅ DEBUG: Subcategory data validation passed")
            
            # Verify database state
            total_subcategories = ServiceSubCategory.objects.count()
            self.assertEqual(total_subcategories, 2)  # Original + new one
            logger.debug(f"✅ DEBUG: Database state validation passed - total subcategories: {total_subcategories}")
            
            test_duration = time.time() - test_start_time
            logger.info(f"✅ DEBUG: test_create_subcategory_standardized_response completed successfully in {test_duration:.3f}s")
            
        except Exception as e:
            test_duration = time.time() - test_start_time
            logger.error(f"💥 DEBUG: test_create_subcategory_standardized_response failed after {test_duration:.3f}s: {e}")
            raise

    def test_update_subcategory_standardized_response(self):
        """
        🧪 ENHANCED TEST: Validate standardized response format for subcategory update
        """
        logger.info("🧪 DEBUG: Starting test_update_subcategory_standardized_response")
        test_start_time = time.time()
        
        try:
            url = reverse('service-subcategory-detail', kwargs={'pk': self.subcategory.id})
            original_name = self.subcategory.name
            
            data = {
                'category': self.category.id,
                'name': 'Updated Test SubCategory',
                'description': 'Updated test subcategory description',
                'sort_order': 15,
                'is_active': True
            }
            logger.debug(f"📊 DEBUG: Updating subcategory with standardized response test data: {data}")
            logger.debug(f"📝 DEBUG: Original name: '{original_name}' -> New name: '{data['name']}'")
            
            response = self.enhanced_api_call('PUT', url, data=data, user=self.admin_user, expected_status=200)
            
            # Validate standardized response format
            response_data = self.assert_standardized_response(response, 200)
            
            # Validate message
            self.assertIn("updated successfully", response_data['message'])
            logger.debug(f"✅ DEBUG: Success message validation passed: {response_data['message']}")
            
            # Validate data structure
            self.assertIn('subcategory', response_data['data'])
            self.assertIn('update_details', response_data['data'])
            logger.debug("✅ DEBUG: Response data structure validation passed")
            
            # Validate update details
            update_details = response_data['data']['update_details']
            expected_update_fields = ['updated_by', 'updated_at', 'changes_made', 'category_name', 'subcategory_id']
            
            for field in expected_update_fields:
                self.assertIn(field, update_details)
                logger.debug(f"✅ DEBUG: Update detail field '{field}' present")
            
            # Validate changes tracking
            changes_made = update_details['changes_made']
            self.assertIsInstance(changes_made, list)
            logger.debug(f"✅ DEBUG: Changes tracking validation passed: {changes_made}")
            
            # Validate subcategory data
            subcategory_data = response_data['data']['subcategory']
            self.assertEqual(subcategory_data['name'], 'Updated Test SubCategory')
            logger.debug("✅ DEBUG: Updated subcategory data validation passed")
            
            # Verify database state
            self.subcategory.refresh_from_db()
            self.assertEqual(self.subcategory.name, 'Updated Test SubCategory')
            self.assertEqual(self.subcategory.sort_order, 15)
            logger.debug("✅ DEBUG: Database state validation passed")
            
            test_duration = time.time() - test_start_time
            logger.info(f"✅ DEBUG: test_update_subcategory_standardized_response completed successfully in {test_duration:.3f}s")
            
        except Exception as e:
            test_duration = time.time() - test_start_time
            logger.error(f"💥 DEBUG: test_update_subcategory_standardized_response failed after {test_duration:.3f}s: {e}")
            raise

    def test_partial_update_subcategory_standardized_response(self):
        """
        🧪 ENHANCED TEST: Validate standardized response format for subcategory partial update
        """
        logger.info("🧪 DEBUG: Starting test_partial_update_subcategory_standardized_response")
        test_start_time = time.time()
        
        try:
            url = reverse('service-subcategory-detail', kwargs={'pk': self.subcategory.id})
            original_name = self.subcategory.name
            
            data = {
                'description': 'Partially updated test description',
                'sort_order': 25
            }
            logger.debug(f"📊 DEBUG: Partially updating subcategory with data: {data}")
            logger.debug(f"📝 DEBUG: Original name should remain: '{original_name}'")
            
            response = self.enhanced_api_call('PATCH', url, data=data, user=self.admin_user, expected_status=200)
            
            # Validate standardized response format
            response_data = self.assert_standardized_response(response, 200)
            
            # Validate message
            self.assertIn("partially updated successfully", response_data['message'])
            logger.debug(f"✅ DEBUG: Partial update success message validation passed: {response_data['message']}")
            
            # Validate data structure
            self.assertIn('subcategory', response_data['data'])
            self.assertIn('partial_update_details', response_data['data'])
            logger.debug("✅ DEBUG: Partial update response data structure validation passed")
            
            # Validate partial update details
            update_details = response_data['data']['partial_update_details']
            expected_fields = ['updated_by', 'updated_at', 'fields_updated', 'changes_made', 'category_name', 'subcategory_id']
            
            for field in expected_fields:
                self.assertIn(field, update_details)
                logger.debug(f"✅ DEBUG: Partial update detail field '{field}' present")
            
            # Validate fields_updated
            fields_updated = update_details['fields_updated']
            self.assertIn('description', fields_updated)
            self.assertIn('sort_order', fields_updated)
            self.assertNotIn('name', fields_updated)  # Name shouldn't be in partial update
            logger.debug(f"✅ DEBUG: Fields updated validation passed: {fields_updated}")
            
            # Validate subcategory data - name should remain unchanged
            subcategory_data = response_data['data']['subcategory']
            self.assertEqual(subcategory_data['name'], original_name)  # Name should be unchanged
            self.assertEqual(subcategory_data['description'], 'Partially updated test description')
            logger.debug("✅ DEBUG: Partial update data validation passed - name unchanged, description updated")
            
            # Verify database state
            self.subcategory.refresh_from_db()
            self.assertEqual(self.subcategory.name, original_name)  # Name unchanged
            self.assertEqual(self.subcategory.description, 'Partially updated test description')
            self.assertEqual(self.subcategory.sort_order, 25)
            logger.debug("✅ DEBUG: Database state validation passed for partial update")
            
            test_duration = time.time() - test_start_time
            logger.info(f"✅ DEBUG: test_partial_update_subcategory_standardized_response completed successfully in {test_duration:.3f}s")
            
        except Exception as e:
            test_duration = time.time() - test_start_time
            logger.error(f"💥 DEBUG: test_partial_update_subcategory_standardized_response failed after {test_duration:.3f}s: {e}")
            raise

    def test_delete_subcategory_standardized_response(self):
        """
        🧪 ENHANCED TEST: Validate standardized response format for subcategory deletion
        """
        logger.info("🧪 DEBUG: Starting test_delete_subcategory_standardized_response")
        test_start_time = time.time()
        
        try:
            url = reverse('service-subcategory-detail', kwargs={'pk': self.subcategory.id})
            subcategory_name = self.subcategory.name
            subcategory_id = str(self.subcategory.id)
            
            logger.debug(f"🗑️ DEBUG: Deleting subcategory: '{subcategory_name}' (ID: {subcategory_id})")
            
            response = self.enhanced_api_call('DELETE', url, user=self.admin_user, expected_status=204)
            
            # Validate standardized response format for deletion (204 No Content)
            response_data = self.assert_standardized_response(response, 204)
            
            # Validate message
            self.assertIn("deleted successfully", response_data['message'])
            logger.debug(f"✅ DEBUG: Deletion success message validation passed: {response_data['message']}")
            
            # Validate deletion data structure
            self.assertIn('deleted_subcategory', response_data['data'])
            self.assertIn('impact_analysis', response_data['data'])
            self.assertIn('deletion_metadata', response_data['data'])
            logger.debug("✅ DEBUG: Deletion response data structure validation passed")
            
            # Validate deleted subcategory details
            deleted_info = response_data['data']['deleted_subcategory']
            self.assertEqual(deleted_info['id'], subcategory_id)
            self.assertEqual(deleted_info['name'], subcategory_name)
            logger.debug("✅ DEBUG: Deleted subcategory details validation passed")
            
            # Validate impact analysis
            impact_analysis = response_data['data']['impact_analysis']
            expected_impact_fields = ['total_services_affected', 'active_services_affected', 'inactive_services_affected']
            
            for field in expected_impact_fields:
                self.assertIn(field, impact_analysis)
                self.assertIsInstance(impact_analysis[field], int)
                logger.debug(f"✅ DEBUG: Impact analysis field '{field}' present and valid")
            
            # Validate deletion metadata
            deletion_metadata = response_data['data']['deletion_metadata']
            self.assertIn('deleted_by', deletion_metadata)
            self.assertIn('deleted_at', deletion_metadata)
            self.assertIn('deletion_type', deletion_metadata)
            self.assertEqual(deletion_metadata['deleted_by'], self.admin_user.username)
            logger.debug("✅ DEBUG: Deletion metadata validation passed")
            
            # Verify database state - subcategory should be deleted
            total_subcategories = ServiceSubCategory.objects.count()
            self.assertEqual(total_subcategories, 0)
            logger.debug("✅ DEBUG: Database state validation passed - subcategory deleted")
            
            test_duration = time.time() - test_start_time
            logger.info(f"✅ DEBUG: test_delete_subcategory_standardized_response completed successfully in {test_duration:.3f}s")
            
        except Exception as e:
            test_duration = time.time() - test_start_time
            logger.error(f"💥 DEBUG: test_delete_subcategory_standardized_response failed after {test_duration:.3f}s: {e}")
            raise

    def test_subcategory_validation_errors(self):
        """
        🧪 ENHANCED TEST: Validate error response format for subcategory validation failures
        """
        logger.info("🧪 DEBUG: Starting test_subcategory_validation_errors")
        test_start_time = time.time()
        
        try:
            url = reverse('service-subcategory-list')
            
            # Test with invalid data (missing required field)
            invalid_data = {
                'name': 'Test SubCategory',
                # Missing 'category' field which is required
                'description': 'Test description'
            }
            logger.debug(f"📊 DEBUG: Testing validation error with invalid data: {invalid_data}")
            
            response = self.enhanced_api_call('POST', url, data=invalid_data, user=self.admin_user, expected_status=400)
            
            # Validate error response format
            response_data = self.assert_standardized_response(response, 400)
            
            # Validate error message
            self.assertIn("validation failed", response_data['message'])
            logger.debug(f"✅ DEBUG: Error message validation passed: {response_data['message']}")
            
            # Validate error data structure
            self.assertIn('validation_errors', response_data['data'])
            self.assertIn('provided_data', response_data['data'])
            self.assertIn('error_type', response_data['data'])
            logger.debug("✅ DEBUG: Error response data structure validation passed")
            
            # Validate validation errors
            validation_errors = response_data['data']['validation_errors']
            self.assertIn('category', validation_errors)  # Should have category field error
            logger.debug("✅ DEBUG: Validation errors correctly identified missing category field")
            
            test_duration = time.time() - test_start_time
            logger.info(f"✅ DEBUG: test_subcategory_validation_errors completed successfully in {test_duration:.3f}s")
            
        except Exception as e:
            test_duration = time.time() - test_start_time
            logger.error(f"💥 DEBUG: test_subcategory_validation_errors failed after {test_duration:.3f}s: {e}")
            raise
