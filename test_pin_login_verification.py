#!/usr/bin/env python
"""
🔐 PIN Login Verification Script for All User Types

This script verifies that the PIN authentication system works properly for:
- Customer users (user_type='customer')
- Provider users (user_type='provider')  
- Admin users (user_type='admin')

Tests the complete authentication flow:
PinLoginView → PinLoginSerializer → authenticate_user_with_pin → User.check_pin
"""

import os
import sys
import django
import json
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prbal_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.utils import authenticate_user_with_pin
from users.serializers import PinLoginSerializer

User = get_user_model()

def test_pin_authentication():
    """
    🧪 Test PIN authentication for all user types
    """
    print("🔐 PIN LOGIN VERIFICATION FOR ALL USER TYPES")
    print("=" * 60)
    
    # Test data for different user types
    test_cases = [
        {
            'username': 'test_customer',
            'email': 'test_customer@example.com',
            'phone_number': '+1111111111',
            'user_type': 'customer',
            'pin': '1234',
            'description': '🛒 Customer User'
        },
        {
            'username': 'test_provider',
            'email': 'test_provider@example.com', 
            'phone_number': '+2222222222',
            'user_type': 'provider',
            'pin': '5678',
            'description': '🔧 Provider User',
            'rating': 4.5
        },
        {
            'username': 'test_admin',
            'email': 'test_admin@example.com',
            'phone_number': '+3333333333', 
            'user_type': 'admin',
            'pin': '9999',
            'description': '👑 Admin User',
            'is_staff': True
        }
    ]
    
    created_users = []
    test_results = []
    
    # Create test users
    print("🔧 Setting up test users...")
    for test_case in test_cases:
        try:
            # Remove existing test user if exists
            User.objects.filter(phone_number=test_case['phone_number']).delete()
            
            # Create user
            user_data = test_case.copy()
            pin = user_data.pop('pin')
            user_data.pop('description')
            
            user = User.objects.create_user(**user_data)
            user.set_pin(pin)
            user.save()
            
            created_users.append((user, pin))
            print(f"✅ Created {test_case['description']}: {user.username}")
            
        except Exception as e:
            print(f"❌ Failed to create {test_case['description']}: {e}")
            continue
    
    print()
    
    # Test 1: Model check_pin method
    print("🔐 Testing User.check_pin() method...")
    for user, pin in created_users:
        try:
            # Test correct PIN
            if user.check_pin(pin):
                print(f"✅ {user.get_user_type_display()} check_pin: PASS (correct PIN)")
                test_results.append(f"{user.user_type}_check_pin_correct: PASS")
            else:
                print(f"❌ {user.get_user_type_display()} check_pin: FAIL (correct PIN rejected)")
                test_results.append(f"{user.user_type}_check_pin_correct: FAIL")
            
            # Test wrong PIN
            if not user.check_pin("0000"):
                print(f"✅ {user.get_user_type_display()} check_pin: PASS (wrong PIN rejected)")
                test_results.append(f"{user.user_type}_check_pin_wrong: PASS")
            else:  
                print(f"❌ {user.get_user_type_display()} check_pin: FAIL (wrong PIN accepted)")
                test_results.append(f"{user.user_type}_check_pin_wrong: FAIL")
                
        except Exception as e:
            print(f"❌ {user.get_user_type_display()} check_pin: ERROR - {e}")
            test_results.append(f"{user.user_type}_check_pin: ERROR")
    
    print()
    
    # Test 2: Utils authenticate_user_with_pin function
    print("🔍 Testing authenticate_user_with_pin() function...")
    for user, pin in created_users:
        try:
            # Test correct credentials
            auth_user = authenticate_user_with_pin(user.phone_number, pin)
            if auth_user and auth_user.id == user.id:
                print(f"✅ {user.get_user_type_display()} utils auth: PASS (correct credentials)")
                test_results.append(f"{user.user_type}_utils_auth_correct: PASS")
            else:
                print(f"❌ {user.get_user_type_display()} utils auth: FAIL (correct credentials)")
                test_results.append(f"{user.user_type}_utils_auth_correct: FAIL")
            
            # Test wrong PIN
            wrong_auth = authenticate_user_with_pin(user.phone_number, "0000")
            if wrong_auth is None:
                print(f"✅ {user.get_user_type_display()} utils auth: PASS (wrong PIN rejected)")  
                test_results.append(f"{user.user_type}_utils_auth_wrong: PASS")
            else:
                print(f"❌ {user.get_user_type_display()} utils auth: FAIL (wrong PIN accepted)")
                test_results.append(f"{user.user_type}_utils_auth_wrong: FAIL")
                
        except Exception as e:
            print(f"❌ {user.get_user_type_display()} utils auth: ERROR - {e}")
            test_results.append(f"{user.user_type}_utils_auth: ERROR")
    
    print()
    
    # Test 3: PinLoginSerializer validation
    print("📝 Testing PinLoginSerializer validation...")
    for user, pin in created_users:
        try:
            # Test valid data
            serializer = PinLoginSerializer(data={
                'phone_number': user.phone_number,
                'pin': pin
            })
            
            if serializer.is_valid():
                validated_user = serializer.validated_data.get('user')
                if validated_user and validated_user.id == user.id:
                    print(f"✅ {user.get_user_type_display()} serializer: PASS (valid data)")
                    test_results.append(f"{user.user_type}_serializer_valid: PASS")
                else:
                    print(f"❌ {user.get_user_type_display()} serializer: FAIL (wrong user returned)")
                    test_results.append(f"{user.user_type}_serializer_valid: FAIL")
            else:
                print(f"❌ {user.get_user_type_display()} serializer: FAIL (validation failed: {serializer.errors})")
                test_results.append(f"{user.user_type}_serializer_valid: FAIL")
            
            # Test invalid PIN
            invalid_serializer = PinLoginSerializer(data={
                'phone_number': user.phone_number,  
                'pin': '0000'
            })
            
            if not invalid_serializer.is_valid():
                print(f"✅ {user.get_user_type_display()} serializer: PASS (invalid PIN rejected)")
                test_results.append(f"{user.user_type}_serializer_invalid: PASS")
            else:
                print(f"❌ {user.get_user_type_display()} serializer: FAIL (invalid PIN accepted)")
                test_results.append(f"{user.user_type}_serializer_invalid: FAIL")
                
        except Exception as e:
            print(f"❌ {user.get_user_type_display()} serializer: ERROR - {e}")
            test_results.append(f"{user.user_type}_serializer: ERROR")
    
    print()
    
    # Cleanup test users
    print("🧹 Cleaning up test users...")
    for user, pin in created_users:
        try:
            user.delete()
            print(f"✅ Deleted test user: {user.username}")
        except Exception as e:
            print(f"❌ Failed to delete {user.username}: {e}")
    
    print()
    
    # Print summary
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = len([r for r in test_results if 'PASS' in r])
    failed_tests = len([r for r in test_results if 'FAIL' in r])
    error_tests = len([r for r in test_results if 'ERROR' in r])
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"🚨 Errors: {error_tests}")
    print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
    
    print("\n🎯 User Type Coverage:")
    user_types = ['customer', 'provider', 'admin']
    for user_type in user_types:
        type_results = [r for r in test_results if r.startswith(user_type)]
        type_passed = len([r for r in type_results if 'PASS' in r])
        print(f"   {user_type.upper()}: {type_passed}/{len(type_results)} tests passed")
    
    if failed_tests > 0 or error_tests > 0:
        print("\n❌ Issues Found:")
        for result in test_results:
            if 'FAIL' in result or 'ERROR' in result:
                print(f"   • {result}")
    
    print("=" * 60)
    print("🏁 PIN Login Verification Complete!")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = test_pin_authentication()
    sys.exit(0 if success else 1) 