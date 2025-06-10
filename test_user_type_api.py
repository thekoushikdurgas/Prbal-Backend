#!/usr/bin/env python
"""
Simple test script to verify the user type detection API endpoint.
Run this script to test the API functionality.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prbal_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.tokens import CustomRefreshToken
from django.test import Client
from django.urls import reverse

User = get_user_model()

def test_user_type_api():
    """Test the user type detection API"""
    print("🚀 Testing User Type Detection API")
    print("=" * 50)
    
    # Create test users if they don't exist
    try:
        # Create a customer user
        customer_user, created = User.objects.get_or_create(
            username='test_customer_api',
            defaults={
                'email': 'test_customer_api@example.com',
                'user_type': 'customer'
            }
        )
        if created:
            customer_user.set_pin('1234')
            customer_user.save()
        print(f"✅ Customer user: {customer_user.username} (ID: {customer_user.id})")
        
        # Create a provider user
        provider_user, created = User.objects.get_or_create(
            username='test_provider_api',
            defaults={
                'email': 'test_provider_api@example.com',
                'user_type': 'provider'
            }
        )
        if created:
            provider_user.set_pin('5678')
            provider_user.save()
        print(f"✅ Provider user: {provider_user.username} (ID: {provider_user.id})")
        
        # Create an admin user
        admin_user, created = User.objects.get_or_create(
            username='test_admin_api',
            defaults={
                'email': 'test_admin_api@example.com',
                'user_type': 'admin',
                'is_staff': True
            }
        )
        if created:
            admin_user.set_pin('9999')
            admin_user.save()
        print(f"✅ Admin user: {admin_user.username} (ID: {admin_user.id})")
        
    except Exception as e:
        print(f"❌ Error creating test users: {e}")
        return
    
    print("\n" + "=" * 50)
    print("🔍 Testing API Responses")
    print("=" * 50)
    
    # Test each user type
    users_to_test = [
        (customer_user, "Customer"),
        (provider_user, "Service Provider"),
        (admin_user, "Administrator")
    ]
    
    client = Client()
    
    for user, expected_display in users_to_test:
        try:
            # Generate token for user
            refresh = CustomRefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            
            # Make API request
            url = reverse('user-type')
            response = client.get(
                url,
                HTTP_AUTHORIZATION=f'Bearer {access_token}'
            )
            
            print(f"\n👤 Testing {user.username}:")
            print(f"   📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                user_data = data.get('data', {})
                
                print(f"   🆔 User ID: {user_data.get('user_id')}")
                print(f"   👤 Username: {user_data.get('username')}")
                print(f"   🏷️  User Type: {user_data.get('user_type')}")
                print(f"   📋 Display: {user_data.get('user_type_display')}")
                print(f"   🛍️  Is Customer: {user_data.get('is_customer')}")
                print(f"   🔧 Is Provider: {user_data.get('is_provider')}")
                print(f"   👑 Is Admin: {user_data.get('is_admin')}")
                print(f"   💬 Message: {data.get('message')}")
                
                # Verify correctness
                if (user_data.get('user_type') == user.user_type and 
                    user_data.get('user_type_display') == expected_display):
                    print(f"   ✅ CORRECT: User type detected properly!")
                else:
                    print(f"   ❌ ERROR: User type mismatch!")
                    
            else:
                print(f"   ❌ ERROR: Unexpected status code")
                print(f"   📄 Response: {response.content}")
                
        except Exception as e:
            print(f"   ❌ ERROR testing {user.username}: {e}")
    
    print("\n" + "=" * 50)
    print("🔒 Testing Unauthenticated Access")
    print("=" * 50)
    
    # Test without authentication
    try:
        url = reverse('user-type')
        response = client.get(url)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ CORRECT: Unauthenticated access properly blocked!")
        else:
            print("❌ ERROR: Unauthenticated access should return 401")
            
    except Exception as e:
        print(f"❌ ERROR testing unauthenticated access: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 API Endpoint Information")
    print("=" * 50)
    print(f"URL Pattern: /auth/user-type/")
    print(f"Method: GET")
    print(f"Authentication: Bearer Token Required")
    print(f"Response Format: JSON")
    
    print("\n" + "=" * 50)
    print("📝 Usage Example")
    print("=" * 50)
    print("""
# Example API Request:
GET /auth/user-type/
Authorization: Bearer your_access_token_here

# Example Response:
{
    "data": {
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "username": "john_doe",
        "user_type": "customer",
        "user_type_display": "Customer",
        "is_customer": true,
        "is_provider": false,
        "is_admin": false
    },
    "message": "User is a Customer",
    "status": "success"
}
    """)
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    test_user_type_api() 