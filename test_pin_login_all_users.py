#!/usr/bin/env python
"""
🔐 PIN Login Test Script for All User Types
Test script to verify that PIN authentication works properly for:
- Customer users
- Provider users  
- Admin users

This script tests the complete authentication flow:
PinLoginView → PinLoginSerializer → authenticate_user_with_pin → User.check_pin
"""

import os
import sys
import django
import requests
import json
from datetime import datetime

# Setup Django environment
sys.path.append('/d%3A/durgas/Prbal-App/prbal_server')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prbal_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.utils import authenticate_user_with_pin
from users.serializers import PinLoginSerializer

User = get_user_model()

class PinLoginTester:
    """
    🧪 Comprehensive PIN login tester for all user types
    """
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.login_endpoint = f"{base_url}/auth/login/"
        self.test_results = []
        
    def log_test(self, test_name, status, message, details=None):
        """Log test results with emoji indicators"""
        emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "ℹ️"
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{emoji} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
        print()
    
    def create_test_users(self):
        """
        🔧 Create test users for each user type
        """
        print("🔧 Setting up test users...")
        
        test_users = [
            {
                'username': 'test_customer_001',
                'email': 'customer@test.com',
                'phone_number': '+1234567001',
                'user_type': 'customer',
                'first_name': 'Test',
                'last_name': 'Customer',
                'pin': '1234'
            },
            {
                'username': 'test_provider_001', 
                'email': 'provider@test.com',
                'phone_number': '+1234567002',
                'user_type': 'provider',
                'first_name': 'Test',
                'last_name': 'Provider',
                'pin': '5678',
                'rating': 4.5,
                'skills': ['plumbing', 'electrical']
            },
            {
                'username': 'test_admin_001',
                'email': 'admin@test.com', 
                'phone_number': '+1234567003',
                'user_type': 'admin',
                'first_name': 'Test',
                'last_name': 'Admin',
                'pin': '9999',
                'is_staff': True
            }
        ]
        
        created_users = []
        
        for user_data in test_users:
            try:
                # Delete existing test user if exists
                User.objects.filter(phone_number=user_data['phone_number']).delete()
                
                # Create new user
                pin = user_data.pop('pin')
                user = User.objects.create_user(**user_data)
                user.set_pin(pin)
                user.save()
                
                created_users.append({
                    'user': user,
                    'pin': pin,
                    'phone_number': user_data['phone_number']
                })
                
                self.log_test(
                    f"Create {user.user_type} user",
                    "PASS",
                    f"Created user {user.username} with phone {user.phone_number}",
                    {'user_id': str(user.id), 'user_type': user.user_type}
                )
                
            except Exception as e:
                self.log_test(
                    f"Create {user_data['user_type']} user",
                    "FAIL", 
                    f"Failed to create user: {e}",
                    {'phone_number': user_data['phone_number']}
                )
        
        return created_users
    
    def test_utils_authentication(self, test_users):
        """
        🔍 Test the authenticate_user_with_pin utility function
        """
        print("🔍 Testing utils.authenticate_user_with_pin function...")
        
        for user_data in test_users:
            user = user_data['user']
            pin = user_data['pin']
            phone = user_data['phone_number']
            
            try:
                # Test correct PIN
                auth_user = authenticate_user_with_pin(phone, pin)
                
                if auth_user and auth_user.id == user.id:
                    self.log_test(
                        f"Utils auth - {user.user_type}",
                        "PASS",
                        f"Successfully authenticated {user.user_type} user with PIN",
                        {
                            'user_id': str(user.id),
                            'user_type': user.user_type,
                            'username': user.username
                        }
                    )
                else:
                    self.log_test(
                        f"Utils auth - {user.user_type}",
                        "FAIL",
                        f"Authentication returned None or wrong user",
                        {'expected_user': str(user.id), 'returned': str(auth_user.id) if auth_user else None}
                    )
                
                # Test wrong PIN
                wrong_auth = authenticate_user_with_pin(phone, "0000")
                if wrong_auth is None:
                    self.log_test(
                        f"Utils auth wrong PIN - {user.user_type}",
                        "PASS",
                        f"Correctly rejected wrong PIN for {user.user_type}",
                        {'user_type': user.user_type}
                    )
                else:
                    self.log_test(
                        f"Utils auth wrong PIN - {user.user_type}",
                        "FAIL",
                        f"Should have rejected wrong PIN",
                        {'user_type': user.user_type}
                    )
                    
            except Exception as e:
                self.log_test(
                    f"Utils auth - {user.user_type}",
                    "FAIL",
                    f"Exception during authentication: {e}",
                    {'user_type': user.user_type, 'error': str(e)}
                )
    
    def test_serializer_validation(self, test_users):
        """
        📝 Test PinLoginSerializer validation
        """
        print("📝 Testing PinLoginSerializer validation...")
        
        for user_data in test_users:
            user = user_data['user']
            pin = user_data['pin']
            phone = user_data['phone_number']
            
            try:
                # Test valid data
                serializer = PinLoginSerializer(data={
                    'phone_number': phone,
                    'pin': pin
                })
                
                if serializer.is_valid():
                    validated_user = serializer.validated_data.get('user')
                    
                    if validated_user and validated_user.id == user.id:
                        self.log_test(
                            f"Serializer validation - {user.user_type}",
                            "PASS",
                            f"Successfully validated {user.user_type} user",
                            {
                                'user_id': str(user.id),
                                'user_type': user.user_type,
                                'username': user.username
                            }
                        )
                    else:
                        self.log_test(
                            f"Serializer validation - {user.user_type}",
                            "FAIL",
                            f"Validation returned wrong user",
                            {'expected': str(user.id), 'got': str(validated_user.id) if validated_user else None}
                        )
                else:
                    self.log_test(
                        f"Serializer validation - {user.user_type}",
                        "FAIL",
                        f"Serializer validation failed: {serializer.errors}",
                        {'errors': serializer.errors}
                    )
                
                # Test invalid PIN
                invalid_serializer = PinLoginSerializer(data={
                    'phone_number': phone,
                    'pin': '0000'
                })
                
                if not invalid_serializer.is_valid():
                    self.log_test(
                        f"Serializer invalid PIN - {user.user_type}",
                        "PASS",
                        f"Correctly rejected invalid PIN for {user.user_type}",
                        {'errors': invalid_serializer.errors}
                    )
                else:
                    self.log_test(
                        f"Serializer invalid PIN - {user.user_type}",
                        "FAIL",
                        f"Should have rejected invalid PIN",
                        {'user_type': user.user_type}
                    )
                    
            except Exception as e:
                self.log_test(
                    f"Serializer validation - {user.user_type}",
                    "FAIL",
                    f"Exception during validation: {e}",
                    {'user_type': user.user_type, 'error': str(e)}
                )
    
    def test_api_endpoint(self, test_users):
        """
        🌐 Test the actual API endpoint /auth/login/
        """
        print("🌐 Testing /auth/login/ API endpoint...")
        
        for user_data in test_users:
            user = user_data['user']
            pin = user_data['pin']
            phone = user_data['phone_number']
            
            try:
                # Test successful login
                response = requests.post(self.login_endpoint, json={
                    'phone_number': phone,
                    'pin': pin,
                    'device_type': 'test'
                })
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if (data.get('success') and 
                        data.get('data', {}).get('user', {}).get('id') == str(user.id)):
                        
                        self.log_test(
                            f"API login - {user.user_type}",
                            "PASS",
                            f"Successfully logged in {user.user_type} via API",
                            {
                                'user_id': str(user.id),
                                'user_type': user.user_type,
                                'username': user.username,
                                'has_tokens': 'tokens' in data.get('data', {}),
                                'response_status': response.status_code
                            }
                        )
                    else:
                        self.log_test(
                            f"API login - {user.user_type}",
                            "FAIL",
                            f"API response invalid or wrong user",
                            {
                                'expected_user': str(user.id),
                                'response_data': data,
                                'status_code': response.status_code
                            }
                        )
                else:
                    self.log_test(
                        f"API login - {user.user_type}",
                        "FAIL",
                        f"API returned error status: {response.status_code}",
                        {
                            'status_code': response.status_code,
                            'response': response.text
                        }
                    )
                
                # Test failed login
                fail_response = requests.post(self.login_endpoint, json={
                    'phone_number': phone,
                    'pin': '0000'
                })
                
                if fail_response.status_code == 400:
                    self.log_test(
                        f"API login wrong PIN - {user.user_type}",
                        "PASS",
                        f"Correctly rejected wrong PIN for {user.user_type}",
                        {'status_code': fail_response.status_code}
                    )
                else:
                    self.log_test(
                        f"API login wrong PIN - {user.user_type}",
                        "FAIL",
                        f"Should have returned 400 for wrong PIN",
                        {
                            'status_code': fail_response.status_code,
                            'response': fail_response.text
                        }
                    )
                    
            except Exception as e:
                self.log_test(
                    f"API login - {user.user_type}",
                    "FAIL",
                    f"Exception during API test: {e}",
                    {'user_type': user.user_type, 'error': str(e)}
                )
    
    def test_model_check_pin(self, test_users):
        """
        🔐 Test User.check_pin method directly
        """
        print("🔐 Testing User.check_pin method...")
        
        for user_data in test_users:
            user = user_data['user']
            pin = user_data['pin']
            
            try:
                # Test correct PIN
                if user.check_pin(pin):
                    self.log_test(
                        f"Model check_pin - {user.user_type}",
                        "PASS",
                        f"check_pin correctly validated PIN for {user.user_type}",
                        {
                            'user_id': str(user.id),
                            'user_type': user.user_type,
                            'username': user.username
                        }
                    )
                else:
                    self.log_test(
                        f"Model check_pin - {user.user_type}",
                        "FAIL",
                        f"check_pin rejected correct PIN",
                        {'user_type': user.user_type}
                    )
                
                # Test wrong PIN
                if not user.check_pin("0000"):
                    self.log_test(
                        f"Model check_pin wrong PIN - {user.user_type}",
                        "PASS", 
                        f"check_pin correctly rejected wrong PIN for {user.user_type}",
                        {'user_type': user.user_type}
                    )
                else:
                    self.log_test(
                        f"Model check_pin wrong PIN - {user.user_type}",
                        "FAIL",
                        f"check_pin should have rejected wrong PIN",
                        {'user_type': user.user_type}
                    )
                    
            except Exception as e:
                self.log_test(
                    f"Model check_pin - {user.user_type}",
                    "FAIL",
                    f"Exception during check_pin: {e}",
                    {'user_type': user.user_type, 'error': str(e)}
                )
    
    def cleanup_test_users(self, test_users):
        """
        🧹 Clean up test users
        """
        print("🧹 Cleaning up test users...")
        
        for user_data in test_users:
            try:
                user = user_data['user']
                user.delete()
                self.log_test(
                    f"Cleanup - {user.user_type}",
                    "PASS",
                    f"Cleaned up test user {user.username}",
                    {'user_id': str(user.id)}
                )
            except Exception as e:
                self.log_test(
                    f"Cleanup - {user_data.get('user', {}).get('user_type', 'unknown')}",
                    "FAIL",
                    f"Failed to cleanup user: {e}",
                    {'error': str(e)}
                )
    
    def run_all_tests(self):
        """
        🚀 Run all PIN login tests
        """
        print("🚀 Starting comprehensive PIN login tests for all user types")
        print("=" * 80)
        
        # Create test users
        test_users = self.create_test_users()
        
        if not test_users:
            print("❌ No test users created, aborting tests")
            return
        
        try:
            # Run all test suites
            self.test_model_check_pin(test_users)
            self.test_utils_authentication(test_users)
            self.test_serializer_validation(test_users)
            self.test_api_endpoint(test_users)
            
        finally:
            # Always cleanup
            self.cleanup_test_users(test_users)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """
        📊 Print test results summary
        """
        print("=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        
        print(f"🔢 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"   • {result['test']}: {result['message']}")
        
        print("\n🎯 USER TYPE COVERAGE:")
        user_types = ['customer', 'provider', 'admin']
        for user_type in user_types:
            type_tests = [r for r in self.test_results if user_type in r['test'].lower()]
            type_passed = len([r for r in type_tests if r['status'] == 'PASS'])
            type_total = len(type_tests)
            
            if type_total > 0:
                emoji = "✅" if type_passed == type_total else "⚠️" if type_passed > 0 else "❌"
                print(f"   {emoji} {user_type.upper()}: {type_passed}/{type_total} tests passed")
        
        print("=" * 80)


if __name__ == "__main__":
    tester = PinLoginTester()
    tester.run_all_tests() 