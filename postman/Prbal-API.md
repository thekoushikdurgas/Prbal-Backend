# Prbal API Documentation

This document outlines the various API endpoints available in the Prbal backend system, derived from the project's codebase and supporting documentation.

## Table of Contents
- [Authentication](#authentication)
  - [JWT Token Management](#jwt-token-management)
    - [User Login (Obtain JWT Tokens)](#user-login-obtain-jwt-tokens)
    - [Refresh JWT Access Token](#refresh-jwt-access-token)
    - [User Logout](#user-logout)
  - [User Registration](#user-registration)
    - [Generic User Registration](#generic-user-registration)
    - [Customer Specific Registration](#customer-specific-registration)
    - [Provider Specific Registration](#provider-specific-registration)
    - [Admin Specific Registration](#admin-specific-registration)
- [User Management](#user-management)
  - [Generic User Endpoints](#generic-user-endpoints)
  - [Customer Specific Endpoints](#customer-specific-endpoints)
  - [Provider Specific Endpoints](#provider-specific-endpoints)
  - [Admin Specific Endpoints (Profile)](#admin-specific-endpoints-profile)
  - [User Search](#user-search)
- [Services & Service Requests](#services--service-requests)
  - [Public Service & Category Endpoints](#public-service--category-endpoints)
  - [Service Requests (All Roles)](#service-requests-all-roles)
- [Products](#products)
  - [Product Categories](#product-categories)
  - [Products](#products-individual)
- [Bids](#bids)
- [Bookings](#bookings)
- [Calendar Integration](#calendar-integration)
- [Payments](#payments)
  - [Payment Processing](#payment-processing)
  - [Payment Gateway Accounts](#payment-gateway-accounts)
  - [Payouts](#payouts)
- [Messaging](#messaging)
  - [Message Threads](#message-threads)
  - [Individual Messages](#individual-messages)
  - [Messages within a Thread](#messages-within-a-thread)
- [Notifications (HTTP)](#notifications-http)
- [AI Suggestions & Feedback](#ai-suggestions--feedback)
  - [AI Suggestions](#ai-suggestions)
  - [AI Feedback Logs](#ai-feedback-logs)
- [Verifications (User Identity, etc.)](#verifications-user-identity-etc)
- [Reviews](#reviews)
- [Sync (Offline Functionality)](#sync-offline-functionality)
- [Analytics & Admin Management](#analytics--admin-management)
  - [Analytics Reports](#analytics-reports)
  - [Admin User Management](#admin-user-management)
  - [Admin Service Management](#admin-service-management)
- [WebSocket APIs](#websocket-apis)
- [Health Checks](#health-checks)
- [Metrics](#metrics)

---

## Authentication

This section details user registration, login, and token management processes.

### User Registration

#### Generic User Registration (Defaults to Customer Type)

- **Endpoint:** `POST {{base_url}}/api/v1/auth/register/`
- **Description:** Allows new users to register. By default, this endpoint registers a user with the 'customer' type. For specific roles like 'provider' or 'admin', use their dedicated registration endpoints.
- **Permissions:** Anonymous User
- **Request Body:** `application/json`
  *Required fields: `username`, `email`, `password`, `password_confirm`*
  *Optional fields: `phone_number`, `first_name`, `last_name`*
  ```json
  {
      "username": "newgenericuser",
      "email": "generic@example.com",
      "password": "newpassword123",
      "password_confirm": "newpassword123",
      "phone_number": "1234567890",
      "first_name": "Generic",
      "last_name": "User"
  }
  ```

- **Example cURL Request:** ✅
  ```bash
  curl -X POST {{base_url}}/api/v1/auth/register/ \
    -H "Content-Type: application/json" \
    -d '{
          "username": "newgenericuser",
          "email": "generic@example.com",
          "password": "newpassword123",
          "password_confirm": "newpassword123",
          "phone_number": "1234567890",
          "first_name": "Generic",
          "last_name": "User"
        }'
  ```

- **Example Success Response (201 Created):**
  ```json
  {
      "user": {
          "id": "usr_01H...",
          "username": "newgenericuser",
          "email": "generic@example.com",
          "phone_number": "1234567890",
          "first_name": "Generic",
          "last_name": "User",
          "user_type": "customer",
          "profile_picture": null,
          "bio": null,
          "location": null,
          "is_verified": false,
          "rating": 0.0,
          "balance": "0.00",
          "created_at": "2023-10-27T10:00:00Z",
          "updated_at": "2023-10-27T10:00:00Z"
      },
      "tokens": {
          "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      },
      "message": "customer registered successfully"
  }
  ```

- **Example Error Response (400 Bad Request - Validation Error):**
  ```json
  {
      "email": [
          "A user with that email address already exists."
      ],
      "password": [
          "Password fields didn't match."
      ],
      "username": [
          "A user with that username already exists."
      ]
  }
  ```

- **Example Error Response (400 Bad Request - Missing Fields):**
  ```json
  {
      "username": [
          "This field is required."
      ],
      "email": [
          "This field is required."
      ],
      "password": [
          "This field is required."
      ],
      "password_confirm": [
          "This field is required."
      ]
  }
  ```

#### Customer Registration

- **Endpoint:** `POST {{base_url}}/api/v1/auth/customer/register/`
- **Description:** Allows new users to register specifically as a 'customer'.
- **Permissions:** Anonymous User
- **Request Body:** `application/json`
  *Required fields: `username`, `email`, `password`, `password_confirm`*
  *Optional fields: `phone_number`, `first_name`, `last_name`*
  ```json
  {
      "username": "newcustomer",
      "email": "customer@example.com",
      "password": "securepassword123",
      "password_confirm": "securepassword123",
      "phone_number": "0987654321",
      "first_name": "Customer",
      "last_name": "Person"
  }
  ```

- **Example cURL Request:** ✅
  ```bash
  curl -X POST {{base_url}}/api/v1/auth/customer/register/ \
    -H "Content-Type: application/json" \
    -d '{
          "username": "newcustomer",
          "email": "customer@example.com",
          "password": "securepassword123",
          "password_confirm": "securepassword123",
          "phone_number": "0987654321",
          "first_name": "Customer",
          "last_name": "Person"
        }'
  ```

- **Example Success Response (201 Created):**
  ```json
  {
      "user": {
          "id": "usr_01H...",
          "username": "newcustomer",
          "email": "customer@example.com",
          "phone_number": "0987654321",
          "first_name": "Customer",
          "last_name": "Person",
          "user_type": "customer",
          "profile_picture": null,
          "bio": null,
          "location": null,
          "is_verified": false,
          "rating": 0.0,
          "balance": "0.00",
          "created_at": "2023-10-27T10:05:00Z",
          "updated_at": "2023-10-27T10:05:00Z"
      },
      "tokens": {
          "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      },
      "message": "customer registered successfully"
  }
  ```
- **Example Error Responses:** (Similar to Generic User Registration)

#### Provider Registration

- **Endpoint:** `POST {{base_url}}/api/v1/auth/provider/register/`
- **Description:** Allows new users to register specifically as a 'provider'.
- **Permissions:** Anonymous User
- **Request Body:** `application/json`
  *Required fields: `username`, `email`, `password`, `password_confirm`*
  *Optional fields: `phone_number`, `first_name`, `last_name`, `skills` (JSON object)*
  ```json
  {
      "username": "newprovider",
      "email": "provider@example.com",
      "password": "strongpass456",
      "password_confirm": "strongpass456",
      "phone_number": "1122334455",
      "first_name": "Provider",
      "last_name": "Pro",
      "skills": {"plumbing": "expert", "electrical": "intermediate"}
  }
  ```

- **Example cURL Request:** ✅
  ```bash
  curl -X POST {{base_url}}/api/v1/auth/provider/register/ \
    -H "Content-Type: application/json" \
    -d '{
          "username": "newprovider",
          "email": "provider@example.com",
          "password": "strongpass456",
          "password_confirm": "strongpass456",
          "phone_number": "1122334455",
          "first_name": "Provider",
          "last_name": "Pro",
          "skills": {"plumbing": "expert", "electrical": "intermediate"}
        }'
  ```

- **Example Success Response (201 Created):**
  ```json
  {
      "user": {
          "id": "usr_01H...",
          "username": "newprovider",
          "email": "provider@example.com",
          "phone_number": "1122334455",
          "first_name": "Provider",
          "last_name": "Pro",
          "user_type": "provider",
          "profile_picture": null,
          "bio": null,
          "location": null,
          "is_verified": false,
          "rating": 0.0,
          "balance": "0.00",
          "created_at": "2023-10-27T10:10:00Z",
          "updated_at": "2023-10-27T10:10:00Z"
          // Note: 'skills' field is part of the User model but might not be in UserProfileSerializer by default.
          // If skills are returned here, the UserProfileSerializer needs to include them.
          // Assuming skills are managed separately or part of a detailed profile view.
      },
      "tokens": {
          "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      },
      "message": "provider registered successfully"
  }
  ```
- **Example Error Responses:** (Similar to Generic User Registration)

#### Admin Registration

- **Endpoint:** `POST {{base_url}}/api/v1/auth/admin/register/`
- **Description:** Allows new users to register specifically as an 'admin'. Requires a valid admin verification code.
- **Permissions:** Anonymous User (but protected by `admin_code`)
- **Request Body:** `application/json`
  *Required fields: `username`, `email`, `password`, `password_confirm`, `admin_code`*
  *Optional fields: `phone_number`, `first_name`, `last_name`*
  ```json
  {
      "username": "newadmin",
      "email": "admin@example.com",
      "password": "adminpass789",
      "password_confirm": "adminpass789",
      "phone_number": "5544332211",
      "first_name": "Admin",
      "last_name": "User",
      "admin_code": "123" 
  }
  ```
  *Note: The `admin_code` "123" is a placeholder from the codebase and should be securely managed.*

- **Example cURL Request:** ✅
  ```bash
  curl -X POST {{base_url}}/api/v1/auth/admin/register/ \
    -H "Content-Type: application/json" \
    -d '{
          "username": "newadmin",
          "email": "admin@example.com",
          "password": "adminpass789",
          "password_confirm": "adminpass789",
          "phone_number": "5544332211",
          "first_name": "Admin",
          "last_name": "User",
          "admin_code": "123"
        }'
  ```

- **Example Success Response (201 Created):**
  ```json
  {
      "user": {
          "id": "usr_01H...",
          "username": "newadmin",
          "email": "admin@example.com",
          "phone_number": "5544332211",
          "first_name": "Admin",
          "last_name": "User",
          "user_type": "admin",
          "profile_picture": null,
          "bio": null,
          "location": null,
          "is_verified": false, // Admins might have different verification logic
          "rating": 0.0,
          "balance": "0.00",
          "created_at": "2023-10-27T10:15:00Z",
          "updated_at": "2023-10-27T10:15:00Z"
      },
      "tokens": {
          "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      },
      "message": "admin registered successfully"
  }
  ```
- **Example Error Response (400 Bad Request - Invalid Admin Code):**
  ```json
  {
      "admin_code": [
          "Invalid administrator verification code"
      ]
  }
  ```
- **Example Error Responses:** (Other errors similar to Generic User Registration)

### User Login

#### Generic User Login

- **Endpoint:** `POST {{base_url}}/api/v1/auth/login/`
- **Description:** Authenticates any registered user (Customer, Provider, Admin, or Generic) with their username, email, or phone number and password, then returns a new access and refresh JSON Web Token (JWT) pair.
- **Permissions:** Anonymous User
- **Request Body:** `application/json`
  *Required fields: `password`, and one of `username`, `email`, or `phone_number`.*
  ```json
  {
      "email": "generic@example.com", 
      "password": "newpassword123"
  }
  ```
  *Alternatively:*
  ```json
  {
      "username": "newgenericuser",
      "password": "newpassword123"
  }
  ```
  *Or:*
  ```json
  {
      "phone_number": "1234567890",
      "password": "newpassword123"
  }
  ```

- **Example cURL Request (using email):** ✅
  ```bash
  curl -X POST {{base_url}}/api/v1/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{
          "email": "generic@example.com",
          "password": "newpassword123"
        }'
  ```

- **Example Success Response (200 OK):**
  ```json
  {
      "user": {
          "id": "usr_01H...",
          "username": "newgenericuser",
          "email": "generic@example.com",
          "phone_number": "1234567890",
          "first_name": "Generic",
          "last_name": "User",
          "user_type": "customer", // Example, will be the actual type of the logged-in user
          "profile_picture": null,
          "bio": null,
          "location": null,
          "is_verified": false,
          "rating": 0.0,
          "balance": "0.00",
          "created_at": "2023-10-27T10:00:00Z",
          "updated_at": "2023-10-27T10:00:00Z"
      },
      "tokens": {
          "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      },
      "message": "customer login successful" // Message reflects actual user type
  }
  ```

- **Example Error Response (400 Bad Request - Invalid Credentials):**
  ```json
  {
      "detail": "Unable to log in with provided credentials."
  }
  ```
  *(Note: The `UserLoginSerializer` can return more specific errors like "Must include either 'username', 'email' or 'phone_number'" if none are provided, or serializer field errors if types are wrong, before hitting the "Unable to log in..." error from `authenticate`.)*

- **Example Error Response (400 Bad Request - Missing Fields):**
  ```json
  {
      "password": [
          "This field is required."
      ],
      "detail": [ // If no identifier (username/email/phone) is provided
          "Must include either 'username', 'email' or 'phone_number'"
      ]
  }
  ```

#### Customer Login

- **Endpoint:** `POST {{base_url}}/api/v1/auth/customer/login/`
- **Description:** Authenticates a user specifically as a 'customer'.
- **Permissions:** Anonymous User
- **Request Body:** `application/json` (Same as Generic User Login)
  ```json
  {
      "email": "customer@example.com",
      "password": "securepassword123"
  }
  ```
- **Example cURL Request:** ✅
  ```bash
  curl -X POST {{base_url}}/api/v1/auth/customer/login/ \
    -H "Content-Type: application/json" \
    -d '{
          "email": "customer@example.com",
          "password": "securepassword123"
        }'
  ```
- **Example Success Response (200 OK):** (Similar to Generic Login, but `user_type` will be 'customer' and message will reflect it)
  ```json
  {
      "user": { /* ... user data for customer ... */ "user_type": "customer", ... },
      "tokens": { /* ... tokens ... */ },
      "message": "customer login successful"
  }
  ```
- **Example Error Response (400 Bad Request - Not a Customer):**
  ```json
  {
      "detail": "User is not registered as a customer" 
  }
  ```
- **Example Error Responses:** (Other errors similar to Generic Login)

#### Provider Login

- **Endpoint:** `POST {{base_url}}/api/v1/auth/provider/login/`
- **Description:** Authenticates a user specifically as a 'provider'.
- **Permissions:** Anonymous User
- **Request Body:** `application/json` (Same as Generic User Login)
  ```json
  {
      "email": "provider@example.com",
      "password": "strongpass456"
  }
  ```
- **Example cURL Request:** ✅
  ```bash
  curl -X POST {{base_url}}/api/v1/auth/provider/login/ \
    -H "Content-Type: application/json" \
    -d '{
          "email": "provider@example.com",
          "password": "strongpass456"
        }'
  ```
- **Example Success Response (200 OK):** (Similar to Generic Login, but `user_type` will be 'provider')
  ```json
  {
      "user": { /* ... user data for provider ... */ "user_type": "provider", ... },
      "tokens": { /* ... tokens ... */ },
      "message": "provider login successful"
  }
  ```
- **Example Error Response (400 Bad Request - Not a Provider):**
  ```json
  {
      "detail": "User is not registered as a provider"
  }
  ```
- **Example Error Responses:** (Other errors similar to Generic Login)

#### Admin Login

- **Endpoint:** `POST {{base_url}}/api/v1/auth/admin/login/`
- **Description:** Authenticates a user specifically as an 'admin'.
- **Permissions:** Anonymous User
- **Request Body:** `application/json` (Same as Generic User Login)
  ```json
  {
      "email": "admin@example.com",
      "password": "adminpass789"
  }
  ```
- **Example cURL Request:** ✅
  ```bash
  curl -X POST {{base_url}}/api/v1/auth/admin/login/ \
    -H "Content-Type: application/json" \
    -d '{
          "email": "admin@example.com",
          "password": "adminpass789"
        }'
  ```
- **Example Success Response (200 OK):** (Similar to Generic Login, but `user_type` will be 'admin')
  ```json
  {
      "user": { /* ... user data for admin ... */ "user_type": "admin", ... },
      "tokens": { /* ... tokens ... */ },
      "message": "admin login successful"
  }
  ```
- **Example Error Response (400 Bad Request - Not an Admin):**
  ```json
  {
      "detail": "User is not registered as a admin" 
  }
  ```
- **Example Error Responses:** (Other errors similar to Generic Login)

### Token Management

#### Refresh JWT Access Token

- **Endpoint:** `POST {{base_url}}/api/v1/auth/token/refresh/`
- **Description:** Takes a refresh JSON Web Token (JWT) and returns a new access JWT if the refresh token is valid.
- **Permissions:** Authenticated User (via a valid refresh token)
- **Request Body:** `application/json`
  ```json
  {
      "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTcyNDQ4OTYwMCwiaWF0IjoxNzIzNjI1NjAwLCJqdGkiOiJhYmNkZWZnMTIzNDU2Nzg5IiwidXNlcl9pZCI6MX0.abcdefghijklmnopqrstuvwxyz123456"
  }
  ```

- **Example cURL Request:** ✅
  ```bash
  curl -X POST {{base_url}}/api/v1/auth/token/refresh/ \
    -H "Content-Type: application/json" \
    -d '{
          "refresh": "your_valid_refresh_token"
        }'
  ```

- **Example Success Response (200 OK):**
  ```json
  {
      "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzIzNjI2MjAwLCJpYXQiOjE3MjM2MjU5MDAsImp0aSI6ImRlZmdoaWxrMTIzNDU2NzgiLCJ1c2VyX2lkIjoxfQ.pqrstuvwxyzabcdefghijklmno123456"
      // May include other custom claims from CustomRefreshToken if it modifies the access token structure directly
  }
  ```

- **Example Error Response (401 Unauthorized - Token Invalid/Expired):**
  ```json
  {
      "detail": "Token is invalid or expired",
      "code": "token_not_valid"
  }
  ```

- **Example Error Response (400 Bad Request - Missing Refresh Token):**
  ```json
  {
      "refresh": [
          "This field is required."
      ]
  }
  ```

#### User Logout (Invalidate Token)

- **Endpoint:** `POST {{base_url}}/api/v1/auth/logout/`
- **Description:** Logs out the currently authenticated user by invalidating their refresh token. The client should also discard both the access and refresh tokens locally.
- **Permissions:** Authenticated User
- **Request Body:** `application/json`
  *Required fields: `refresh`*
  ```json
  {
      "refresh": "your_valid_refresh_token"
  }
  ```

- **Example cURL Request:** ✅
  ```bash
  curl -X POST {{base_url}}/api/v1/auth/logout/ \
    -H "Authorization: Bearer <your_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "refresh": "your_valid_refresh_token"
        }'
  ```
  *Note: The Authorization header with an access token is required to access this protected endpoint.*

- **Example Success Response (200 OK):** 
  *(The code returns 200 OK with a message, not 204 No Content as previously in MD)*
  ```json
  {
      "detail": "Successfully logged out."
  }
  ```

- **Example Error Response (400 Bad Request - Missing Refresh Token):**
  ```json
  {
      "refresh": [
          "This field is required."
      ]
  }
  ```

- **Example Error Response (400 Bad Request - Invalid Token):**
  *(If the refresh token itself is malformed or blacklisted already)*
  ```json
  {
      "detail": "Token is invalid or expired",
      "code": "token_not_valid" 
  }
  ```
  *(Or a more specific error from the `CustomRefreshToken.blacklist()` method if it raises one)*

- **Example Error Response (401 Unauthorized - Invalid Access Token):**
  ```json
  {
      "detail": "Authentication credentials were not provided." 
      // Or "Given token not valid for any token type" if access token is bad
  }
  ```



### User Registration

#### Generic User Registration ✅

- **Endpoint:** `POST {{base_url}}/api/v1/auth/register/`
- **Description:** Registers a new generic user. By default, if no specific user type registration endpoint is used, this will register the user with the 'customer' type. Returns user data and JWT tokens upon successful registration.
- **Permissions:** Anonymous User
- **Request Body:** `application/json`
  *Required fields: `username`, `email`, `password`, `password_confirm`*
  *Optional fields: `first_name`, `last_name`, `phone_number`*
  ```json
  {
      "username": "newgenericuser",
      "email": "newgenericuser@example.com",
      "password": "newstrongpassword123",
      "password_confirm": "newstrongpassword123",
      "first_name": "New",
      "last_name": "Generic",
      "phone_number": "+15551234567"
  }
  ```

- **Example cURL Request:** ✅
  ```bash
  curl -X POST {{base_url}}/api/v1/auth/register/ \
    -H "Content-Type: application/json" \
    -d '{
          "username": "newgenericuser",
          "email": "newgenericuser@example.com",
          "password": "newstrongpassword123",
          "password_confirm": "newstrongpassword123",
          "first_name": "New",
          "last_name": "Generic",
          "phone_number": "+15551234567"
        }'
  ```

- **Example Success Response (201 Created):**
  ```json
  {
      "user": {
          "id": "usr_01HXYZ...",
          "username": "newgenericuser",
          "email": "newgenericuser@example.com",
          "phone_number": "+15551234567",
          "first_name": "New",
          "last_name": "Generic",
          "user_type": "customer",
          "profile_picture": null,
          "bio": null,
          "location": null,
          "is_verified": false,
          "rating": 0.0,
          "balance": "0.00",
          "created_at": "2023-10-27T10:00:00Z",
          "updated_at": "2023-10-27T10:00:00Z"
      },
      "tokens": {
          "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      },
      "message": "Customer registered successfully"
  }
  ```

- **Example Error Response (400 Bad Request - Duplicate Username):**
  ```json
  {
      "username": [
          "A user with that username already exists."
      ]
  }
  ```

- **Example Error Response (400 Bad Request - Duplicate Email):**
  ```json
  {
      "email": [
          "A user with that email address already exists."
      ]
  }
  ```

- **Example Error Response (400 Bad Request - Password Mismatch):**
  ```json
  {
      "password": [
          "Password fields didn't match."
      ]
  }
  ```

- **Example Error Response (400 Bad Request - Invalid Password):**
  ```json
  {
      "password": [
          "This password is too common.",
          "Password must contain at least 8 characters."
      ]
  }
  ```

#### Customer Specific Registration ✅

- **Endpoint:** `POST {{base_url}}/api/v1/auth/customer/register/`
- **Description:** Registers a new user specifically as a 'customer'.
- **Permissions:** Anonymous User
- **Request Body:** `application/json`
  *Required fields: `username`, `email`, `password`, `password_confirm`*
  *Optional fields: `first_name`, `last_name`, `phone_number`*
  ```json
  {
      "username": "newcustomer01",
      "email": "newcustomer01@example.com",
      "password": "customerpass123",
      "password_confirm": "customerpass123",
      "first_name": "Cust",
      "last_name": "Omer",
      "phone_number": "+15551230011"
  }
  ```

- **Example cURL Request:** ✅
  ```bash
  curl -X POST {{base_url}}/api/v1/auth/customer/register/ \
    -H "Content-Type: application/json" \
    -d '{
          "username": "newcustomer01",
          "email": "newcustomer01@example.com",
          "password": "customerpass123",
          "password_confirm": "customerpass123",
          "first_name": "Cust",
          "last_name": "Omer",
          "phone_number": "+15551230011"
        }'
  ```

- **Example Success Response (201 Created):**
  ```json
  {
      "user": {
          "id": "usr_01HXYZ...",
          "username": "newcustomer01",
          "email": "newcustomer01@example.com",
          "phone_number": "+15551230011",
          "first_name": "Cust",
          "last_name": "Omer",
          "user_type": "customer",
          "profile_picture": null,
          "bio": null,
          "location": null,
          "is_verified": false,
          "rating": 0.0,
          "balance": "0.00",
          "created_at": "2023-10-27T10:05:00Z",
          "updated_at": "2023-10-27T10:05:00Z"
      },
      "tokens": {
          "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      },
      "message": "Customer registered successfully"
  }
  ```
- **Error Responses:** Similar to Generic User Registration.

#### Provider Specific Registration ✅

- **Endpoint:** `POST {{base_url}}/api/v1/auth/provider/register/`
- **Description:** Registers a new user specifically as a 'provider'. Can include an optional `skills` JSON field.
- **Permissions:** Anonymous User
- **Request Body:** `application/json`
  *Required fields: `username`, `email`, `password`, `password_confirm`*
  *Optional fields: `first_name`, `last_name`, `phone_number`, `skills` (JSON object)*
  ```json
  {
      "username": "newprovider01",
      "email": "newprovider01@example.com",
      "password": "providerpass123",
      "password_confirm": "providerpass123",
      "first_name": "Pro",
      "last_name": "Vider",
      "phone_number": "+15551230022",
      "skills": {"cleaning": "5 years experience", "languages": ["english", "spanish"]}
  }
  ```

- **Example cURL Request:** ✅
  ```bash
  curl -X POST {{base_url}}/api/v1/auth/provider/register/ \
    -H "Content-Type: application/json" \
    -d '{
          "username": "newprovider01",
          "email": "newprovider01@example.com",
          "password": "providerpass123",
          "password_confirm": "providerpass123",
          "first_name": "Pro",
          "last_name": "Vider",
          "phone_number": "+15551230022",
          "skills": {"cleaning": "5 years experience", "languages": ["english", "spanish"]}
        }'
  ```

- **Example Success Response (201 Created):**
  ```json
  {
      "user": {
          "id": "usr_01HXYZ...",
          "username": "newprovider01",
          "email": "newprovider01@example.com",
          "phone_number": "+15551230022",
          "first_name": "Pro",
          "last_name": "Vider",
          "user_type": "provider",
          "profile_picture": null,
          "bio": null,
          "location": null,
          "is_verified": false,
          "rating": 0.0,
          "balance": "0.00",
          "created_at": "2023-10-27T10:10:00Z",
          "updated_at": "2023-10-27T10:10:00Z"
      },
      "tokens": {
          "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      },
      "message": "Service Provider registered successfully"
  }
  ```
- **Error Responses:** Similar to Generic User Registration.

#### Admin Specific Registration ✅

- **Endpoint:** `POST {{base_url}}/api/v1/auth/admin/register/`
- **Description:** Registers a new user specifically as an 'admin'. Requires a valid `admin_code`.
- **Permissions:** Anonymous User (effectively restricted by `admin_code`)
- **Request Body:** `application/json`
  *Required fields: `username`, `email`, `password`, `password_confirm`, `admin_code`*
  *Optional fields: `first_name`, `last_name`, `phone_number`*
  ```json
  {
      "username": "newadmin01",
      "email": "newadmin01@example.com",
      "password": "adminpass123",
      "password_confirm": "adminpass123",
      "first_name": "Ad",
      "last_name": "Min",
      "phone_number": "+15551230033",
      "admin_code": "YOUR_VALID_ADMIN_CODE"
  }
  ```

- **Example cURL Request:** ✅
  ```bash
  curl -X POST {{base_url}}/api/v1/auth/admin/register/ \
    -H "Content-Type: application/json" \
    -d '{
          "username": "newadmin01",
          "email": "newadmin01@example.com",
          "password": "adminpass123",
          "password_confirm": "adminpass123",
          "first_name": "Ad",
          "last_name": "Min",
          "phone_number": "+15551230033",
          "admin_code": "YOUR_VALID_ADMIN_CODE"
        }'
  ```

- **Example Success Response (201 Created):**
  ```json
  {
      "user": {
          "id": "usr_01HXYZ...",
          "username": "newadmin01",
          "email": "newadmin01@example.com",
          "phone_number": "+15551230033",
          "first_name": "Ad",
          "last_name": "Min",
          "user_type": "admin",
          "profile_picture": null,
          "bio": null,
          "location": null,
          "is_verified": false,
          "rating": 0.0,
          "balance": "0.00",
          "created_at": "2023-10-27T10:15:00Z",
          "updated_at": "2023-10-27T10:15:00Z"
      },
      "tokens": {
          "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      },
      "message": "Admin registered successfully"
  }
  ```
- **Error Responses:** Similar to Generic User Registration, plus:
  - **Example Error Response (400 Bad Request - Invalid Admin Code):**
    ```json
    {
        "admin_code": [
            "Invalid administrator verification code."
        ]
    }
    ```

---

## User Management

### Generic User Endpoints

#### User Login ✅

- **Endpoint:** `POST {{base_url}}/api/v1/auth/login/`
- **Description:** Authenticates a user with their username/email/phone and password. Returns user data and JWT tokens upon successful login.
- **Permissions:** Anonymous User
- **Request Body:** `application/json`
  *Required: `password`*
  *Optional: `username`, `email`, `phone_number` (at least one of these three must be provided)*
  ```json
  {
      "email": "testuser@example.com",
      "password": "strongpassword123"
  }
  ```

- **Example cURL Request:** ✅
  ```bash
  curl -X POST {{base_url}}/api/v1/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{
          "email": "testuser@example.com",
          "password": "strongpassword123"
        }'
  ```

- **Example Success Response (200 OK):**
  ```json
  {
      "user": {
          "id": "usr_01HABC...",
          "username": "testuser",
          "email": "testuser@example.com",
          "phone_number": "+15551234567",
          "first_name": "Test",
          "last_name": "User",
          "user_type": "customer",
          "profile_picture": null,
          "bio": null,
          "location": null,
          "is_verified": false,
          "rating": 0.0,
          "balance": "0.00",
          "created_at": "2023-10-27T10:20:00Z",
          "updated_at": "2023-10-27T10:20:00Z"
      },
      "tokens": {
          "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      },
      "message": "Customer login successful"
  }
  ```

- **Example Error Response (400 Bad Request - Invalid Credentials):**
  ```json
  {
      "detail": "Unable to log in with provided credentials."
  }
  ```

- **Example Error Response (400 Bad Request - Missing Identifier/Password):**
  ```json
  {
      "email": [
          "This field may not be blank."
      ],
      "password": [
          "This field is required."
      ]
  }
  ```

#### User Logout ✅

- **Endpoint:** `POST {{base_url}}/api/v1/auth/logout/`
- **Description:** Logs out the currently authenticated user by blacklisting their refresh token.
- **Permissions:** Authenticated User
- **Request Body:** `application/json`
  ```json
  {
      "refresh_token": "your_valid_refresh_token_here"
  }
  ```

- **Example cURL Request:** ✅
  ```bash
  curl -X POST {{base_url}}/api/v1/auth/logout/ \
    -H "Authorization: Bearer {{access_token}}" \
    -H "Content-Type: application/json" \
    -d '{
          "refresh_token": "{{refresh_token}}"
        }'
  ```

- **Example Success Response (200 OK):**
  ```json
  {
      "detail": "Successfully logged out."
  }
  ```

- **Example Error Response (400 Bad Request - Refresh Token Required):**
  ```json
  {
      "detail": "Refresh token is required."
  }
  ```

- **Example Error Response (400 Bad Request - Invalid Refresh Token):**
  ```json
  {
      "detail": "Invalid refresh token: Token is blacklisted",
      "code": "token_not_valid"
  }
  ```

#### Get User Profile ✅

- **Endpoint:** `GET {{base_url}}/api/v1/users/me/`
- **Description:** Retrieves the profile of the currently authenticated user.
- **Permissions:** Authenticated User
- **Example cURL Request:** ✅
  ```bash
  curl -X GET {{base_url}}/api/v1/users/me/ \
    -H "Authorization: Bearer {{access_token}}"
  ```

- **Example Success Response (200 OK):**
  ```json
  {
      "id": "usr_01HABC...",
      "username": "testuser",
      "email": "testuser@example.com",
      "phone_number": "+15551234567",
      "first_name": "Test",
      "last_name": "User",
      "user_type": "customer",
      "profile_picture": "https://yourdomain.com/media/avatars/avatar.jpg",
      "bio": "Loves coding and coffee.",
      "location": "San Francisco, CA",
      "is_verified": true,
      "rating": 4.5,
      "balance": "100.00",
      "created_at": "2023-10-27T10:20:00Z",
      "updated_at": "2023-10-28T11:00:00Z"
  }
  ```

- **Example Error Response (401 Unauthorized):**
  ```json
  {
      "detail": "Authentication credentials were not provided."
  }
  ```

#### Update User Profile (PUT) ✅

- **Endpoint:** `PUT {{base_url}}/api/v1/users/me/`
- **Description:** Updates the entire profile of the currently authenticated user. All writable fields must be provided.
- **Permissions:** Authenticated User
- **Request Body:** `application/json` (Fields based on `UserProfileSerializer` writable fields: `username`, `phone_number`, `first_name`, `last_name`, `profile_picture` (URL string), `bio`, `location`)
  ```json
  {
      "username": "updateduser",
      "phone_number": "+15557654321",
      "first_name": "UpdatedFirstName",
      "last_name": "UpdatedLastName",
      "profile_picture": "https://yourdomain.com/media/avatars/new_avatar.jpg",
      "bio": "Updated bio here.",
      "location": "New York, NY"
  }
  ```

- **Example cURL Request:** ✅
  ```bash
  curl -X PUT {{base_url}}/api/v1/users/me/ \
    -H "Authorization: Bearer {{access_token}}" \
    -H "Content-Type: application/json" \
    -d '{
          "username": "updateduser",
          "phone_number": "+15557654321",
          "first_name": "UpdatedFirstName",
          "last_name": "UpdatedLastName",
          "profile_picture": "https://yourdomain.com/media/avatars/new_avatar.jpg",
          "bio": "Updated bio here.",
          "location": "New York, NY"
        }'
  ```

- **Example Success Response (200 OK):** (Returns the updated user profile)
  ```json
  {
      "id": "usr_01HABC...",
      "username": "updateduser",
      "email": "testuser@example.com",
      "phone_number": "+15557654321",
      "first_name": "UpdatedFirstName",
      "last_name": "UpdatedLastName",
      "user_type": "customer",
      "profile_picture": "https://yourdomain.com/media/avatars/new_avatar.jpg",
      "bio": "Updated bio here.",
      "location": "New York, NY",
      "is_verified": true,
      "rating": 4.5,
      "balance": "100.00",
      "created_at": "2023-10-27T10:20:00Z",
      "updated_at": "2023-10-28T12:00:00Z"
  }
  ```

- **Example Error Response (400 Bad Request - Validation Error):**
  ```json
  {
      "username": [
          "A user with that username already exists."
      ]
  }
  ```

#### Partially Update User Profile (PATCH) ✅

- **Endpoint:** `PATCH {{base_url}}/api/v1/users/me/`
- **Description:** Partially updates the profile of the currently authenticated user. Only include fields to be updated.
- **Permissions:** Authenticated User
- **Request Body:** `application/json` (Any subset of writable fields from `UserProfileSerializer`)
  ```json
  {
      "bio": "A new, concise bio.",
      "location": "Remote"
  }
  ```

- **Example cURL Request:** ✅
  ```bash
  curl -X PATCH {{base_url}}/api/v1/users/me/ \
    -H "Authorization: Bearer {{access_token}}" \
    -H "Content-Type: application/json" \
    -d '{
          "bio": "A new, concise bio.",
          "location": "Remote"
        }'
  ```

- **Example Success Response (200 OK):** (Returns the updated user profile)
  ```json
  {
      "id": "usr_01HABC...",
      "username": "updateduser", 
      "email": "testuser@example.com",
      "phone_number": "+15557654321", 
      "first_name": "UpdatedFirstName", 
      "last_name": "UpdatedLastName", 
      "user_type": "customer",
      "profile_picture": "https://yourdomain.com/media/avatars/new_avatar.jpg", 
      "bio": "A new, concise bio.",
      "location": "Remote",
      "is_verified": true,
      "rating": 4.5,
      "balance": "100.00",
      "created_at": "2023-10-27T10:20:00Z",
      "updated_at": "2023-10-28T12:05:00Z"
  }
  ```
- **Error Responses:** Similar to PUT, e.g., validation errors, 401.
## User Management

### Generic User Endpoints
*Base Path: `/api/v1/users/`*
- `GET me/` - Retrieve current authenticated user's profile.
- `PUT me/` - Update current authenticated user's profile.
- `PATCH me/` - Partially update current authenticated user's profile.
- `POST me/avatar/` - Upload avatar for the current user. (Ref: Postman Collection)
- `POST profile/image/` - Upload profile image for the current user. (Note: Postman collection path was `me/profile/image/`)
- `POST me/change-password/` - Change current authenticated user's password. (Ref: Postman Collection)
- `POST me/deactivate/` - Deactivate current authenticated user's account. (Ref: Postman Collection, not directly in `users/urls.py` but likely handled by `UserProfileView`)
- `GET {user_id}/` - Retrieve a public user profile by ID. (Ref: Postman Collection)
- `POST {user_id}/like/` - Like a user's profile. (Ref: Postman Collection)
- `POST {user_id}/pass/` - Pass on a user's profile. (Ref: Postman Collection)
- `POST verify/` - Submit or check user verification status/details (general verification, not the dedicated module).

### Customer Specific Endpoints
*Base Path: `/api/v1/users/customer/`*
- `GET me/` - Retrieve current authenticated customer's profile.
- `PUT me/` - Update current authenticated customer's profile.
- `PATCH me/` - Partially update current authenticated customer's profile.

### Provider Specific Endpoints
*Base Path: `/api/v1/users/provider/`*
- `GET me/` - Retrieve current authenticated provider's profile.
- `PUT me/` - Update current authenticated provider's profile.
- `PATCH me/` - Partially update current authenticated provider's profile.

### Admin Specific Endpoints (Profile)
*Base Path: `/api/v1/users/admin/`*
- `GET me/` - Retrieve current authenticated admin's profile.
- `PUT me/` - Update current authenticated admin's profile. (Ref: Postman Collection)
- `PATCH me/` - Partially update current authenticated admin's profile. (Ref: Postman Collection)

### User Search
*Base Path: `/api/v1/users/search/`*
- `GET /` - Search users by various criteria (username, email, phone, name). Supports query parameters. (Ref: Memory `ce4e0ed1-2210-421a-9da4-7af6310ee741`)
- `GET phone/` - Search users specifically by phone number. (Ref: Memory `ce4e0ed1-2210-421a-9da4-7af6310ee741`)

---

## Services & Service Requests

### Public Service & Category Endpoints
*Base Path: `/api/v1/services/`*

#### Service Categories (`categories/`)
- `GET categories/` - List all service categories. (Ref: Postman Collection `Public Endpoints`)
- `POST categories/` - Create a new service category (Admin).
- `GET categories/{id}/` - Retrieve a specific service category. (Ref: Postman Collection `Public Endpoints`)
- `PUT categories/{id}/` - Update a service category (Admin).
- `PATCH categories/{id}/` - Partially update a service category (Admin).
- `DELETE categories/{id}/` - Delete a service category (Admin).

#### Service Subcategories (`subcategories/`)
- `GET subcategories/` - List all service subcategories. (Ref: Postman Collection `Public Endpoints`)
- `POST subcategories/` - Create a new service subcategory (Admin).
- `GET subcategories/{id}/` - Retrieve a specific service subcategory. (Ref: Postman Collection `Public Endpoints`)
- `PUT subcategories/{id}/` - Update a service subcategory (Admin).
- `PATCH subcategories/{id}/` - Partially update a service subcategory (Admin).
- `DELETE subcategories/{id}/` - Delete a service subcategory (Admin).

#### Services (`/` relative to base path `/api/v1/services/`)
- `GET /` - List all services (Public). (Ref: Postman Collection `Public Endpoints`)
- `POST /` - Create a new service (Provider/Admin).
- `GET /{id}/` - Retrieve a specific service (Public). (Ref: Postman Collection `Public Endpoints`)
- `PUT /{id}/` - Update a service (Provider/Admin).
- `PATCH /{id}/` - Partially update a service (Provider/Admin).
- `DELETE /{id}/` - Delete a service (Provider/Admin).

### Service Requests (All Roles)
*Base Path: `/api/v1/service-requests/`*
- `GET /` - List service requests. (Behavior varies by user role: Customer sees own, Provider sees requests for their services, Admin sees all).
- `POST /` - Create a new service request (Customer).
- `GET /{id}/` - Retrieve a specific service request.
- `PUT /{id}/` - Update a service request (e.g., status by Provider/Customer).
- `PATCH /{id}/` - Partially update a service request.
- `DELETE /{id}/` - Cancel/delete a service request (Customer or Admin).
(Ref: Postman Collection `Services & Service Requests`)

---

## Products
*Base Path: `/api/v1/products/`*

<h4 id="product-categories">Product Categories (`categories/`)</h4>
- `GET categories/` - List all product categories.
- `POST categories/` - Create a new product category.
- `GET categories/{id}/` - Retrieve a specific product category.
- `PUT categories/{id}/` - Update a product category.
- `PATCH categories/{id}/` - Partially update a product category.
- `DELETE categories/{id}/` - Delete a product category.

<h4 id="products-individual">Products (`/` relative to base path `/api/v1/products/`)</h4>
- `GET /` - List all products.
- `POST /` - Create a new product.
- `GET /{id}/` - Retrieve a specific product.
- `PUT /{id}/` - Update a product.
- `PATCH /{id}/` - Partially update a product.
- `DELETE /{id}/` - Delete a product.

---

## Bids
*Base Path: `/api/v1/bids/`*
- `GET /` - List bids (context-dependent on user role).
- `POST /` - Create a new bid.
- `GET /{id}/` - Retrieve a specific bid.
- `PUT /{id}/` - Update a bid.
- `PATCH /{id}/` - Partially update a bid.
- `DELETE /{id}/` - Delete/cancel a bid.
*Note: May include custom actions like `accept`, `reject` based on `BidModel` (Ref: Memory `64b7fcd8-50a5-482d-bb41-83e5d8bfad5f`).*

---

## Bookings
*Base Path: `/api/v1/bookings/`*
- `GET /` - List bookings (context-dependent on user role).
- `POST /` - Create a new booking.
- `GET /{id}/` - Retrieve a specific booking.
- `PUT /{id}/` - Update a booking.
- `PATCH /{id}/` - Partially update a booking.
- `DELETE /{id}/` - Delete/cancel a booking.

---

## Calendar Integration
*Base Path: `/api/integrations/calendar/sync/`*
- `POST /` - Synchronize bookings with an external calendar.

---

## Payments
*Base Path: `/api/v1/payments/`*

<h4 id="payment-processing">Payment Processing (`payments/`)</h4>
- `GET payments/` - List payments.
- `POST payments/` - Create/initiate a payment.
- `GET payments/{id}/` - Retrieve a specific payment.
- `PUT payments/{id}/` - Update a payment (e.g., capture, refund).
- `PATCH payments/{id}/` - Partially update a payment.
- `DELETE payments/{id}/` - Delete a payment record (if applicable).

<h4 id="payment-gateway-accounts">Payment Gateway Accounts (`accounts/`)</h4>
- `GET accounts/` - List payment gateway accounts for a user.
- `POST accounts/` - Add a new payment gateway account.
- `GET accounts/{id}/` - Retrieve a specific payment gateway account.
- `PUT accounts/{id}/` - Update a payment gateway account.
- `PATCH accounts/{id}/` - Partially update a payment gateway account.
- `DELETE accounts/{id}/` - Remove a payment gateway account.

<h4 id="payouts">Payouts (`payouts/`)</h4>
- `GET payouts/` - List payouts.
- `POST payouts/` - Initiate a payout.
- `GET payouts/{id}/` - Retrieve a specific payout.
- `PUT payouts/{id}/` - Update a payout.
- `PATCH payouts/{id}/` - Partially update a payout.
- `DELETE payouts/{id}/` - Delete a payout record (if applicable).

---

## Messaging
*Base Path: `/api/v1/messaging/`*

<h4 id="message-threads">Message Threads (`threads/`)</h4>
- `GET threads/` - List message threads for the user.
- `POST threads/` - Create a new message thread.
- `GET threads/{id}/` - Retrieve a specific message thread.
- `PUT threads/{id}/` - Update a message thread (e.g., archive, mark as read).
- `PATCH threads/{id}/` - Partially update a message thread.
- `DELETE threads/{id}/` - Delete a message thread.

<h4 id="individual-messages">Individual Messages (`messages/`)</h4>
- `GET messages/` - List all messages (less common, usually per thread).
- `POST messages/` - Create a new message (might require thread ID in body).
- `GET messages/{id}/` - Retrieve a specific message.
- `PUT messages/{id}/` - Update a message (e.g., edit, if allowed).
- `PATCH messages/{id}/` - Partially update a message.
- `DELETE messages/{id}/` - Delete a message.

<h4 id="messages-within-a-thread">Messages within a Thread (`{thread_id}/`)</h4>
- `GET {thread_id}/` - List all messages within a specific thread.
- `POST {thread_id}/` - Create a new message within a specific thread.

---

## Notifications (HTTP)
*Base Path: `/api/v1/notifications/`*
- `GET /` - List notifications for the user.
- `POST /` - Create a notification (Admin/System).
- `GET /{id}/` - Retrieve a specific notification.
- `PUT /{id}/` - Update a notification (e.g., mark as read/unread).
- `PATCH /{id}/` - Partially update a notification.
- `DELETE /{id}/` - Delete a notification.
*(Ref: Postman memories for `notification_id_example`, `notification_group_id_example`)*

---

## AI Suggestions & Feedback
*Base Path: `/api/v1/ai-suggestions/`*

<h4 id="ai-suggestions">AI Suggestions (`suggestions/`)</h4>
- `GET suggestions/` - List AI suggestions.
- `POST suggestions/` - Create an AI suggestion (System).
- `GET suggestions/{id}/` - Retrieve a specific AI suggestion.
- `PUT suggestions/{id}/` - Update an AI suggestion.
- `PATCH suggestions/{id}/` - Partially update an AI suggestion.
- `DELETE suggestions/{id}/` - Delete an AI suggestion.

<h4 id="ai-feedback-logs">AI Feedback Logs (`feedback/`)</h4>
- `GET feedback/` - List AI feedback logs.
- `POST feedback/` - Submit feedback on an AI suggestion. (Ref: Memory `1fe08a85-673c-4be0-8c4e-7e7c5b6ef8c1` for `suggestion_id`)
- `GET feedback/{id}/` - Retrieve a specific AI feedback log.
- `PUT feedback/{id}/` - Update an AI feedback log.
- `PATCH feedback/{id}/` - Partially update an AI feedback log.
- `DELETE feedback/{id}/` - Delete an AI feedback log.

---

## Verifications (User Identity, etc.)
*Base Path: `/api/v1/verifications/` (Dedicated Verification Module)*
- `GET /` - List verification requests/statuses (Admin or user's own).
- `POST /` - Submit a new verification request.
- `GET /{id}/` - Retrieve a specific verification request/status. (Ref: Memory `76429f2f-b18a-40a9-bb2c-a2970f68f711` for `verification_id_example`)
- `PUT /{id}/` - Update a verification request (Admin: approve, reject).
- `PATCH /{id}/` - Partially update a verification request.
- `DELETE /{id}/` - Delete a verification request.
*(Ref: Memory `50207863-abec-4f83-85d2-39b0076ce3a8` for `VerificationModel` details)*

---

## Reviews
*Base Path: `/api/v1/reviews/`*
- `GET /` - List reviews (can be filtered by service_id, booking_id, user_id etc. via query params).
- `POST /` - Create a new review (requires `service_id`, `booking_id`).
- `GET /{id}/` - Retrieve a specific review. (Ref: Memory `5d141c3b-05a3-4180-8249-75b3694a9deb` for `review_id`)
- `PUT /{id}/` - Update a review (User who wrote it, or Admin).
- `PATCH /{id}/` - Partially update a review.
- `DELETE /{id}/` - Delete a review (User who wrote it, or Admin).

---

## Sync (Offline Functionality)
*Base Path: `/api/sync/`*
- `GET profile/` - Download user profile data for offline use.
- `GET services/` - Download service data for offline browsing.
- `POST upload/` - Upload changes made offline to the backend.

---

## Analytics & Admin Management
*Base Path: `/api/analytics/`*

### Analytics Reports
- `GET overview/` - Retrieve analytics overview data (Admin).
- `GET earnings/` - Retrieve earnings analytics data (Admin, may require `{{admin_access_token_financial}}` - Ref: Memory `f7210385-3649-49aa-a174-a0f45d7ceb8a`).

### Admin User Management
*Base Path: `/api/analytics/admin/users/` (Note: Postman collection may refer to `/api/v1/admin/users/`)*
- `GET /` - List all users (Admin).
- `POST /` - Create a new user (Admin). (Ref: Postman Collection `POST /api/v1/admin/users/`)
- `GET /{id}/` - Retrieve a specific user by ID (Admin).
- `PUT /{id}/` - Update a user by ID (Admin).
- `PATCH /{id}/` - Partially update a user by ID (Admin).
- `DELETE /{id}/` - Delete a user by ID (Admin). (Ref: Postman Collection `DELETE /api/v1/admin/users/{{user_id}}/`)

### Admin Service Management
*Base Path: `/api/analytics/admin/services/` (Note: Postman collection may refer to `/api/v1/admin/services/`)*
- `GET /` - List all services (Admin). (Ref: Postman Collection)
- `POST /` - Create a new service (Admin). (Ref: Postman Collection)
- `GET /{id}/` - Retrieve a specific service by ID (Admin). (Ref: Postman Collection)
- `PUT /{id}/` - Update a service by ID (Admin). (Ref: Postman Collection)
- `PATCH /{id}/` - Partially update a service by ID (Admin). (Ref: Postman Collection)
- `DELETE /{id}/` - Delete a service by ID (Admin). (Ref: Postman Collection)

---

## WebSocket APIs
- `WS {{base_url_ws}}/ws/notifications/?token={{access_token}}` - Real-time notifications. (Ref: Memory `79e2eeff-3784-4c48-b35d-78065b4cac29`)

---

## Health Checks
- `GET /health/` - System health check.
- `GET /health/db/` - Database connectivity health check.

---

## Metrics
- `GET /metrics` - Prometheus metrics endpoint (assuming standard path for `django_prometheus.urls`).

## WebSocket APIs

This section details the WebSocket APIs available in the Prbal backend, primarily for real-time communication.

### Notifications WebSocket API

**Endpoint:** `ws/notifications/`

**Consumer:** `notifications.consumers.NotificationConsumer`

**Description:** This WebSocket API provides real-time notification updates and allows users to manage their notifications. It is designed for authenticated users (customers, providers, and admins).

#### Client-to-Server Messages (User Actions)

Users send messages to the server to perform actions related to notifications.

*   **`mark_read`**: Mark a specific notification as read.
    *   **Payload:**
        ```json
        {
            "type": "mark_read",
            "notification_id": "UUID_of_notification"
        }
        ```

*   **`mark_all_read`**: Mark all unread notifications for the user as read.
    *   **Payload:**
        ```json
        {
            "type": "mark_all_read"
        }
        ```

*   **`get_notifications`**: Request a list of recent notifications for the user.
    *   **Payload:**
        ```json
        {
            "type": "get_notifications"
        }
        ```

*   **`archive_notification`**: Archive a specific notification.
    *   **Payload:**
        ```json
        {
            "type": "archive_notification",
            "notification_id": "UUID_of_notification"
        }
        ```

#### Server-to-Client Messages (Server Updates)

The server sends messages to the client to provide real-time updates or responses to client actions.

*   **`notification`**: Sends a new notification to the user.
    *   **Payload:**
        ```json
        {
            "type": "notification",
            "id": "UUID_of_notification",
            "notification_type": "type_of_notification",
            "title": "Notification Title",
            "message": "Notification Message",
            "content_type": "optional_content_type",
            "object_id": "optional_object_id",
            "action_url": "optional_action_url",
            "timestamp": "ISO_timestamp",
            "is_read": false,
            "group_id": "optional_group_id"
        }
        ```

*   **`notification_count`**: Updates the unread notification count for the user.
    *   **Payload:**
        ```json
        {
            "type": "notification_count",
            "unread_count": integer
        }
        ```

*   **`notification_list`**: Sends a list of recent notifications to the user.
    *   **Payload:**
        ```json
        {
            "type": "notification_list",
            "notifications": [
                {
                    "id": "UUID",
                    "notification_type": "type",
                    "title": "Title",
                    "message": "Message",
                    "is_read": boolean,
                    "action_url": "url",
                    "timestamp": "ISO_timestamp",
                    "group_id": "UUID"
                },
                // ... more notifications
            ]
        }
        ```

*   **`notification_read`**: Acknowledges that a specific notification has been marked as read.
    *   **Payload:**
        ```json
        {
            "type": "notification_read",
            "notification_id": "UUID_of_notification"
        }
        ```

*   **`all_notifications_read`**: Acknowledges that all notifications have been marked as read.
    *   **Payload:**
        ```json
        {
            "type": "all_notifications_read"
        }
        ```

*   **`notification_archived`**: Acknowledges that a specific notification has been archived.
    *   **Payload:**
        ```json
        {
            "type": "notification_archived",
            "notification_id": "UUID_of_notification"
        }
        ```
  "message": "Login successful."
}
```

**Example Response (Error 400 Bad Request / 401 Unauthorized):**
```json
{
  "detail": "Invalid credentials."
}
```

#### POST /api/v1/auth/logout/
Log out the current authenticated user. This typically involves blacklisting the refresh token.

**cURL Example:**
```bash
curl -X POST -H "Authorization: Bearer YOUR_ACCESS_TOKEN" -H "Content-Type: application/json" \
-d '{
  "refresh": "YOUR_REFRESH_TOKEN"
}' \
http://localhost:8000/api/v1/auth/logout/
```

**Example Request Body (Required if your backend needs the refresh token to blacklist it):**
```json
{
  "refresh": "YOUR_REFRESH_TOKEN"
}
```

**Example Response (Success 200 OK or 204 No Content):**
```json
{
  "detail": "Successfully logged out."
}
```
*(Or an empty response with status 204)*

**Example Response (Error 401 Unauthorized):**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

#### POST /api/v1/auth/token/refresh/
Alternative path to refresh JWT access token. Functionally identical to `/api/token/refresh/`.

**cURL Example:**
```bash
curl -X POST -H "Content-Type: application/json" \
-d '{
  "refresh": "YOUR_REFRESH_TOKEN"
}' \
http://localhost:8000/api/v1/auth/token/refresh/
```

**Example Request Body:**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Example Response (Success 200 OK):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...new_access_token"
}
```

**Example Response (Error 401 Unauthorized):**
```json
{
  "detail": "Token is invalid or expired",
  "code": "token_not_valid"
}
```

---

## User Management

### Generic User Endpoints
Base Path: `/api/v1/`

These endpoints are for managing user profiles and interactions that are not specific to a user type (customer, provider, admin).

---

#### 1. Retrieve or Update Current Authenticated User's Profile
- **Endpoint:** `users/me/`
- **Method:** `GET`, `PUT`, `PATCH`
- **Description:** Allows the authenticated user to retrieve or update their own profile details.
- **Permissions:** Authenticated User

**GET `users/me/`**
- **Description:** Retrieve the profile of the currently authenticated user.

  **Example cURL Request:**
  ```bash
  curl -X GET https://yourdomain.com/api/v1/users/me/ \
    -H "Authorization: Bearer <your_access_token>"
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "username": "currentuser",
    "email": "user@example.com",
    "first_name": "Current",
    "last_name": "User",
    "phone_number": "+1234567890",
    "profile": {
      "bio": "This is my bio.",
      "date_of_birth": "1990-01-01",
      "profile_picture_url": "https://yourdomain.com/media/avatars/user_avatar.jpg",
      "cover_photo_url": "https://yourdomain.com/media/covers/user_cover.jpg",
      "address": "123 Main St, Anytown, USA",
      "user_type": "customer"
    }
  }
  ```

**PUT `users/me/`**
- **Description:** Update the entire profile of the currently authenticated user. All fields must be provided.

  **Example cURL Request:**
  ```bash
  curl -X PUT https://yourdomain.com/api/v1/users/me/ \
    -H "Authorization: Bearer <your_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "first_name": "UpdatedFirstName",
          "last_name": "UpdatedLastName",
          "email": "updated_user@example.com",
          "profile": {
            "bio": "An updated bio.",
            "date_of_birth": "1990-01-15",
            "address": "456 New Ave, Anytown, USA"
          }
        }'
  ```

  **Example JSON Request Body:**
  ```json
  {
    "first_name": "UpdatedFirstName",
    "last_name": "UpdatedLastName",
    "email": "updated_user@example.com",
    "profile": {
      "bio": "An updated bio.",
      "date_of_birth": "1990-01-15",
      "address": "456 New Ave, Anytown, USA"
    }
  }
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "username": "currentuser",
    "email": "updated_user@example.com",
    "first_name": "UpdatedFirstName",
    "last_name": "UpdatedLastName",
    "phone_number": "+1234567890",
    "profile": {
      "bio": "An updated bio.",
      "date_of_birth": "1990-01-15",
      "profile_picture_url": "https://yourdomain.com/media/avatars/user_avatar.jpg",
      "cover_photo_url": "https://yourdomain.com/media/covers/user_cover.jpg",
      "address": "456 New Ave, Anytown, USA",
      "user_type": "customer"
    }
  }
  ```

**PATCH `users/me/`**
- **Description:** Partially update the profile of the currently authenticated user. Only include fields to be updated.

  **Example cURL Request:**
  ```bash
  curl -X PATCH https://yourdomain.com/api/v1/users/me/ \
    -H "Authorization: Bearer <your_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "profile": {
            "bio": "A newer bio."
          }
        }'
  ```

  **Example JSON Request Body:**
  ```json
  {
    "profile": {
      "bio": "A newer bio."
    }
  }
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "username": "currentuser",
    "email": "updated_user@example.com",
    "first_name": "Current",
    "last_name": "User",
    "phone_number": "+1234567890",
    "profile": {
      "bio": "A newer bio.",
      "date_of_birth": "1990-01-15",
      "profile_picture_url": "https://yourdomain.com/media/avatars/user_avatar.jpg",
      "cover_photo_url": "https://yourdomain.com/media/covers/user_cover.jpg",
      "address": "456 New Ave, Anytown, USA",
      "user_type": "customer"
    }
  }
  ```

  **Example Response (Error 401 Unauthorized):**
  ```json
  {
    "detail": "Authentication credentials were not provided."
  }
  ```

  **Example Response (Error 400 Bad Request - Validation Error):**
  ```json
  {
    "email": ["Enter a valid email address."],
    "profile": {
        "date_of_birth": ["Date has wrong format. Use one of these formats instead: YYYY-MM-DD."]
    }
  }
  ```

---

#### 2. Upload Avatar for Current User
- **Endpoint:** `users/me/avatar/`
- **Method:** `POST`
- **Description:** Allows the authenticated user to upload or update their avatar (profile picture).
- **Permissions:** Authenticated User

  **Example cURL Request (Multipart/Form-Data):**
  ```bash
  curl -X POST https://yourdomain.com/api/v1/users/me/avatar/ \
    -H "Authorization: Bearer <your_access_token>" \
    -F "avatar=@/path/to/your/avatar_image.jpg"
  ```
  *Note: `@/path/to/your/avatar_image.jpg` specifies the local file path for the image.*

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "message": "Avatar uploaded successfully.",
    "avatar_url": "https://yourdomain.com/media/avatars/user_123e4567_avatar.jpg"
  }
  ```

  **Example JSON Response (Error 400 Bad Request - No file or invalid file):**
  ```json
  {
    "avatar": ["No file was submitted."]
  }
  ```
  ```json
  {
    "avatar": ["The submitted file is not an image."]
  }
  ```

---

#### 3. Upload Profile Image
- **Endpoint:** `users/profile/image/`
- **Method:** `POST`
- **Description:** Allows the authenticated user to upload or update a general profile image (e.g., cover photo, background image). This might be distinct from the avatar.
- **Permissions:** Authenticated User

  **Example cURL Request (Multipart/Form-Data):**
  ```bash
  curl -X POST https://yourdomain.com/api/v1/users/profile/image/ \
    -H "Authorization: Bearer <your_access_token>" \
    -F "profile_image=@/path/to/your/profile_image.jpg"
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "message": "Profile image uploaded successfully.",
    "image_url": "https://yourdomain.com/media/profile_images/user_123e4567_profile.jpg"
  }
  ```

  **Example JSON Response (Error 400 Bad Request):**
  ```json
  {
    "profile_image": ["Invalid image format. Allowed formats: JPG, PNG."]
  }
  ```

---

#### 4. Retrieve a Public User Profile by ID
- **Endpoint:** `users/<uuid:id>/`
- **Method:** `GET`
- **Description:** Retrieve public information about a specific user by their UUID.
- **Permissions:** Any User (Authenticated or Anonymous, depending on privacy settings)

  **Example cURL Request:**
  ```bash
  curl -X GET https://yourdomain.com/api/v1/users/a1b2c3d4-e5f6-7890-1234-567890abcdef/ \
    -H "Authorization: Bearer <your_access_token>" # Optional, may provide more details if authenticated
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "username": "otheruser",
    "first_name": "Other",
    "last_name": "User",
    "profile": {
      "bio": "Public bio of other user.",
      "profile_picture_url": "https://yourdomain.com/media/avatars/otheruser_avatar.jpg",
      "user_type": "provider"
    }
  }
  ```

  **Example JSON Response (Error 404 Not Found):**
  ```json
  {
    "detail": "Not found."
  }
  ```

---

#### 5. Like a User Profile
- **Endpoint:** `users/<uuid:id>/like/`
- **Method:** `POST`
- **Description:** Allows the authenticated user to "like" another user's profile.
- **Permissions:** Authenticated User

  **Example cURL Request:**
  ```bash
  curl -X POST https://yourdomain.com/api/v1/users/a1b2c3d4-e5f6-7890-1234-567890abcdef/like/ \
    -H "Authorization: Bearer <your_access_token>"
  ```

  **Example JSON Response (Success 200 OK - Liked):**
  ```json
  {
    "status": "liked",
    "message": "User profile liked successfully."
  }
  ```

  **Example JSON Response (Success 200 OK - Unliked, if it's a toggle and user already liked):**
  ```json
  {
    "status": "unliked",
    "message": "User profile unliked."
  }
  ```

  **Example JSON Response (Error 404 Not Found - User to like does not exist):**
  ```json
  {
    "detail": "User not found."
  }
  ```

  **Example JSON Response (Error 400 Bad Request - Cannot like own profile):**
  ```json
  {
    "detail": "You cannot like your own profile."
  }
  ```

---

#### 6. Pass on a User Profile
- **Endpoint:** `users/<uuid:id>/pass/`
- **Method:** `POST`
- **Description:** Allows the authenticated user to "pass" on (or "skip") another user's profile, often used in matching or discovery contexts.
- **Permissions:** Authenticated User

  **Example cURL Request:**
  ```bash
  curl -X POST https://yourdomain.com/api/v1/users/a1b2c3d4-e5f6-7890-1234-567890abcdef/pass/ \
    -H "Authorization: Bearer <your_access_token>"
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "status": "passed",
    "message": "User profile passed successfully."
  }
  ```

  **Example JSON Response (Error 404 Not Found - User to pass does not exist):**
  ```json
  {
    "detail": "User not found."
  }
  ```

  **Example JSON Response (Error 400 Bad Request - Cannot pass own profile):**
  ```json
  {
    "detail": "You cannot pass your own profile."
  }
  ```

### Customer Specific Endpoints
Base Path: `/api/v1/`

These endpoints are specifically for customer-related actions such as registration, login, and profile management.

---

#### 1. Register a New Customer
- **Endpoint:** `auth/customer/register/`
- **Method:** `POST`
- **Description:** Allows a new user to register as a customer.
- **Permissions:** Anonymous User

  **Example cURL Request:**
  ```bash
  curl -X POST https://yourdomain.com/api/v1/auth/customer/register/ \
    -H "Content-Type: application/json" \
    -d '{
          "username": "newcustomer",
          "email": "customer@example.com",
          "password": "StrongPassword123!",
          "first_name": "New",
          "last_name": "Customer",
          "phone_number": "+1987654321"
        }'
  ```

  **Example JSON Request Body:**
  ```json
  {
    "username": "newcustomer",
    "email": "customer@example.com",
    "password": "StrongPassword123!",
    "first_name": "New",
    "last_name": "Customer",
    "phone_number": "+1987654321"
  }
  ```

  **Example JSON Response (Success 201 Created):**
  ```json
  {
    "id": "abcdef01-2345-6789-abcd-ef0123456789",
    "username": "newcustomer",
    "email": "customer@example.com",
    "first_name": "New",
    "last_name": "Customer",
    "phone_number": "+1987654321",
    "profile": {
        "user_type": "customer"
    },
    "message": "Customer registered successfully. Please check your email to verify your account."
  }
  ```
  *Note: The response might also include JWT tokens (access, refresh) if registration immediately logs the user in.*

  **Example JSON Response (Error 400 Bad Request - Validation Error):**
  ```json
  {
    "username": ["A user with that username already exists."],
    "email": ["Enter a valid email address."],
    "password": ["This password is too common."]
  }
  ```

---

#### 2. Log In as a Customer
- **Endpoint:** `auth/customer/login/`
- **Method:** `POST`
- **Description:** Allows an existing customer to log in and obtain authentication tokens.
- **Permissions:** Anonymous User

  **Example cURL Request:**
  ```bash
  curl -X POST https://yourdomain.com/api/v1/auth/customer/login/ \
    -H "Content-Type: application/json" \
    -d '{
          "email_or_username": "customer@example.com",
          "password": "StrongPassword123!"
        }'
  ```

  **Example JSON Request Body:**
  ```json
  {
    "email_or_username": "customer@example.com", 
    "password": "StrongPassword123!"
  }
  ```
  *Note: `email_or_username` can be either the user's email or username.*

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTcxOTQwNjY4MSwianRpIjoiZmU5Yz...",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzE5MzIwMjgxLCJqdGkiOiI5Yz...",
    "user": {
        "id": "abcdef01-2345-6789-abcd-ef0123456789",
        "username": "newcustomer",
        "email": "customer@example.com",
        "user_type": "customer"
    },
    "message": "Login successful."
  }
  ```

  **Example JSON Response (Error 401 Unauthorized - Invalid Credentials):**
  ```json
  {
    "detail": "No active account found with the given credentials."
  }
  ```

---

#### 3. Retrieve or Update Current Authenticated Customer's Profile
- **Endpoint:** `users/customer/me/`
- **Method:** `GET`, `PUT`, `PATCH`
- **Description:** Allows an authenticated customer to retrieve or update their own specific customer profile details.
- **Permissions:** Authenticated Customer

**GET `users/customer/me/`**
- **Description:** Retrieve the profile of the currently authenticated customer.

  **Example cURL Request:**
  ```bash
  curl -X GET https://yourdomain.com/api/v1/users/customer/me/ \
    -H "Authorization: Bearer <customer_access_token>"
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "abcdef01-2345-6789-abcd-ef0123456789",
    "username": "newcustomer",
    "email": "customer@example.com",
    "first_name": "New",
    "last_name": "Customer",
    "phone_number": "+1987654321",
    "profile": {
      "bio": "Customer bio here.",
      "date_of_birth": "1995-05-10",
      "profile_picture_url": "https://yourdomain.com/media/avatars/customer_avatar.jpg",
      "address": "789 Customer Ln, Townsville, USA",
      "user_type": "customer",
      "preferences": {
        "newsletter_subscribed": true,
        "preferred_language": "en"
      }
    }
  }
  ```

**PUT `users/customer/me/`**
- **Description:** Update the entire customer profile. All fields required for update must be provided.

  **Example cURL Request:**
  ```bash
  curl -X PUT https://yourdomain.com/api/v1/users/customer/me/ \
    -H "Authorization: Bearer <customer_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "first_name": "UpdatedCustomerFirst",
          "last_name": "UpdatedCustomerLast",
          "profile": {
            "bio": "Updated customer bio.",
            "preferences": {
                "newsletter_subscribed": false
            }
          }
        }'
  ```

  **Example JSON Request Body:**
  ```json
  {
    "first_name": "UpdatedCustomerFirst",
    "last_name": "UpdatedCustomerLast",
    "profile": {
      "bio": "Updated customer bio.",
      "preferences": {
          "newsletter_subscribed": false
      }
    }
  }
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "abcdef01-2345-6789-abcd-ef0123456789",
    "username": "newcustomer",
    "email": "customer@example.com",
    "first_name": "UpdatedCustomerFirst",
    "last_name": "UpdatedCustomerLast",
    "phone_number": "+1987654321",
    "profile": {
      "bio": "Updated customer bio.",
      "date_of_birth": "1995-05-10",
      "profile_picture_url": "https://yourdomain.com/media/avatars/customer_avatar.jpg",
      "address": "789 Customer Ln, Townsville, USA",
      "user_type": "customer",
      "preferences": {
        "newsletter_subscribed": false,
        "preferred_language": "en"
      }
    }
  }
  ```

**PATCH `users/customer/me/`**
- **Description:** Partially update the customer profile. Only include fields to be updated.

  **Example cURL Request:**
  ```bash
  curl -X PATCH https://yourdomain.com/api/v1/users/customer/me/ \
    -H "Authorization: Bearer <customer_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "profile": {
            "preferences": {
                "preferred_language": "es"
            }
          }
        }'
  ```

  **Example JSON Request Body:**
  ```json
  {
    "profile": {
      "preferences": {
          "preferred_language": "es"
      }
    }
  }
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "abcdef01-2345-6789-abcd-ef0123456789",
    "username": "newcustomer",
    "email": "customer@example.com",
    "first_name": "UpdatedCustomerFirst",
    "last_name": "UpdatedCustomerLast",
    "phone_number": "+1987654321",
    "profile": {
      "bio": "Updated customer bio.",
      "date_of_birth": "1995-05-10",
      "profile_picture_url": "https://yourdomain.com/media/avatars/customer_avatar.jpg",
      "address": "789 Customer Ln, Townsville, USA",
      "user_type": "customer",
      "preferences": {
        "newsletter_subscribed": false,
        "preferred_language": "es"
      }
    }
  }
  ```

  **Example Response (Error 403 Forbidden - If a non-customer tries to access):**
  ```json
  {
    "detail": "You do not have permission to perform this action."
  }
  ```

### Provider Specific Endpoints
Base Path: `/api/v1/`

These endpoints are dedicated to service provider actions, including registration, login, and managing their specific profiles which may include service offerings, availability, etc.

---

#### 1. Register a New Provider
- **Endpoint:** `auth/provider/register/`
- **Method:** `POST`
- **Description:** Allows a new user to register as a service provider.
- **Permissions:** Anonymous User

  **Example cURL Request:**
  ```bash
  curl -X POST https://yourdomain.com/api/v1/auth/provider/register/ \
    -H "Content-Type: application/json" \
    -d '{
          "username": "newprovider",
          "email": "provider@example.com",
          "password": "SecurePassword456!",
          "first_name": "Service",
          "last_name": "Provider",
          "phone_number": "+1555123456",
          "profile": {
            "business_name": "Pro Services Inc.",
            "service_category": "Home Cleaning",
            "years_of_experience": 5
          }
        }'
  ```

  **Example JSON Request Body:**
  ```json
  {
    "username": "newprovider",
    "email": "provider@example.com",
    "password": "SecurePassword456!",
    "first_name": "Service",
    "last_name": "Provider",
    "phone_number": "+1555123456",
    "profile": {
      "business_name": "Pro Services Inc.",
      "service_category": "Home Cleaning",
      "years_of_experience": 5
    }
  }
  ```

  **Example JSON Response (Success 201 Created):**
  ```json
  {
    "id": "fedcba98-7654-3210-fedc-ba9876543210",
    "username": "newprovider",
    "email": "provider@example.com",
    "first_name": "Service",
    "last_name": "Provider",
    "phone_number": "+1555123456",
    "profile": {
        "user_type": "provider",
        "business_name": "Pro Services Inc.",
        "service_category": "Home Cleaning",
        "years_of_experience": 5,
        "verified": false
    },
    "message": "Provider registered successfully. Please complete your profile and verification."
  }
  ```

  **Example JSON Response (Error 400 Bad Request - Validation Error):**
  ```json
  {
    "email": ["provider with this email already exists."],
    "profile": {
        "service_category": ["This field may not be blank."]
    }
  }
  ```

---

---

#### 3. Retrieve or Update Current Authenticated Provider's Profile
- **Endpoint:** `users/provider/me/`
- **Method:** `GET`, `PUT`, `PATCH`
- **Description:** Allows an authenticated provider to retrieve or update their own specific provider profile details (e.g., business info, services offered, availability).
- **Permissions:** Authenticated Provider

**GET `users/provider/me/`**
- **Description:** Retrieve the profile of the currently authenticated provider.

  **Example cURL Request:**
  ```bash
  curl -X GET https://yourdomain.com/api/v1/users/provider/me/ \
    -H "Authorization: Bearer <provider_access_token>"
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "fedcba98-7654-3210-fedc-ba9876543210",
    "username": "newprovider",
    "email": "provider@example.com",
    "first_name": "Service",
    "last_name": "Provider",
    "phone_number": "+1555123456",
    "profile": {
      "bio": "Experienced home cleaning professional.",
      "date_of_birth": "1985-03-20",
      "profile_picture_url": "https://yourdomain.com/media/avatars/provider_avatar.jpg",
      "address": "123 Provider Ave, Servicetown, USA",
      "user_type": "provider",
      "business_name": "Pro Services Inc.",
      "service_category": "Home Cleaning",
      "services_offered": ["Deep Cleaning", "Regular Cleaning", "Move-out Cleaning"],
      "availability_schedule": {"monday": "9am-5pm", "tuesday": "9am-5pm"},
      "service_radius_km": 20,
      "years_of_experience": 5,
      "hourly_rate": 50.00,
      "verified": true,
      "verification_documents": [
          {"type": "ID", "status": "approved"},
          {"type": "BusinessLicense", "status": "pending"}
      ]
    }
  }
  ```

**PUT `users/provider/me/`**
- **Description:** Update the entire provider profile. All fields required for update must be provided.

  **Example cURL Request:**
  ```bash
  curl -X PUT https://yourdomain.com/api/v1/users/provider/me/ \
    -H "Authorization: Bearer <provider_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "first_name": "UpdatedService",
          "last_name": "Pro",
          "profile": {
            "business_name": "Updated Pro Services LLC",
            "services_offered": ["Deep Cleaning", "Regular Cleaning", "Eco-Friendly Cleaning"],
            "hourly_rate": 55.00
          }
        }'
  ```

  **Example JSON Request Body:**
  ```json
  {
    "first_name": "UpdatedService",
    "last_name": "Pro",
    "profile": {
      "business_name": "Updated Pro Services LLC",
      "services_offered": ["Deep Cleaning", "Regular Cleaning", "Eco-Friendly Cleaning"],
      "hourly_rate": 55.00
    }
  }
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "fedcba98-7654-3210-fedc-ba9876543210",
    "username": "newprovider",
    "email": "provider@example.com",
    "first_name": "UpdatedService",
    "last_name": "Pro",
    "phone_number": "+1555123456",
    "profile": {
      "bio": "Experienced home cleaning professional.",
      "date_of_birth": "1985-03-20",
      "profile_picture_url": "https://yourdomain.com/media/avatars/provider_avatar.jpg",
      "address": "123 Provider Ave, Servicetown, USA",
      "user_type": "provider",
      "business_name": "Updated Pro Services LLC",
      "service_category": "Home Cleaning",
      "services_offered": ["Deep Cleaning", "Regular Cleaning", "Eco-Friendly Cleaning"],
      "availability_schedule": {"monday": "9am-5pm", "tuesday": "9am-5pm"},
      "service_radius_km": 20,
      "years_of_experience": 5,
      "hourly_rate": 55.00,
      "verified": true,
      "verification_documents": [
          {"type": "ID", "status": "approved"},
          {"type": "BusinessLicense", "status": "pending"}
      ]
    }
  }
  ```

**PATCH `users/provider/me/`**
- **Description:** Partially update the provider profile. Only include fields to be updated.

  **Example cURL Request:**
  ```bash
  curl -X PATCH https://yourdomain.com/api/v1/users/provider/me/ \
    -H "Authorization: Bearer <provider_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "profile": {
            "availability_schedule": {"wednesday": "10am-3pm", "friday": "9am-6pm"}
          }
        }'
  ```

  **Example JSON Request Body:**
  ```json
  {
    "profile": {
      "availability_schedule": {"wednesday": "10am-3pm", "friday": "9am-6pm"}
    }
  }
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "fedcba98-7654-3210-fedc-ba9876543210",
    "username": "newprovider",
    "email": "provider@example.com",
    "first_name": "UpdatedService",
    "last_name": "Pro",
    "phone_number": "+1555123456",
    "profile": {
      "bio": "Experienced home cleaning professional.",
      "date_of_birth": "1985-03-20",
      "profile_picture_url": "https://yourdomain.com/media/avatars/provider_avatar.jpg",
      "address": "123 Provider Ave, Servicetown, USA",
      "user_type": "provider",
      "business_name": "Updated Pro Services LLC",
      "service_category": "Home Cleaning",
      "services_offered": ["Deep Cleaning", "Regular Cleaning", "Eco-Friendly Cleaning"],
      "availability_schedule": {"wednesday": "10am-3pm", "friday": "9am-6pm"},
      "service_radius_km": 20,
      "years_of_experience": 5,
      "hourly_rate": 55.00,
      "verified": true,
      "verification_documents": [
          {"type": "ID", "status": "approved"},
          {"type": "BusinessLicense", "status": "pending"}
      ]
    }
  }
  ```

  **Example Response (Error 403 Forbidden - If a non-provider tries to access):**
  ```json
  {
    "detail": "You do not have permission to perform this action as a provider."
  }
  ```

### Admin Specific Endpoints
Base Path: `/api/v1/`

These endpoints are restricted to users with administrative privileges and are used for site administration, user management, and other high-level operations.

---

#### 1. Register a New Admin
- **Endpoint:** `auth/admin/register/`
- **Method:** `POST`
- **Description:** Allows an existing superuser or an admin with appropriate permissions to register a new administrator account. This endpoint should be heavily protected.
- **Permissions:** Superuser / Admin with specific permissions

  **Example cURL Request:**
  ```bash
  curl -X POST https://yourdomain.com/api/v1/auth/admin/register/ \
    -H "Authorization: Bearer <superuser_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "username": "newadminuser",
          "email": "admin@example.com",
          "password": "VerySecureAdminPass1!",
          "first_name": "Admin",
          "last_name": "User",
          "phone_number": "+1231231234",
          "staff_role": "ContentModerator" 
        }'
  ```

  **Example JSON Request Body:**
  ```json
  {
    "username": "newadminuser",
    "email": "admin@example.com",
    "password": "VerySecureAdminPass1!",
    "first_name": "Admin",
    "last_name": "User",
    "phone_number": "+1231231234",
    "staff_role": "ContentModerator" 
  }
  ```

  **Example JSON Response (Success 201 Created):**
  ```json
  {
    "id": "98765432-10fe-dcba-9876-543210fedcba",
    "username": "newadminuser",
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "User",
    "phone_number": "+1231231234",
    "profile": {
        "user_type": "admin",
        "staff_role": "ContentModerator"
    },
    "message": "Admin user registered successfully."
  }
  ```

  **Example JSON Response (Error 400 Bad Request - Validation Error):**
  ```json
  {
    "username": ["An admin with this username already exists."],
    "password": ["Password is not strong enough."]
  }
  ```

  **Example JSON Response (Error 403 Forbidden - Insufficient Permissions):**
  ```json
  {
    "detail": "You do not have permission to register new admin users."
  }
  ```

---

---

#### 3. Retrieve or Update Current Authenticated Admin's Profile
- **Endpoint:** `users/admin/me/`
- **Method:** `GET`, `PUT`, `PATCH`
- **Description:** Allows an authenticated admin to retrieve or update their own profile details.
- **Permissions:** Authenticated Admin

**GET `users/admin/me/`**
- **Description:** Retrieve the profile of the currently authenticated admin.

  **Example cURL Request:**
  ```bash
  curl -X GET https://yourdomain.com/api/v1/users/admin/me/ \
    -H "Authorization: Bearer <admin_access_token>"
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "98765432-10fe-dcba-9876-543210fedcba",
    "username": "newadminuser",
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "User",
    "phone_number": "+1231231234",
    "profile": {
      "bio": "Site administrator with content moderation responsibilities.",
      "date_of_birth": "1980-06-15",
      "profile_picture_url": "https://yourdomain.com/media/avatars/admin_avatar.jpg",
      "user_type": "admin",
      "staff_role": "ContentModerator",
      "permissions": ["can_manage_users", "can_view_reports", "can_moderate_content"]
    },
    "is_superuser": false,
    "is_staff": true
  }
  ```

**PUT `users/admin/me/`**
- **Description:** Update the entire admin profile. All fields required for update must be provided.

  **Example cURL Request:**
  ```bash
  curl -X PUT https://yourdomain.com/api/v1/users/admin/me/ \
    -H "Authorization: Bearer <admin_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "first_name": "SeniorAdmin",
          "last_name": "User",
          "profile": {
            "staff_role": "UserManager",
            "bio": "Senior administrator with user management and system oversight responsibilities."
          }
        }'
  ```

  **Example JSON Request Body:**
  ```json
  {
    "first_name": "SeniorAdmin",
    "last_name": "User",
    "profile": {
      "staff_role": "UserManager",
      "bio": "Senior administrator with user management and system oversight responsibilities."
    }
  }
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "98765432-10fe-dcba-9876-543210fedcba",
    "username": "newadminuser",
    "email": "admin@example.com",
    "first_name": "SeniorAdmin",
    "last_name": "User",
    "phone_number": "+1231231234",
    "profile": {
      "bio": "Senior administrator with user management and system oversight responsibilities.",
      "date_of_birth": "1980-06-15",
      "profile_picture_url": "https://yourdomain.com/media/avatars/admin_avatar.jpg",
      "user_type": "admin",
      "staff_role": "UserManager",
      "permissions": ["can_manage_users", "can_view_reports", "can_moderate_content"]
    },
    "is_superuser": false,
    "is_staff": true
  }
  ```

**PATCH `users/admin/me/`**
- **Description:** Partially update the admin profile. Only include fields to be updated.

  **Example cURL Request:**
  ```bash
  curl -X PATCH https://yourdomain.com/api/v1/users/admin/me/ \
    -H "Authorization: Bearer <admin_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "profile": {
             "phone_number": "+1231239999"
          }
        }'
  ```

  **Example JSON Request Body:**
  ```json
  {
    "profile": {
       "phone_number": "+1231239999"
    }
  }
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "98765432-10fe-dcba-9876-543210fedcba",
    "username": "newadminuser",
    "email": "admin@example.com",
    "first_name": "SeniorAdmin",
    "last_name": "User",
    "phone_number": "+1231239999",
    "profile": {
      "bio": "Senior administrator with user management and system oversight responsibilities.",
      "date_of_birth": "1980-06-15",
      "profile_picture_url": "https://yourdomain.com/media/avatars/admin_avatar.jpg",
      "user_type": "admin",
      "staff_role": "UserManager",
      "permissions": ["can_manage_users", "can_view_reports", "can_moderate_content"]
    },
    "is_superuser": false,
    "is_staff": true
  }
  ```

  **Example Response (Error 403 Forbidden - If a non-admin tries to access):**
  ```json
  {
    "detail": "You do not have permission to perform this action as an admin."
  }
  ```

### User Search
Base Path: `/api/v1/`

These endpoints allow for searching and discovering users within the Prbal platform.

---

#### 1. General User Search
- **Endpoint:** `users/search/`
- **Method:** `GET`
- **Description:** Search for users based on multiple criteria such as username, email, phone number, first name, last name, or user type. This endpoint is useful for finding users across the platform.
- **Permissions:** Authenticated User (rules might vary based on who is searching for whom)

  **Example cURL Request (Search by username and user_type):**
  ```bash
  curl -X GET "https://yourdomain.com/api/v1/users/search/?username=johndoe&user_type=provider" \
    -H "Authorization: Bearer <access_token>"
  ```

  **Example cURL Request (Search by email):**
  ```bash
  curl -X GET "https://yourdomain.com/api/v1/users/search/?email=john.doe@example.com" \
    -H "Authorization: Bearer <access_token>"
  ```

  **Example cURL Request (Search by part of a name):**
  ```bash
  curl -X GET "https://yourdomain.com/api/v1/users/search/?name=john" \
    -H "Authorization: Bearer <access_token>"
  ```

  **Query Parameters:**
  - `username` (string, optional): Filter by username.
  - `email` (string, optional): Filter by email address.
  - `phone` (string, optional): Filter by phone number.
  - `name` (string, optional): Filter by first name or last name (partial matches supported).
  - `user_type` (string, optional): Filter by user type (e.g., 'customer', 'provider', 'admin').

  **Example JSON Response (Success 200 OK - Users Found):**
  ```json
  {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": "12345678-abcd-efgh-ijkl-mnopqrstuvwx",
        "username": "johndoe_provider",
        "email": "john.doe.provider@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "profile": {
          "user_type": "provider",
          "profile_picture_url": "https://yourdomain.com/media/avatars/provider_johndoe.jpg",
          "bio": "Experienced plumber serving the downtown area."
        }
      }
    ]
  }
  ```

  **Example JSON Response (Success 200 OK - No Users Found):**
  ```json
  {
    "count": 0,
    "next": null,
    "previous": null,
    "results": [],
    "message": "No users found matching your criteria."
  }
  ```

  **Example JSON Response (Error 400 Bad Request - Invalid Parameters):**
  ```json
  {
    "error": "Invalid search parameters provided."
  }
  ```

---

#### 2. Search Users by Phone Number
- **Endpoint:** `users/search/phone/`
- **Method:** `GET`
- **Description:** Specifically search for users by their registered phone number. This is a more targeted search.
- **Permissions:** Authenticated User (potentially with stricter rules, e.g., admin only or for specific verified linking processes)

  **Example cURL Request:**
  ```bash
  curl -X GET "https://yourdomain.com/api/v1/users/search/phone/?phone_number=+15551234567" \
    -H "Authorization: Bearer <access_token>"
  ```

  **Query Parameters:**
  - `phone_number` (string, required): The exact phone number to search for (including country code).

  **Example JSON Response (Success 200 OK - User Found):**
  ```json
  {
    "id": "abcdef12-3456-7890-fedc-ba9876543210",
    "username": "janedoe_customer",
    "email": "jane.doe@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "phone_number": "+15551234567",
    "profile": {
      "user_type": "customer",
      "profile_picture_url": "https://yourdomain.com/media/avatars/customer_janedoe.jpg"
    }
  }
  ```

  **Example JSON Response (Success 404 Not Found - User with phone not found):**
  ```json
  {
    "detail": "User with the specified phone number not found."
  }
  ```

  **Example JSON Response (Error 400 Bad Request - Missing phone_number parameter):**
  ```json
  {
    "phone_number": ["This field is required."]
  }
  ```


### User Verification (General)
Base Path: `/api/v1/`

These endpoints manage the user verification process, which is crucial for building trust and security on the Prbal platform. Users can submit documents and information for various types of verification, and their status can be tracked. Verification types include `identity`, `address`, `professional`, `educational`, `background`, `business`, and `banking`. Statuses can be `unverified`, `pending`, `in_progress`, `verified`, `rejected`, or `expired`.

---

#### 1. Initiate or Update User Verification
- **Endpoint:** `users/verify/`
- **Method:** `POST`
- **Description:** Allows an authenticated user to initiate a new verification process for a specific type or update an existing one by submitting required documents and information. For example, resubmitting documents if a previous attempt was 'rejected'.
- **Permissions:** Authenticated User

  **Example cURL Request (Initiate Identity Verification):**
  ```bash
  curl -X POST https://yourdomain.com/api/v1/users/verify/ \
    -H "Authorization: Bearer <user_access_token>" \
    -H "Content-Type: multipart/form-data" \
    -F "verification_type=identity" \
    -F "document_front=@/path/to/id_front.jpg" \
    -F "document_back=@/path/to/id_back.jpg" \
    -F "additional_info={\"issue_date\": \"2023-01-15\", \"expiry_date\": \"2028-01-14\"}"
  ```

  **Request Body (multipart/form-data):**
  - `verification_type` (string, required): The type of verification. E.g., `identity`, `address`, `professional`, `educational`, `background`, `business`, `banking`.
  - `document_front` (file, optional): Front side of the document.
  - `document_back` (file, optional): Back side of the document.
  - `document_additional_1` (file, optional): Additional supporting document.
  - `document_additional_2` (file, optional): Another additional supporting document.
  - `additional_info` (JSON string, optional): Other relevant information (e.g., license number, institution name).

  **Example JSON for `additional_info` (for 'educational' type):**
  ```json
  {
    "institution_name": "University of Example",
    "degree_name": "Bachelor of Science in Computer Science",
    "graduation_year": "2020"
  }
  ```

  **Example JSON Response (Success 201 Created / 200 OK - Verification Initiated/Updated):**
  ```json
  {
    "id": "verify_abcdef1234567890",
    "user_id": "user_uuid_here",
    "verification_type": "identity",
    "status": "pending",
    "submitted_at": "2024-07-29T10:30:00Z",
    "message": "Identity verification request submitted successfully. Your documents are under review."
  }
  ```

  **Example JSON Response (Error 400 Bad Request - Invalid Type or Missing Fields):**
  ```json
  {
    "verification_type": ["Invalid verification type specified."],
    "document_front": ["This field is required for identity verification."]
  }
  ```

  **Example JSON Response (Error 409 Conflict - Verification Already Verified):**
  ```json
  {
    "detail": "You are already verified for this type (identity) and it's currently in 'verified' status."
  }
  ```

---

#### 2. Check User Verification Status
- **Endpoint:** `users/verify/`
- **Method:** `GET`
- **Description:** Allows an authenticated user to retrieve the status of their verification requests. Can list all or filter by type.
- **Permissions:** Authenticated User

  **Example cURL Request (Get all verification statuses for the user):**
  ```bash
  curl -X GET https://yourdomain.com/api/v1/users/verify/ \
    -H "Authorization: Bearer <user_access_token>"
  ```

  **Example cURL Request (Get status for a specific verification type):**
  ```bash
  curl -X GET "https://yourdomain.com/api/v1/users/verify/?verification_type=identity" \
    -H "Authorization: Bearer <user_access_token>"
  ```

  **Query Parameters:**
  - `verification_type` (string, optional): Filter by type (e.g., `identity`). If omitted, returns all for the user.

  **Example JSON Response (Success 200 OK - List of Verifications):**
  ```json
  {
    "count": 2,
    "results": [
      {
        "id": "verify_abcdef1234567890",
        "user_id": "user_uuid_here",
        "verification_type": "identity",
        "status": "verified",
        "submitted_at": "2024-07-29T10:30:00Z",
        "last_updated_at": "2024-07-30T15:00:00Z",
        "verified_at": "2024-07-30T15:00:00Z",
        "rejection_reason": null,
        "expires_at": "2029-07-30T15:00:00Z"
      },
      {
        "id": "verify_qwerty0987654321",
        "user_id": "user_uuid_here",
        "verification_type": "address",
        "status": "pending",
        "submitted_at": "2024-08-01T11:00:00Z",
        "last_updated_at": "2024-08-01T11:00:00Z",
        "verified_at": null,
        "rejection_reason": null,
        "expires_at": null
      }
    ]
  }
  ```

  **Example JSON Response (Success 200 OK - Specific Verification Type Found):**
  ```json
  {
    "id": "verify_abcdef1234567890",
    "user_id": "user_uuid_here",
    "verification_type": "identity",
    "status": "verified",
    "submitted_at": "2024-07-29T10:30:00Z",
    "last_updated_at": "2024-07-30T15:00:00Z",
    "verified_at": "2024-07-30T15:00:00Z",
    "rejection_reason": null,
    "expires_at": "2029-07-30T15:00:00Z",
    "documents": [
        {"document_type_key": "document_front", "url": "https://yourdomain.com/media/verifications/user_uuid/id_front_secure.jpg", "uploaded_at": "2024-07-29T10:29:00Z"},
        {"document_type_key": "document_back", "url": "https://yourdomain.com/media/verifications/user_uuid/id_back_secure.jpg", "uploaded_at": "2024-07-29T10:29:30Z"}
    ],
    "additional_info": {"issue_date": "2023-01-15", "expiry_date": "2028-01-14"}
  }
  ```

  **Example JSON Response (Success 404 Not Found - Specific Verification Type Not Found for User):**
  ```json
  {
    "detail": "No 'professional' verification record found for this user."
  }
  ```

---

## Services & Service Requests
Base Path: `/api/v1/` (via `api.urls` router, typically mounted at `/api/`)
### 1. Manage Service Categories
- **Endpoint:** `services/categories/`
- **Description:** Allows for the management of service categories. Categories help organize services offered on the platform.
- **Model Fields (example):** `id`, `name` (string, required), `slug` (string, unique, auto-generated or provided), `description` (text, optional), `icon_url` (URL, optional), `parent_category` (FK, optional for sub-categories), `is_active` (boolean, default: true).

---

#### 1.1. List Service Categories
- **Method:** `GET`
- **Endpoint:** `services/categories/`
- **Description:** Retrieves a list of all available service categories. Supports pagination.
- **Permissions:** Authenticated User

  **Example cURL Request:**
  ```bash
  curl -X GET https://yourdomain.com/api/v1/services/categories/ \
    -H "Authorization: Bearer <access_token>"
  ```

  **Query Parameters (Optional):**
  - `page` (integer): Page number for pagination.
  - `page_size` (integer): Number of items per page.
  - `is_active` (boolean): Filter by active status.
  - `search` (string): Search term for category name or description.

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "count": 25,
    "next": "https://yourdomain.com/api/v1/services/categories/?page=2",
    "previous": null,
    "results": [
      {
        "id": "cat_01H7XZ8V5N7QJWBJ0G8X2E5Y3P",
        "name": "Home Cleaning",
        "slug": "home-cleaning",
        "description": "Professional cleaning services for residential properties.",
        "icon_url": "https://yourdomain.com/icons/home_cleaning.png",
        "parent_category": null,
        "is_active": true
      },
      {
        "id": "cat_01H7XZ9B3K8RFWJ0P4S1N3M6Z7",
        "name": "Plumbing",
        "slug": "plumbing",
        "description": "All types of plumbing repairs and installations.",
        "icon_url": "https://yourdomain.com/icons/plumbing.png",
        "parent_category": null,
        "is_active": true
      }
      // ... more categories
    ]
  }
  ```

---

#### 1.2. Create a New Service Category
- **Method:** `POST`
- **Endpoint:** `services/categories/`
- **Description:** Creates a new service category. Typically restricted to admin users.
- **Permissions:** Admin User

  **Example cURL Request:**
  ```bash
  curl -X POST https://yourdomain.com/api/v1/services/categories/ \
    -H "Authorization: Bearer <admin_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "name": "Gardening Services",
          "description": "Lawn care, garden design, and maintenance.",
          "icon_url": "https://yourdomain.com/icons/gardening.png",
          "parent_category_id": null,
          "is_active": true
        }'
  ```

  **Example JSON Request Body:**
  ```json
  {
    "name": "Gardening Services",
    "description": "Lawn care, garden design, and maintenance.",
    "icon_url": "https://yourdomain.com/icons/gardening.png",
    "parent_category_id": null, // or "cat_..." if it's a subcategory
    "is_active": true
  }
  ```

  **Example JSON Response (Success 201 Created):**
  ```json
  {
    "id": "cat_01H7Y0A5M3P2N1Q8R7S6T5V4W9",
    "name": "Gardening Services",
    "slug": "gardening-services",
    "description": "Lawn care, garden design, and maintenance.",
    "icon_url": "https://yourdomain.com/icons/gardening.png",
    "parent_category": null,
    "is_active": true
  }
  ```

  **Example JSON Response (Error 400 Bad Request - Validation Error):**
  ```json
  {
    "name": ["This field is required."],
    "slug": ["Service category with this slug already exists."]
  }
  ```

---

#### 1.3. Retrieve a Specific Service Category
- **Method:** `GET`
- **Endpoint:** `services/categories/{category_id_or_slug}/`
- **Description:** Retrieves details of a specific service category by its ID or slug.
- **Permissions:** Authenticated User

  **Example cURL Request (by ID):**
  ```bash
  curl -X GET https://yourdomain.com/api/v1/services/categories/cat_01H7XZ8V5N7QJWBJ0G8X2E5Y3P/ \
    -H "Authorization: Bearer <access_token>"
  ```

  **Example cURL Request (by Slug):**
  ```bash
  curl -X GET https://yourdomain.com/api/v1/services/categories/home-cleaning/ \
    -H "Authorization: Bearer <access_token>"
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "cat_01H7XZ8V5N7QJWBJ0G8X2E5Y3P",
    "name": "Home Cleaning",
    "slug": "home-cleaning",
    "description": "Professional cleaning services for residential properties.",
    "icon_url": "https://yourdomain.com/icons/home_cleaning.png",
    "parent_category": null,
    "is_active": true,
    "sub_categories": [ // Example if subcategories are nested or linked
        {
            "id": "subcat_01H8...",
            "name": "Deep Cleaning",
            "slug": "deep-cleaning"
        }
    ]
  }
  ```

  **Example JSON Response (Error 404 Not Found):**
  ```json
  {
    "detail": "Not found."
  }
  ```

---

#### 1.4. Update a Service Category
- **Method:** `PUT` or `PATCH`
- **Endpoint:** `services/categories/{category_id_or_slug}/`
- **Description:** Updates an existing service category. `PUT` requires all fields, `PATCH` allows partial updates. Typically restricted to admin users.
- **Permissions:** Admin User

  **Example cURL Request (PATCH):**
  ```bash
  curl -X PATCH https://yourdomain.com/api/v1/services/categories/cat_01H7Y0A5M3P2N1Q8R7S6T5V4W9/ \
    -H "Authorization: Bearer <admin_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "description": "Comprehensive lawn care, advanced garden design, and regular maintenance services.",
          "is_active": false
        }'
  ```

  **Example JSON Request Body (PATCH):**
  ```json
  {
    "description": "Comprehensive lawn care, advanced garden design, and regular maintenance services.",
    "is_active": false
  }
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "cat_01H7Y0A5M3P2N1Q8R7S6T5V4W9",
    "name": "Gardening Services",
    "slug": "gardening-services",
    "description": "Comprehensive lawn care, advanced garden design, and regular maintenance services.",
    "icon_url": "https://yourdomain.com/icons/gardening.png",
    "parent_category": null,
    "is_active": false
  }
  ```

---

#### 1.5. Delete a Service Category
- **Method:** `DELETE`
- **Endpoint:** `services/categories/{category_id_or_slug}/`
- **Description:** Deletes a service category. Typically restricted to admin users. Consider implications (e.g., soft delete, disassociation from services).
- **Permissions:** Admin User

  **Example cURL Request:**
  ```bash
  curl -X DELETE https://yourdomain.com/api/v1/services/categories/cat_01H7Y0A5M3P2N1Q8R7S6T5V4W9/ \
    -H "Authorization: Bearer <admin_access_token>"
  ```

  **Example JSON Response (Success 204 No Content):**
  (No body content is returned on successful deletion)

  **Example JSON Response (Error 404 Not Found):**
  ```json
  {
    "detail": "Not found."
  }
  ```

  **Example JSON Response (Error 409 Conflict - Category in use):**
  ```json
  {
    "detail": "Cannot delete category. It is currently associated with active services or subcategories."
  }
  ```

---

### 2. Manage Service Subcategories
- **Endpoint:** `services/subcategories/`
- **Description:** Allows for the management of service subcategories. Subcategories provide a more granular classification under main service categories.
- **Model Fields (example):** `id`, `name` (string, required), `slug` (string, unique), `description` (text, optional), `parent_category` (FK to ServiceCategory, required), `icon_url` (URL, optional), `is_active` (boolean, default: true).

---

#### 2.1. List Service Subcategories
- **Method:** `GET`
- **Endpoint:** `services/subcategories/`
- **Description:** Retrieves a list of all available service subcategories. Can be filtered by parent category.
- **Permissions:** Authenticated User

  **Example cURL Request (List all subcategories):**
  ```bash
  curl -X GET https://yourdomain.com/api/v1/services/subcategories/ \
    -H "Authorization: Bearer <access_token>"
  ```

  **Example cURL Request (List subcategories for a specific parent category):**
  ```bash
  curl -X GET "https://yourdomain.com/api/v1/services/subcategories/?parent_category_id=cat_01H7XZ8V5N7QJWBJ0G8X2E5Y3P" \
    -H "Authorization: Bearer <access_token>"
  ```

  **Query Parameters (Optional):**
  - `page` (integer): Page number for pagination.
  - `page_size` (integer): Number of items per page.
  - `parent_category_id` (string): Filter by the ID of the parent service category.
  - `parent_category_slug` (string): Filter by the slug of the parent service category.
  - `is_active` (boolean): Filter by active status.
  - `search` (string): Search term for subcategory name or description.

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "count": 15,
    "next": "https://yourdomain.com/api/v1/services/subcategories/?page=2",
    "previous": null,
    "results": [
      {
        "id": "subcat_01H8Y2P5J7K3M4N1Q9R8S7T6V",
        "name": "Deep Cleaning",
        "slug": "deep-cleaning",
        "description": "Intensive cleaning for homes and apartments.",
        "parent_category": {
          "id": "cat_01H7XZ8V5N7QJWBJ0G8X2E5Y3P",
          "name": "Home Cleaning",
          "slug": "home-cleaning"
        },
        "icon_url": "https://yourdomain.com/icons/deep_cleaning.png",
        "is_active": true
      },
      {
        "id": "subcat_01H8Y2Q9A8B7C6D5E4F3G2H1J",
        "name": "Faucet Repair",
        "slug": "faucet-repair",
        "description": "Repair and replacement of leaky or broken faucets.",
        "parent_category": {
          "id": "cat_01H7XZ9B3K8RFWJ0P4S1N3M6Z7",
          "name": "Plumbing",
          "slug": "plumbing"
        },
        "icon_url": "https://yourdomain.com/icons/faucet_repair.png",
        "is_active": true
      }
      // ... more subcategories
    ]
  }
  ```

---

#### 2.2. Create a New Service Subcategory
- **Method:** `POST`
- **Endpoint:** `services/subcategories/`
- **Description:** Creates a new service subcategory under a specified parent category. Typically restricted to admin users.
- **Permissions:** Admin User

  **Example cURL Request:**
  ```bash
  curl -X POST https://yourdomain.com/api/v1/services/subcategories/ \
    -H "Authorization: Bearer <admin_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "name": "Window Cleaning",
          "description": "Interior and exterior window cleaning services.",
          "parent_category_id": "cat_01H7XZ8V5N7QJWBJ0G8X2E5Y3P",
          "icon_url": "https://yourdomain.com/icons/window_cleaning.png",
          "is_active": true
        }'
  ```

  **Example JSON Request Body:**
  ```json
  {
    "name": "Window Cleaning",
    "description": "Interior and exterior window cleaning services.",
    "parent_category_id": "cat_01H7XZ8V5N7QJWBJ0G8X2E5Y3P", // ID of "Home Cleaning"
    "icon_url": "https://yourdomain.com/icons/window_cleaning.png",
    "is_active": true
  }
  ```

  **Example JSON Response (Success 201 Created):**
  ```json
  {
    "id": "subcat_01H8Y3R7S6T5V4W9X2Y1Z0A3B",
    "name": "Window Cleaning",
    "slug": "window-cleaning",
    "description": "Interior and exterior window cleaning services.",
    "parent_category": {
      "id": "cat_01H7XZ8V5N7QJWBJ0G8X2E5Y3P",
      "name": "Home Cleaning",
      "slug": "home-cleaning"
    },
    "icon_url": "https://yourdomain.com/icons/window_cleaning.png",
    "is_active": true
  }
  ```

  **Example JSON Response (Error 400 Bad Request - Validation Error):**
  ```json
  {
    "name": ["This field is required."],
    "parent_category_id": ["This field is required.", "Invalid parent category ID."]
  }
  ```

---

#### 2.3. Retrieve a Specific Service Subcategory
- **Method:** `GET`
- **Endpoint:** `services/subcategories/{subcategory_id_or_slug}/`
- **Description:** Retrieves details of a specific service subcategory by its ID or slug.
- **Permissions:** Authenticated User

  **Example cURL Request (by ID):**
  ```bash
  curl -X GET https://yourdomain.com/api/v1/services/subcategories/subcat_01H8Y2P5J7K3M4N1Q9R8S7T6V/ \
    -H "Authorization: Bearer <access_token>"
  ```

  **Example cURL Request (by Slug):**
  ```bash
  curl -X GET https://yourdomain.com/api/v1/services/subcategories/deep-cleaning/ \
    -H "Authorization: Bearer <access_token>"
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "subcat_01H8Y2P5J7K3M4N1Q9R8S7T6V",
    "name": "Deep Cleaning",
    "slug": "deep-cleaning",
    "description": "Intensive cleaning for homes and apartments.",
    "parent_category": {
      "id": "cat_01H7XZ8V5N7QJWBJ0G8X2E5Y3P",
      "name": "Home Cleaning",
      "slug": "home-cleaning"
    },
    "icon_url": "https://yourdomain.com/icons/deep_cleaning.png",
    "is_active": true
  }
  ```

  **Example JSON Response (Error 404 Not Found):**
  ```json
  {
    "detail": "Not found."
  }
  ```

---

#### 2.4. Update a Service Subcategory
- **Method:** `PUT` or `PATCH`
- **Endpoint:** `services/subcategories/{subcategory_id_or_slug}/`
- **Description:** Updates an existing service subcategory. `PUT` requires all fields, `PATCH` allows partial updates. Typically restricted to admin users.
- **Permissions:** Admin User

  **Example cURL Request (PATCH):**
  ```bash
  curl -X PATCH https://yourdomain.com/api/v1/services/subcategories/subcat_01H8Y3R7S6T5V4W9X2Y1Z0A3B/ \
    -H "Authorization: Bearer <admin_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "description": "Premium interior and exterior window cleaning for residential and commercial properties.",
          "is_active": false
        }'
  ```

  **Example JSON Request Body (PATCH):**
  ```json
  {
    "description": "Premium interior and exterior window cleaning for residential and commercial properties.",
    "is_active": false
  }
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "subcat_01H8Y3R7S6T5V4W9X2Y1Z0A3B",
    "name": "Window Cleaning",
    "slug": "window-cleaning",
    "description": "Premium interior and exterior window cleaning for residential and commercial properties.",
    "parent_category": {
      "id": "cat_01H7XZ8V5N7QJWBJ0G8X2E5Y3P",
      "name": "Home Cleaning",
      "slug": "home-cleaning"
    },
    "icon_url": "https://yourdomain.com/icons/window_cleaning.png",
    "is_active": false
  }
  ```

---

#### 2.5. Delete a Service Subcategory
- **Method:** `DELETE`
- **Endpoint:** `services/subcategories/{subcategory_id_or_slug}/`
- **Description:** Deletes a service subcategory. Typically restricted to admin users. Consider implications (e.g., soft delete, disassociation from services).
- **Permissions:** Admin User

  **Example cURL Request:**
  ```bash
  curl -X DELETE https://yourdomain.com/api/v1/services/subcategories/subcat_01H8Y3R7S6T5V4W9X2Y1Z0A3B/ \
    -H "Authorization: Bearer <admin_access_token>"
  ```

  **Example JSON Response (Success 204 No Content):**
  (No body content is returned on successful deletion)

  **Example JSON Response (Error 404 Not Found):**
  ```json
  {
    "detail": "Not found."
  }
  ```

  **Example JSON Response (Error 409 Conflict - Subcategory in use):**
  ```json
  {
    "detail": "Cannot delete subcategory. It is currently associated with active services."
  }
  ```

---

### 3. Manage Services
- **Endpoint:** `services/`
- **Description:** Allows for the management of specific services offered by providers. Services are linked to a subcategory and a provider.
- **Model Fields (example):** `id`, `title` (string, required), `description` (text, required), `subcategory` (FK to ServiceSubcategory, required), `provider` (FK to User, required, typically the authenticated provider), `base_price` (decimal, optional), `pricing_model` (choices: fixed, hourly, per_unit, negotiable, default: fixed), `unit_name` (string, optional, e.g., "hour", "sq ft"), `service_area_radius_km` (integer, optional), `location_latitude` (decimal, optional), `location_longitude` (decimal, optional), `availability_schedule` (JSON, optional), `images` (JSON array of URLs, optional), `videos` (JSON array of URLs, optional), `is_active` (boolean, default: true), `is_verified` (boolean, default: false, admin/system verified), `average_rating` (float, read-only), `total_bookings` (integer, read-only).

---

#### 3.1. List Services
- **Method:** `GET`
- **Endpoint:** `services/`
- **Description:** Retrieves a list of all available services. Can be filtered by various criteria like subcategory, provider, location, price range, etc.
- **Permissions:** Authenticated User (for general listing), Provider (to list their own services with more detail/options)

  **Example cURL Request (List all active services):**
  ```bash
  curl -X GET https://yourdomain.com/api/v1/services/?is_active=true \
    -H "Authorization: Bearer <access_token>"
  ```

  **Example cURL Request (List services by subcategory slug):**
  ```bash
  curl -X GET "https://yourdomain.com/api/v1/services/?subcategory_slug=deep-cleaning" \
    -H "Authorization: Bearer <access_token>"
  ```

  **Example cURL Request (List services by a specific provider ID):**
  ```bash
  curl -X GET "https://yourdomain.com/api/v1/services/?provider_id=user_01H7XW5R9P6YJ2N3K8M4Z7B1Q0" \
    -H "Authorization: Bearer <access_token>"
  ```

  **Query Parameters (Optional - examples):**
  - `page` (integer): Page number for pagination.
  - `page_size` (integer): Number of items per page.
  - `subcategory_id` (string): Filter by subcategory ID.
  - `subcategory_slug` (string): Filter by subcategory slug.
  - `provider_id` (string): Filter by provider's user ID.
  - `provider_username` (string): Filter by provider's username.
  - `is_active` (boolean): Filter by active status.
  - `is_verified` (boolean): Filter by verification status.
  - `min_price` (decimal): Filter by minimum base price.
  - `max_price` (decimal): Filter by maximum base price.
  - `pricing_model` (string): Filter by pricing model (e.g., "hourly", "fixed").
  - `search` (string): Search term for service title or description.
  - `location` (string, e.g., "latitude,longitude"): Search for services near a specific location.
  - `radius_km` (integer): Radius in kilometers for location-based search (used with `location`).
  - `ordering` (string): Field to order by (e.g., `base_price`, `-average_rating`).

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "count": 50,
    "next": "https://yourdomain.com/api/v1/services/?page=2",
    "previous": null,
    "results": [
      {
        "id": "svc_01H8Z5K9P7Q2R3S4T1V6W8X0Y",
        "title": "Residential Deep Cleaning Service",
        "description": "Comprehensive deep cleaning for your home, including kitchens, bathrooms, and living areas.",
        "subcategory": {
          "id": "subcat_01H8Y2P5J7K3M4N1Q9R8S7T6V",
          "name": "Deep Cleaning",
          "slug": "deep-cleaning"
        },
        "provider": {
          "id": "user_01H7XW5R9P6YJ2N3K8M4Z7B1Q0",
          "username": "cleanproservices",
          "average_rating": 4.8
        },
        "base_price": "150.00",
        "pricing_model": "fixed",
        "images": ["https://yourdomain.com/images/deep_clean_1.jpg"],
        "is_active": true,
        "is_verified": true,
        "average_rating": 4.7,
        "total_bookings": 25
      },
      {
        "id": "svc_01H8Z5M2N0P1Q9R8S7T6V5W4X",
        "title": "Leaky Faucet & Pipe Repair",
        "description": "Quick and reliable repair for all types of plumbing leaks.",
        "subcategory": {
          "id": "subcat_01H8Y2Q9A8B7C6D5E4F3G2H1J",
          "name": "Faucet Repair",
          "slug": "faucet-repair"
        },
        "provider": {
          "id": "user_01H7XW6F3G9H1J2K5L4M0N7P8Q",
          "username": "plumbperfect",
          "average_rating": 4.9
        },
        "base_price": "75.00",
        "pricing_model": "hourly",
        "unit_name": "hour",
        "is_active": true,
        "is_verified": true,
        "average_rating": 4.9,
        "total_bookings": 62
      }
      // ... more services
    ]
  }
  ```

---

#### 3.2. Create a New Service
- **Method:** `POST`
- **Endpoint:** `services/`
- **Description:** Allows a provider to create a new service they offer. The authenticated user is typically set as the provider.
- **Permissions:** Provider User

  **Example cURL Request:**
  ```bash
  curl -X POST https://yourdomain.com/api/v1/services/ \
    -H "Authorization: Bearer <provider_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "title": "Custom Web Development",
          "description": "Building responsive and modern websites tailored to your business needs.",
          "subcategory_id": "subcat_01H8Z6X0Y1Z2A3B4C5D6E7F8G",
          "base_price": "2500.00",
          "pricing_model": "fixed",
          "service_area_radius_km": 100,
          "availability_schedule": {"monday": "09:00-17:00", "tuesday": "09:00-17:00"},
          "images": ["https://yourdomain.com/images/webdev_portfolio1.jpg"],
          "is_active": true
        }'
  ```

  **Example JSON Request Body:**
  ```json
  {
    "title": "Custom Web Development",
    "description": "Building responsive and modern websites tailored to your business needs.",
    "subcategory_id": "subcat_01H8Z6X0Y1Z2A3B4C5D6E7F8G", // ID for "Web Development" subcategory
    "base_price": "2500.00",
    "pricing_model": "fixed", // "fixed", "hourly", "per_unit", "negotiable"
    "unit_name": null, // e.g., "project", "hour", "page" if pricing_model is per_unit
    "service_area_radius_km": 100, // Optional
    "location_latitude": 34.0522, // Optional
    "location_longitude": -118.2437, // Optional
    "availability_schedule": { // Optional
        "monday": "09:00-17:00", 
        "tuesday": "09:00-17:00",
        "saturday": "10:00-14:00" 
    },
    "images": ["https://yourdomain.com/images/webdev_portfolio1.jpg"], // Optional
    "videos": [], // Optional
    "is_active": true
  }
  ```

  **Example JSON Response (Success 201 Created):**
  ```json
  {
    "id": "svc_01H8Z7A1B2C3D4E5F6G7H8J9K",
    "title": "Custom Web Development",
    "description": "Building responsive and modern websites tailored to your business needs.",
    "subcategory": {
      "id": "subcat_01H8Z6X0Y1Z2A3B4C5D6E7F8G",
      "name": "Web Development",
      "slug": "web-development"
    },
    "provider": {
      "id": "user_01H7XW5R9P6YJ2N3K8M4Z7B1Q0", // Authenticated provider's ID
      "username": "devsolutions",
      "average_rating": 0 // New service, no ratings yet
    },
    "base_price": "2500.00",
    "pricing_model": "fixed",
    "unit_name": null,
    "service_area_radius_km": 100,
    "location_latitude": 34.0522,
    "location_longitude": -118.2437,
    "availability_schedule": {"monday": "09:00-17:00", "tuesday": "09:00-17:00", "saturday": "10:00-14:00"},
    "images": ["https://yourdomain.com/images/webdev_portfolio1.jpg"],
    "videos": [],
    "is_active": true,
    "is_verified": false,
    "average_rating": 0.0,
    "total_bookings": 0
  }
  ```

  **Example JSON Response (Error 400 Bad Request - Validation Error):**
  ```json
  {
    "title": ["This field is required."],
    "subcategory_id": ["Invalid subcategory ID or subcategory does not exist."],
    "base_price": ["A valid number is required."]
  }
  ```

---

#### 3.3. Retrieve a Specific Service
- **Method:** `GET`
- **Endpoint:** `services/{service_id_or_slug}/`
- **Description:** Retrieves details of a specific service by its ID or a unique slug (if implemented for services).
- **Permissions:** Authenticated User

  **Example cURL Request (by ID):**
  ```bash
  curl -X GET https://yourdomain.com/api/v1/services/svc_01H8Z5K9P7Q2R3S4T1V6W8X0Y/ \
    -H "Authorization: Bearer <access_token>"
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "svc_01H8Z5K9P7Q2R3S4T1V6W8X0Y",
    "title": "Residential Deep Cleaning Service",
    "description": "Comprehensive deep cleaning for your home, including kitchens, bathrooms, and living areas.",
    "subcategory": {
      "id": "subcat_01H8Y2P5J7K3M4N1Q9R8S7T6V",
      "name": "Deep Cleaning",
      "slug": "deep-cleaning"
    },
    "provider": {
      "id": "user_01H7XW5R9P6YJ2N3K8M4Z7B1Q0",
      "username": "cleanproservices",
      "average_rating": 4.8,
      "profile_image_url": "https://yourdomain.com/profiles/cleanpro.jpg",
      "member_since": "2023-01-15T10:00:00Z"
    },
    "base_price": "150.00",
    "pricing_model": "fixed",
    "unit_name": null,
    "service_area_radius_km": 50,
    "location_latitude": null,
    "location_longitude": null,
    "availability_schedule": {
        "monday": "08:00-18:00", 
        "wednesday": "08:00-18:00",
        "friday": "08:00-18:00"
    },
    "images": ["https://yourdomain.com/images/deep_clean_1.jpg", "https://yourdomain.com/images/deep_clean_2.jpg"],
    "videos": [],
    "is_active": true,
    "is_verified": true,
    "average_rating": 4.7,
    "total_bookings": 25,
    "reviews_preview": [ // Optional: a few recent reviews
        {"rating": 5, "comment": "Amazing job!", "user": "customer123"},
        {"rating": 4, "comment": "Very thorough.", "user": "happyclient"}
    ]
  }
  ```

  **Example JSON Response (Error 404 Not Found):**
  ```json
  {
    "detail": "Not found."
  }
  ```

---

#### 3.4. Update a Service
- **Method:** `PUT` or `PATCH`
- **Endpoint:** `services/{service_id_or_slug}/`
- **Description:** Updates an existing service. Only the provider who owns the service or an admin can update it. `PUT` requires all modifiable fields, `PATCH` allows partial updates.
- **Permissions:** Provider User (own service) / Admin User

  **Example cURL Request (PATCH by owner):**
  ```bash
  curl -X PATCH https://yourdomain.com/api/v1/services/svc_01H8Z7A1B2C3D4E5F6G7H8J9K/ \
    -H "Authorization: Bearer <provider_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "base_price": "2750.00",
          "description": "Building responsive and modern websites and web applications tailored to your business needs. Includes basic SEO setup.",
          "is_active": true 
        }'
  ```

  **Example JSON Request Body (PATCH):**
  ```json
  {
    "base_price": "2750.00",
    "description": "Building responsive and modern websites and web applications tailored to your business needs. Includes basic SEO setup.",
    "is_active": true 
  }
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "svc_01H8Z7A1B2C3D4E5F6G7H8J9K",
    "title": "Custom Web Development",
    "description": "Building responsive and modern websites and web applications tailored to your business needs. Includes basic SEO setup.",
    "subcategory": {
      "id": "subcat_01H8Z6X0Y1Z2A3B4C5D6E7F8G",
      "name": "Web Development",
      "slug": "web-development"
    },
    "provider": {
      "id": "user_01H7XW5R9P6YJ2N3K8M4Z7B1Q0",
      "username": "devsolutions",
      "average_rating": 0 
    },
    "base_price": "2750.00",
    "pricing_model": "fixed",
    "is_active": true,
    // ... other fields remain or are updated
  }
  ```

  **Example JSON Response (Error 403 Forbidden - Not owner or admin):**
  ```json
  {
    "detail": "You do not have permission to perform this action."
  }
  ```

---

#### 3.5. Delete a Service
- **Method:** `DELETE`
- **Endpoint:** `services/{service_id_or_slug}/`
- **Description:** Deletes a service. Only the provider who owns the service or an admin can delete it. Consider implications (e.g., soft delete, impact on active bookings).
- **Permissions:** Provider User (own service) / Admin User

  **Example cURL Request (by owner):**
  ```bash
  curl -X DELETE https://yourdomain.com/api/v1/services/svc_01H8Z7A1B2C3D4E5F6G7H8J9K/ \
    -H "Authorization: Bearer <provider_access_token>"
  ```

  **Example JSON Response (Success 204 No Content):**
  (No body content is returned on successful deletion)

  **Example JSON Response (Error 404 Not Found):**
  ```json
  {
    "detail": "Not found."
  }
  ```

  **Example JSON Response (Error 409 Conflict - Service has active bookings):**
  ```json
  {
    "detail": "Cannot delete service. It has active bookings or requests."
  }
  ```

---

### 4. Manage Service Requests
- **Endpoint:** `service-requests/`
- **Description:** Manages requests made by customers for services. This includes creating requests, and tracking their status through to completion or cancellation.
- **Model Fields (example):** `id`, `service` (FK to Service, required), `customer` (FK to User, required, authenticated customer), `provider` (FK to User, derived from Service), `requested_datetime` (datetime, auto_now_add), `preferred_datetime_start` (datetime, required), `preferred_datetime_end` (datetime, optional), `status` (string, choices: pending_provider_acceptance, provider_accepted, provider_rejected, customer_cancelled, provider_cancelled, in_progress, completed, requires_reschedule, default: pending_provider_acceptance), `customer_notes` (text, optional), `provider_notes` (text, optional, by provider), `quoted_price` (decimal, optional, if different from service base price, set by provider), `agreed_price` (decimal, optional, after negotiation), `cancellation_reason` (text, optional), `reschedule_reason` (text, optional).

---

#### 4.1. List Service Requests
- **Method:** `GET`
- **Endpoint:** `service-requests/`
- **Description:** Retrieves a list of service requests. Behavior varies based on user role:
    - **Customer:** Sees their own requests.
    - **Provider:** Sees requests for their services.
    - **Admin:** Sees all requests, with advanced filtering.
- **Permissions:** Authenticated User (Customer, Provider, Admin)

  **Example cURL Request (Customer listing their requests):**
  ```bash
  curl -X GET "https://yourdomain.com/api/v1/service-requests/?customer_id=me" \
    -H "Authorization: Bearer <customer_access_token>"
  ```

  **Example cURL Request (Provider listing requests for their services):**
  ```bash
  curl -X GET "https://yourdomain.com/api/v1/service-requests/?provider_id=me&status=pending_provider_acceptance" \
    -H "Authorization: Bearer <provider_access_token>"
  ```

  **Example cURL Request (Admin listing all 'in_progress' requests):**
  ```bash
  curl -X GET "https://yourdomain.com/api/v1/service-requests/?status=in_progress" \
    -H "Authorization: Bearer <admin_access_token>"
  ```

  **Query Parameters (Examples, vary by role):**
  - `page`, `page_size` (integer): For pagination.
  - `customer_id` (string): Filter by customer ID (use "me" for current customer).
  - `provider_id` (string): Filter by provider ID (use "me" for current provider).
  - `service_id` (string): Filter by service ID.
  - `status` (string): Filter by request status (e.g., `pending_provider_acceptance`, `completed`).
  - `date_from`, `date_to` (date string YYYY-MM-DD): Filter by `preferred_datetime_start`.
  - `ordering` (string): Field to order by (e.g., `preferred_datetime_start`, `-requested_datetime`).

  **Example JSON Response (Success 200 OK - Customer's view):**
  ```json
  {
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": "sreq_01H9A2B3C4D5E6F7G8H9J0K1L",
        "service": {
          "id": "svc_01H8Z5K9P7Q2R3S4T1V6W8X0Y",
          "title": "Residential Deep Cleaning Service",
          "provider_username": "cleanproservices"
        },
        "customer": {
          "id": "user_01H7XV8S5N2QJWBJ0G8X2E5Y3P",
          "username": "customer_jane"
        },
        "provider": {
            "id": "user_01H7XW5R9P6YJ2N3K8M4Z7B1Q0",
            "username": "cleanproservices"
        },
        "requested_datetime": "2024-03-10T10:00:00Z",
        "preferred_datetime_start": "2024-03-15T09:00:00Z",
        "preferred_datetime_end": "2024-03-15T12:00:00Z",
        "status": "provider_accepted",
        "customer_notes": "Please focus on kitchen and bathrooms.",
        "agreed_price": "150.00"
      }
      // ... more requests
    ]
  }
  ```

---

#### 4.2. Create a New Service Request
- **Method:** `POST`
- **Endpoint:** `service-requests/`
- **Description:** Allows a customer to request a specific service.
- **Permissions:** Customer User

  **Example cURL Request:**
  ```bash
  curl -X POST https://yourdomain.com/api/v1/service-requests/ \
    -H "Authorization: Bearer <customer_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "service_id": "svc_01H8Z5K9P7Q2R3S4T1V6W8X0Y",
          "preferred_datetime_start": "2024-03-20T14:00:00Z",
          "preferred_datetime_end": "2024-03-20T17:00:00Z",
          "customer_notes": "Need help with assembling new furniture. Have all tools ready."
        }'
  ```

  **Example JSON Request Body:**
  ```json
  {
    "service_id": "svc_01H8Z5K9P7Q2R3S4T1V6W8X0Y", // ID of the service being requested
    "preferred_datetime_start": "2024-03-20T14:00:00Z", // ISO 8601 format
    "preferred_datetime_end": "2024-03-20T17:00:00Z",   // ISO 8601 format, optional
    "customer_notes": "Need help with assembling new furniture. Have all tools ready." // Optional
  }
  ```

  **Example JSON Response (Success 201 Created):**
  ```json
  {
    "id": "sreq_01H9A3C5D6E7F8G9H0J1K2L3M",
    "service": {
      "id": "svc_01H8Z5K9P7Q2R3S4T1V6W8X0Y",
      "title": "Residential Deep Cleaning Service"
    },
    "customer": {
      "id": "user_01H7XV8S5N2QJWBJ0G8X2E5Y3P", // Authenticated customer's ID
      "username": "customer_jane"
    },
    "provider": { // Provider details derived from the service
        "id": "user_01H7XW5R9P6YJ2N3K8M4Z7B1Q0",
        "username": "cleanproservices"
    },
    "requested_datetime": "2024-03-10T11:30:00Z",
    "preferred_datetime_start": "2024-03-20T14:00:00Z",
    "preferred_datetime_end": "2024-03-20T17:00:00Z",
    "status": "pending_provider_acceptance",
    "customer_notes": "Need help with assembling new furniture. Have all tools ready.",
    "provider_notes": null,
    "quoted_price": null, // Initially null, can be set by provider if service price is variable
    "agreed_price": "150.00" // Can be service's base_price or quoted_price upon acceptance
  }
  ```

  **Example JSON Response (Error 400 Bad Request - Validation Error):**
  ```json
  {
    "service_id": ["This field is required."],
    "preferred_datetime_start": ["Datetime has to be in the future."],
    "availability": ["Provider is not available at the requested time."]
  }
  ```

---

#### 4.3. Retrieve a Specific Service Request
- **Method:** `GET`
- **Endpoint:** `service-requests/{request_id}/`
- **Description:** Retrieves details of a specific service request. Accessible by the customer who made it, the provider of the service, or an admin.
- **Permissions:** Customer (own request), Provider (request for their service), Admin

  **Example cURL Request:**
  ```bash
  curl -X GET https://yourdomain.com/api/v1/service-requests/sreq_01H9A2B3C4D5E6F7G8H9J0K1L/ \
    -H "Authorization: Bearer <user_access_token>"
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "sreq_01H9A2B3C4D5E6F7G8H9J0K1L",
    "service": {
      "id": "svc_01H8Z5K9P7Q2R3S4T1V6W8X0Y",
      "title": "Residential Deep Cleaning Service",
      "provider_username": "cleanproservices"
    },
    "customer": {
      "id": "user_01H7XV8S5N2QJWBJ0G8X2E5Y3P",
      "username": "customer_jane",
      "contact_email": "jane@example.com",
      "contact_phone": "+1234567890"
    },
    "provider": {
      "id": "user_01H7XW5R9P6YJ2N3K8M4Z7B1Q0",
      "username": "cleanproservices",
      "contact_email": "contact@cleanpro.com"
    },
    "requested_datetime": "2024-03-10T10:00:00Z",
    "preferred_datetime_start": "2024-03-15T09:00:00Z",
    "preferred_datetime_end": "2024-03-15T12:00:00Z",
    "status": "provider_accepted",
    "customer_notes": "Please focus on kitchen and bathrooms.",
    "provider_notes": "Confirmed. Will bring all necessary supplies.",
    "quoted_price": null,
    "agreed_price": "150.00",
    "cancellation_reason": null,
    "reschedule_reason": null
  }
  ```

  **Example JSON Response (Error 404 Not Found):**
  ```json
  {
    "detail": "Not found."
  }
  ```

---

#### 4.4. Update a Service Request (Status Changes, Notes, etc.)
- **Method:** `PATCH` (typically) or `PUT`
- **Endpoint:** `service-requests/{request_id}/`
- **Description:** Allows updates to a service request. Common actions:
    - **Provider:** Accept/Reject request, add notes, mark as in_progress/completed, propose reschedule.
    - **Customer:** Cancel request (if allowed by status), confirm completion, add notes, accept reschedule.
    - **Admin:** Modify any field, resolve disputes.
- **Permissions:** Varies by action and user role (Customer, Provider, Admin)

  **Example cURL Request (Provider accepts a request):**
  ```bash
  curl -X PATCH https://yourdomain.com/api/v1/service-requests/sreq_01H9A3C5D6E7F8G9H0J1K2L3M/ \
    -H "Authorization: Bearer <provider_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "status": "provider_accepted",
          "provider_notes": "Request accepted. Will arrive at preferred time.",
          "agreed_price": "150.00" 
        }'
  ```

  **Example cURL Request (Customer cancels a request):**
  ```bash
  curl -X PATCH https://yourdomain.com/api/v1/service-requests/sreq_01H9A3C5D6E7F8G9H0J1K2L3M/ \
    -H "Authorization: Bearer <customer_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "status": "customer_cancelled",
          "cancellation_reason": "Change of plans."
        }'
  ```
  
  **Example cURL Request (Provider marks as completed):**
  ```bash
  curl -X PATCH https://yourdomain.com/api/v1/service-requests/sreq_01H9A2B3C4D5E6F7G8H9J0K1L/ \
    -H "Authorization: Bearer <provider_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "status": "completed",
          "provider_notes": "Service completed successfully. Invoice sent."
        }'
  ```

  **Example JSON Request Body (Provider accepts):**
  ```json
  {
    "status": "provider_accepted", // e.g. provider_rejected, in_progress, completed, customer_cancelled, provider_cancelled
    "provider_notes": "Request accepted. Will arrive at preferred time.", // Optional
    "agreed_price": "150.00" // Optional, provider confirms or sets price
    // "quoted_price": "160.00" // If provider wants to quote a different price before acceptance
  }
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "sreq_01H9A3C5D6E7F8G9H0J1K2L3M",
    "status": "provider_accepted",
    "provider_notes": "Request accepted. Will arrive at preferred time.",
    "agreed_price": "150.00",
    // ... other fields
  }
  ```

  **Example JSON Response (Error 400 Bad Request - Invalid status transition):**
  ```json
  {
    "status": ["Cannot transition from 'completed' to 'pending_provider_acceptance'."],
    "detail": "Invalid status transition."
  }
  ```

  **Example JSON Response (Error 403 Forbidden):**
  ```json
  {
    "detail": "You do not have permission to update this request to the status 'completed'."
  }
  ```

---

#### 4.5. Delete a Service Request (Generally not recommended, prefer cancellation)
- **Method:** `DELETE`
- **Endpoint:** `service-requests/{request_id}/`
- **Description:** Deletes a service request. This is typically restricted and might only be allowed for requests in certain states (e.g., a customer deleting a request before it's accepted) or by admins. Soft delete is often preferred.
- **Permissions:** Admin User / Customer (own request, if status allows)

  **Example cURL Request (Admin deleting):**
  ```bash
  curl -X DELETE https://yourdomain.com/api/v1/service-requests/sreq_01H9A3C5D6E7F8G9H0J1K2L3M/ \
    -H "Authorization: Bearer <admin_access_token>"
  ```

  **Example JSON Response (Success 204 No Content):**
  (No body content is returned on successful deletion)

  **Example JSON Response (Error 403 Forbidden - Cannot delete due to status):**
  ```json
  {
    "detail": "Service request cannot be deleted in its current status ('in_progress'). Consider cancelling instead."
  }
  ```


---

## Products
Base Path: `/api/v1/products/`
- **CRUD** `categories/`: Manage product categories.
- **CRUD** (root): Manage products.

---

## Bids
Base Path: `/api/v1/bids/`
- **CRUD** (root): Manage bids on services. Includes operations for creating, viewing, accepting, rejecting bids.

---

## Bookings
Base Path: `/api/v1/bookings/`
- **CRUD** (root): Manage bookings for services.

### Calendar Integration
Base Path: `/api/integrations/calendar/sync/`
- **POST** (root): Synchronize booking data with external calendars.

---

## Payments
Base Path: `/api/v1/payments/`
- **CRUD** `payments/`: Manage payment transactions.
- **CRUD** `accounts/`: Manage user payment gateway accounts.
- **CRUD** `payouts/`: Manage provider payouts.

---

## Messaging
Base Path: `/api/v1/messaging/`
- **CRUD** `threads/`: Manage message threads.
- **CRUD** `messages/`: Manage individual messages (potentially for admin or broader access).
- **GET, POST** `<uuid:thread_id>/`: List messages within a specific thread or create a new message in that thread.

---

## Notifications
Base Path: `/api/v1/notifications/`
- **CRUD** (root): Manage user notifications.

---

## AI Suggestions
Base Path: `/api/v1/ai-suggestions/`
- **CRUD** `suggestions/`: Manage AI-generated suggestions (e.g., for pricing, scheduling).
#### X.1. Manage Feedback for AI Suggestions
- **Endpoint:** `ai-suggestions/feedback/`
- **Description:** Allows users or admins to provide feedback on AI-generated suggestions. This feedback can be used to improve future suggestions.
- **Model Fields (example):** `id`, `suggestion_id` (string or FK, identifies the specific AI suggestion), `user_id` (FK to User, who provided feedback, optional if anonymous), `is_helpful` (boolean, required), `feedback_type` (choices: e.g., 'accurate', 'inaccurate', 'irrelevant', 'helpful', 'not_helpful', 'other'), `comments` (text, optional), `timestamp` (datetime, auto_now_add).

---

##### X.1.1. List Feedback Entries
- **Method:** `GET`
- **Endpoint:** `ai-suggestions/feedback/`
- **Description:** Retrieves a list of feedback entries. Typically restricted to admins or for analytics.
- **Permissions:** Admin User

  **Example cURL Request:**
  ```bash
  curl -X GET "https://yourdomain.com/api/v1/ai-suggestions/feedback/?suggestion_id=sug_01H9B4C5D6E7F8G9H0J1K2L3M" \
    -H "Authorization: Bearer <admin_access_token>"
  ```

  **Query Parameters (Optional):**
  - `page`, `page_size` (integer): For pagination.
  - `suggestion_id` (string): Filter by the specific AI suggestion ID.
  - `user_id` (string): Filter by the user who provided feedback.
  - `is_helpful` (boolean): Filter by whether the suggestion was marked helpful.
  - `feedback_type` (string): Filter by the type of feedback.
  - `date_from`, `date_to` (date string YYYY-MM-DD): Filter by timestamp.

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": "fbk_01H9B5D6E7F8G9H0J1K2L3M4N",
        "suggestion_id": "sug_01H9B4C5D6E7F8G9H0J1K2L3M",
        "user_id": "user_01H7XV8S5N2QJWBJ0G8X2E5Y3P",
        "is_helpful": true,
        "feedback_type": "accurate",
        "comments": "This suggestion was spot on and saved me time.",
        "timestamp": "2024-03-11T14:30:00Z"
      },
      {
        "id": "fbk_01H9B5E7F8G9H0J1K2L3M4N5P",
        "suggestion_id": "sug_01H9B4C5D6E7F8G9H0J1K2L3M",
        "user_id": "user_01H7XW5R9P6YJ2N3K8M4Z7B1Q0",
        "is_helpful": false,
        "feedback_type": "irrelevant",
        "comments": "Not applicable to my current task.",
        "timestamp": "2024-03-11T15:00:00Z"
      }
    ]
  }
  ```

---

##### X.1.2. Create Feedback Entry
- **Method:** `POST`
- **Endpoint:** `ai-suggestions/feedback/`
- **Description:** Allows a user to submit feedback for a specific AI suggestion.
- **Permissions:** Authenticated User

  **Example cURL Request:**
  ```bash
  curl -X POST https://yourdomain.com/api/v1/ai-suggestions/feedback/ \
    -H "Authorization: Bearer <user_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "suggestion_id": "sug_01H9B4C5D6E7F8G9H0J1K2L3M",
          "is_helpful": true,
          "feedback_type": "helpful",
          "comments": "Great suggestion!"
        }'
  ```

  **Example JSON Request Body:**
  ```json
  {
    "suggestion_id": "sug_01H9B4C5D6E7F8G9H0J1K2L3M",
    "is_helpful": true,
    "feedback_type": "helpful", // e.g., 'accurate', 'inaccurate', 'irrelevant', 'other'
    "comments": "Great suggestion!" // Optional
  }
  ```

  **Example JSON Response (Success 201 Created):**
  ```json
  {
    "id": "fbk_01H9B6F8G9H0J1K2L3M4N5P6Q",
    "suggestion_id": "sug_01H9B4C5D6E7F8G9H0J1K2L3M",
    "user_id": "user_01H7XV8S5N2QJWBJ0G8X2E5Y3P", // Authenticated user
    "is_helpful": true,
    "feedback_type": "helpful",
    "comments": "Great suggestion!",
    "timestamp": "2024-03-11T16:00:00Z"
  }
  ```

  **Example JSON Response (Error 400 Bad Request - Validation Error):**
  ```json
  {
    "suggestion_id": ["This field is required."],
    "is_helpful": ["This field is required."]
  }
  ```

---


## Verification (Dedicated Module)
Base Path: `/api/v1/verifications/`
This module manages detailed verification processes for users, covering various types like identity, address, professional qualifications, etc. It is more comprehensive than the basic user verification status checks available under user management.

**Model Fields (example based on `VerificationModel`):**
- `id` (string, Primary Key, e.g., `ver_01HABCDEFGHJKLMNPQRSTVWXYZ`)
- `user` (string, Foreign Key to User ID, e.g., `user_01H7XV8S5N2QJWBJ0G8X2E5Y3P`)
- `verification_type` (string, Enum: `identity`, `address`, `professional`, `educational`, `background_check`, `business_license`, `banking_details`)
- `status` (string, Enum: `unverified`, `pending_submission`, `pending_review`, `in_progress`, `verified`, `rejected`, `expired`, `requires_resubmission`)
- `documents` (array of objects, for document uploads):
    - `document_type` (string, e.g., `passport`, `drivers_license_front`, `utility_bill`, `certificate`)
    - `file_url` (string, URL to the uploaded document)
    - `uploaded_at` (datetime)
- `submitted_at` (datetime, when the user submitted the verification request)
- `last_updated_at` (datetime, when the record was last updated, e.g., status change)
- `reviewed_by` (string, Foreign Key to Admin User ID, optional)
- `review_notes` (text, internal notes by admin, optional)
- `rejection_reason` (text, reason if status is `rejected`, optional)
- `expires_at` (datetime, if the verification has an expiry date, optional)
- `metadata` (json, for storing additional data, e.g., from external verification services)
- `external_reference_id` (string, ID from an external verification provider, optional)

---

#### XI.1. List Verification Requests
- **Method:** `GET`
- **Endpoint:** `verifications/`
- **Description:** Retrieves a list of verification requests.
  - For **Admins**: Lists all verification requests, with filters.
  - For **Authenticated Users**: Lists their own verification requests.
- **Permissions:** Admin User (all) or Authenticated User (own)

  **Example cURL Request (Admin):**
  ```bash
  curl -X GET "https://yourdomain.com/api/v1/verifications/?status=pending_review&verification_type=identity" \
    -H "Authorization: Bearer <admin_access_token>"
  ```

  **Example cURL Request (User retrieving their own):**
  ```bash
  curl -X GET "https://yourdomain.com/api/v1/verifications/" \
    -H "Authorization: Bearer <user_access_token>"
  ```

  **Query Parameters (Optional, primarily for Admins):**
  - `page`, `page_size` (integer): For pagination.
  - `user_id` (string): Filter by user ID.
  - `verification_type` (string): Filter by type (e.g., `identity`, `address`).
  - `status` (string): Filter by status (e.g., `pending_review`, `verified`).
  - `date_submitted_from`, `date_submitted_to` (date string YYYY-MM-DD): Filter by submission date.

  **Example JSON Response (Success 200 OK - Admin View):**
  ```json
  {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": "ver_01HAEFGHJ1KMNPQRSTVWXYZABC",
        "user": "user_01H7XV8S5N2QJWBJ0G8X2E5Y3P",
        "verification_type": "identity",
        "status": "pending_review",
        "documents": [
          {"document_type": "passport", "file_url": "https://cdn.example.com/docs/passport_user123.jpg", "uploaded_at": "2024-03-12T10:00:00Z"}
        ],
        "submitted_at": "2024-03-12T10:00:00Z",
        "last_updated_at": "2024-03-12T10:05:00Z",
        "reviewed_by": null,
        "review_notes": null,
        "rejection_reason": null,
        "expires_at": null,
        "metadata": {},
        "external_reference_id": null
      }
    ]
  }
  ```

---

#### XI.2. Initiate a Verification Process (Submit Documents)
- **Method:** `POST`
- **Endpoint:** `verifications/`
- **Description:** Allows an authenticated user to initiate a new verification process by submitting required information and documents for a specific verification type.
- **Permissions:** Authenticated User

  **Example cURL Request:**
  ```bash
  curl -X POST https://yourdomain.com/api/v1/verifications/ \
    -H "Authorization: Bearer <user_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "verification_type": "identity",
          "documents": [
            {
              "document_type": "passport_front",
              "file_id": "file_temp_id_from_upload_service_123" 
            },
            {
              "document_type": "selfie_with_passport",
              "file_id": "file_temp_id_from_upload_service_456"
            }
          ],
          "metadata": {"consent_given": true}
        }'
  ```
  *(Note: `file_id` assumes a two-step process: 1. Upload file to a temporary storage, get an ID. 2. Submit this ID with the verification request. Alternatively, direct multipart/form-data upload could be used here, which would change the cURL and request structure.)*

  **Example JSON Request Body:**
  ```json
  {
    "verification_type": "identity", // e.g., 'address', 'professional_license'
    "documents": [ // Array of documents being submitted for this verification
      {
        "document_type": "passport_front", // Specific type of document
        "file_id": "file_temp_id_from_upload_service_123" // ID of the pre-uploaded file
      },
      {
        "document_type": "selfie_with_passport",
        "file_id": "file_temp_id_from_upload_service_456"
      }
    ],
    "metadata": { // Optional additional data
      "consent_given": true 
    }
  }
  ```

  **Example JSON Response (Success 201 Created):**
  ```json
  {
    "id": "ver_01HBGHJKLMNPQRSTVWXYZABCDEF",
    "user": "user_01H7XV8S5N2QJWBJ0G8X2E5Y3P", // Authenticated user ID
    "verification_type": "identity",
    "status": "pending_review", // Initial status after submission
    "documents": [
      {"document_type": "passport_front", "file_url": "https://cdn.example.com/docs/final_passport_user123.jpg", "uploaded_at": "2024-03-12T11:00:00Z"},
      {"document_type": "selfie_with_passport", "file_url": "https://cdn.example.com/docs/final_selfie_user123.jpg", "uploaded_at": "2024-03-12T11:00:00Z"}
    ],
    "submitted_at": "2024-03-12T11:00:00Z",
    "last_updated_at": "2024-03-12T11:00:00Z",
    "reviewed_by": null,
    "review_notes": null,
    "rejection_reason": null,
    "expires_at": null,
    "metadata": {"consent_given": true},
    "external_reference_id": null
  }
  ```

  **Example JSON Response (Error 400 Bad Request - Validation Error):**
  ```json
  {
    "verification_type": ["This field is required."],
    "documents": ["This field is required and must contain at least one document."]
  }
  ```
  **Example JSON Response (Error 409 Conflict - Already Pending/Verified):**
  ```json
  {
    "detail": "An active verification request of this type already exists or is already verified."
  }
  ```

---

#### XI.3. Retrieve a Specific Verification Request
- **Method:** `GET`
- **Endpoint:** `verifications/{verification_id}/`
- **Description:** Retrieves details of a specific verification request.
- **Permissions:** Admin User or Authenticated User (if they own the request)

  **Example cURL Request:**
  ```bash
  curl -X GET "https://yourdomain.com/api/v1/verifications/ver_01HAEFGHJ1KMNPQRSTVWXYZABC/" \
    -H "Authorization: Bearer <user_or_admin_access_token>"
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "ver_01HAEFGHJ1KMNPQRSTVWXYZABC",
    "user": "user_01H7XV8S5N2QJWBJ0G8X2E5Y3P",
    "verification_type": "identity",
    "status": "pending_review",
    "documents": [
      {"document_type": "passport", "file_url": "https://cdn.example.com/docs/passport_user123.jpg", "uploaded_at": "2024-03-12T10:00:00Z"}
    ],
    "submitted_at": "2024-03-12T10:00:00Z",
    "last_updated_at": "2024-03-12T10:05:00Z",
    "reviewed_by": null,
    "review_notes": null,
    "rejection_reason": null,
    "expires_at": null,
    "metadata": {},
    "external_reference_id": null
  }
  ```

---

#### XI.4. Update a Verification Request (Admin Action)
- **Method:** `PATCH` (or `PUT`)
- **Endpoint:** `verifications/{verification_id}/`
- **Description:** Allows an Admin to update the status and details of a verification request (e.g., mark as verified, rejected, add review notes). Users might have limited update capabilities, e.g., resubmitting documents if status is `requires_resubmission`. This example focuses on Admin updates.
- **Permissions:** Admin User

  **Example cURL Request (Admin marks as verified):**
  ```bash
  curl -X PATCH "https://yourdomain.com/api/v1/verifications/ver_01HAEFGHJ1KMNPQRSTVWXYZABC/" \
    -H "Authorization: Bearer <admin_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "status": "verified",
          "review_notes": "Documents clear, identity confirmed.",
          "expires_at": "2026-03-12T00:00:00Z" 
        }'
  ```

  **Example JSON Request Body (Admin update):**
  ```json
  {
    "status": "verified", // Or 'rejected', 'in_progress', 'requires_resubmission'
    "review_notes": "Documents clear, identity confirmed.", // Optional
    "rejection_reason": null, // Provide if status is 'rejected'
    "expires_at": "2026-03-12T00:00:00Z" // Optional, if applicable
  }
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "ver_01HAEFGHJ1KMNPQRSTVWXYZABC",
    "user": "user_01H7XV8S5N2QJWBJ0G8X2E5Y3P",
    "verification_type": "identity",
    "status": "verified",
    "documents": [
      {"document_type": "passport", "file_url": "https://cdn.example.com/docs/passport_user123.jpg", "uploaded_at": "2024-03-12T10:00:00Z"}
    ],
    "submitted_at": "2024-03-12T10:00:00Z",
    "last_updated_at": "2024-03-12T12:30:00Z", // Updated timestamp
    "reviewed_by": "admin_01H8YZA1B2C3D4E5F6G7H8J9K0", // Admin who performed the update
    "review_notes": "Documents clear, identity confirmed.",
    "rejection_reason": null,
    "expires_at": "2026-03-12T00:00:00Z",
    "metadata": {},
    "external_reference_id": null
  }
  ```
*(Note: DELETE operations for verification records are typically rare and might be restricted to super-admins or handled by data retention policies rather than direct API calls by most admins.)*

---

## Reviews
Base Path: `/api/v1/reviews/`
This section covers endpoints for managing reviews and ratings submitted by users for services or providers.

**Model Fields (example `Review` model):**
- `id` (string, Primary Key, e.g., `rev_01HCDETFGHIJKLMNOPQRSTUVWXYZ`)
- `user` (string, Foreign Key to User ID - the customer who wrote the review)
- `provider_id` (string, Foreign Key to User ID - the provider being reviewed, optional, use if review is for a provider directly)
- `service_id` (string, Foreign Key to Service ID - the service being reviewed, optional, use if review is for a specific service)
- `booking_id` (string, Foreign Key to Booking ID - links review to a specific completed transaction, highly recommended)
- `rating` (integer, e.g., 1 to 5 stars, required)
- `title` (string, optional, a headline for the review)
- `comment` (text, the main content of the review, optional but usually encouraged)
- `is_anonymous` (boolean, default: `false`. If true, `user` details might be hidden in public views)
- `status` (string, Enum: `pending_approval`, `approved`, `rejected`, `edited_by_user`, `edited_by_admin`. Default: `pending_approval` or `approved` based on platform policy)
- `created_at` (datetime, auto_now_add)
- `updated_at` (datetime, auto_now)
- `admin_notes` (text, internal notes by admin for moderation, optional)
- `reply_to` (string, Foreign Key to another Review ID, if this is a reply from a provider, optional)

---

#### XII.1. List Reviews
- **Method:** `GET`
- **Endpoint:** `reviews/`
- **Description:** Retrieves a list of reviews. Publicly, this usually shows approved reviews. Admins might see all.
- **Permissions:** Public (for approved reviews), Admin User (for all reviews including pending/rejected)

  **Example cURL Request (Public, for a specific service):**
  ```bash
  curl -X GET "https://yourdomain.com/api/v1/reviews/?service_id=svc_01H7Y8Z9A0B1C2D3E4F5G6H7J8&status=approved"
  ```

  **Example cURL Request (Admin, listing pending reviews):**
  ```bash
  curl -X GET "https://yourdomain.com/api/v1/reviews/?status=pending_approval" \
    -H "Authorization: Bearer <admin_access_token>"
  ```

  **Query Parameters (Optional):**
  - `page`, `page_size` (integer): For pagination.
  - `service_id` (string): Filter reviews for a specific service.
  - `provider_id` (string): Filter reviews for a specific provider.
  - `user_id` (string): Filter reviews written by a specific customer (usually admin only).
  - `booking_id` (string): Filter review associated with a specific booking.
  - `rating` (integer): Filter by rating (e.g., `rating=5`).
  - `status` (string): Filter by status (e.g., `approved`, `pending_approval`). Public default should be `approved`.
  - `ordering` (string): e.g., `-created_at` (newest first), `rating` (lowest first), `-rating` (highest first).

  **Example JSON Response (Success 200 OK - Public List for a Service):**
  ```json
  {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": "rev_01HCEFGHJ1KMNPQRSTVWXYZABC",
        "user": { // Publicly, may show limited user info or be anonymous
          "username": "HappyCustomer123", 
          "avatar_url": "https://cdn.example.com/avatars/user123.png"
        },
        "service_id": "svc_01H7Y8Z9A0B1C2D3E4F5G6H7J8",
        "rating": 5,
        "title": "Excellent Service!",
        "comment": "The provider was professional and the service exceeded my expectations.",
        "is_anonymous": false,
        "status": "approved",
        "created_at": "2024-03-15T10:00:00Z",
        "updated_at": "2024-03-15T10:05:00Z"
      }
    ]
  }
  ```

---

#### XII.2. Create a Review
- **Method:** `POST`
- **Endpoint:** `reviews/`
- **Description:** Allows an authenticated user (typically a customer) to submit a review for a service/provider, often linked to a completed booking.
- **Permissions:** Authenticated User (Customer role)

  **Example cURL Request:**
  ```bash
  curl -X POST https://yourdomain.com/api/v1/reviews/ \
    -H "Authorization: Bearer <customer_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "booking_id": "bk_01H6X7Y8Z9A0B1C2D3E4F5G6H7", 
          "service_id": "svc_01H7Y8Z9A0B1C2D3E4F5G6H7J8", 
          "rating": 5,
          "title": "Fantastic Experience",
          "comment": "Would definitely recommend this service to others.",
          "is_anonymous": false
        }'
  ```

  **Example JSON Request Body:**
  ```json
  {
    "booking_id": "bk_01H6X7Y8Z9A0B1C2D3E4F5G6H7", // Strongly recommended
    "service_id": "svc_01H7Y8Z9A0B1C2D3E4F5G6H7J8", // Or provider_id
    "rating": 5, // Required
    "title": "Fantastic Experience", // Optional
    "comment": "Would definitely recommend this service to others.", // Optional
    "is_anonymous": false // Optional, default false
  }
  ```

  **Example JSON Response (Success 201 Created):**
  ```json
  {
    "id": "rev_01HCFGHIJKLMNOPQRSTUVWXYZABCDE",
    "user": "user_01H7XV8S5N2QJWBJ0G8X2E5Y3P", // ID of the user who wrote it
    "booking_id": "bk_01H6X7Y8Z9A0B1C2D3E4F5G6H7",
    "service_id": "svc_01H7Y8Z9A0B1C2D3E4F5G6H7J8",
    "rating": 5,
    "title": "Fantastic Experience",
    "comment": "Would definitely recommend this service to others.",
    "is_anonymous": false,
    "status": "pending_approval", // Or "approved" if auto-approval is on
    "created_at": "2024-03-15T11:30:00Z",
    "updated_at": "2024-03-15T11:30:00Z",
    "admin_notes": null
  }
  ```

  **Example JSON Response (Error 400 Bad Request - Validation Error):**
  ```json
  {
    "rating": ["This field is required."],
    "booking_id": ["A review must be linked to a valid booking or service/provider."]
  }
  ```
  **Example JSON Response (Error 403 Forbidden - Already Reviewed):**
  ```json
  {
    "detail": "You have already submitted a review for this booking/service."
  }
  ```

---

#### XII.3. Retrieve a Specific Review
- **Method:** `GET`
- **Endpoint:** `reviews/{review_id}/`
- **Description:** Retrieves details of a specific review.
- **Permissions:** Public (if approved), or Owner/Admin.

  **Example cURL Request:**
  ```bash
  curl -X GET "https://yourdomain.com/api/v1/reviews/rev_01HCEFGHJ1KMNPQRSTVWXYZABC/"
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "rev_01HCEFGHJ1KMNPQRSTVWXYZABC",
    "user": { 
      "username": "HappyCustomer123", 
      "avatar_url": "https://cdn.example.com/avatars/user123.png"
    },
    "service_id": "svc_01H7Y8Z9A0B1C2D3E4F5G6H7J8",
    "rating": 5,
    "title": "Excellent Service!",
    "comment": "The provider was professional and the service exceeded my expectations.",
    "is_anonymous": false,
    "status": "approved",
    "created_at": "2024-03-15T10:00:00Z",
    "updated_at": "2024-03-15T10:05:00Z",
    "admin_notes": "Reviewed and approved by admin_X." 
  }
  ```

---

#### XII.4. Update a Review
- **Method:** `PATCH` (or `PUT`)
- **Endpoint:** `reviews/{review_id}/`
- **Description:** Allows a user to update their own review (e.g., within a time limit or if status is `pending_approval`) or an Admin to moderate a review (e.g., change status, add notes).
- **Permissions:** Owner (limited fields, conditional) or Admin User.

  **Example cURL Request (User updating their comment):**
  ```bash
  curl -X PATCH "https://yourdomain.com/api/v1/reviews/rev_01HCEFGHJ1KMNPQRSTVWXYZABC/" \
    -H "Authorization: Bearer <customer_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "comment": "Update: After a month, still very happy with the results!"
        }'
  ```

  **Example cURL Request (Admin approving a review):**
  ```bash
  curl -X PATCH "https://yourdomain.com/api/v1/reviews/rev_01HCFGHIJKLMNOPQRSTUVWXYZABCDE/" \
    -H "Authorization: Bearer <admin_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "status": "approved",
          "admin_notes": "Review content verified and approved."
        }'
  ```

  **Example JSON Request Body (User update):**
  ```json
  {
    "rating": 4, // If allowed to change
    "title": "Update: Good, but one small issue.",
    "comment": "Update: After a month, still very happy with the results, though one minor detail came up."
  }
  ```

  **Example JSON Request Body (Admin update):**
  ```json
  {
    "status": "approved", // Or 'rejected'
    "admin_notes": "Review content verified and approved."
  }
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "rev_01HCEFGHJ1KMNPQRSTVWXYZABC",
    // ... other fields ...
    "comment": "Update: After a month, still very happy with the results!",
    "status": "approved", // Could be updated by user or admin
    "updated_at": "2024-03-15T12:00:00Z", // Timestamp updated
    "admin_notes": "Review content verified and approved." // If updated by admin
  }
  ```

---

#### XII.5. Delete a Review
- **Method:** `DELETE`
- **Endpoint:** `reviews/{review_id}/`
- **Description:** Allows an Admin to delete a review (e.g., if it violates terms of service). Users might be able to delete their own reviews under certain conditions.
- **Permissions:** Admin User, or Owner (conditional, e.g., if review is pending or policy allows).

  **Example cURL Request (Admin deleting a review):**
  ```bash
  curl -X DELETE "https://yourdomain.com/api/v1/reviews/rev_01HCEFGHJ1KMNPQRSTVWXYZABC/" \
    -H "Authorization: Bearer <admin_access_token>"
  ```

  **Example JSON Response (Success 204 No Content):**
  (No body content for 204)

  **Example JSON Response (Error 403 Forbidden):**
  ```json
  {
    "detail": "You do not have permission to delete this review."
  }
  ```
  **Example JSON Response (Error 404 Not Found):**
  ```json
  {
    "detail": "Not found."
  }
  ```

---

## Analytics (Primarily Admin)
Base Path: `/api/analytics/`

This section provides endpoints for accessing aggregated data and reports for administrative and business intelligence purposes. Access is typically restricted to Admin Users.

**Common Data Points & Reports (Examples - not direct models):**
- **Platform Overview:** Total users, new user registrations, active users, total services, total bookings, total revenue.
- **User Analytics:** User growth trends, demographics (if collected), engagement metrics (e.g., average sessions, feature usage).
- **Service Analytics:** Popular services, service category performance, booking trends per service, average ratings.
- **Provider Analytics:** Provider growth, top-performing providers, earnings per provider.
- **Financial Analytics:** Revenue trends (daily, weekly, monthly), commission reports, payout summaries.
- **Booking Analytics:** Booking volume, completion rates, cancellation rates, peak booking times.

---

#### XIII.1. Get Platform Summary Statistics
- **Method:** `GET`
- **Endpoint:** `analytics/summary/`
- **Description:** Retrieves a summary of key platform metrics.
- **Permissions:** Admin User

  **Example cURL Request:**
  ```bash
  curl -X GET "https://yourdomain.com/api/analytics/summary/?period=last_30_days" \
    -H "Authorization: Bearer <admin_access_token>"
  ```

  **Query Parameters (Optional):**
  - `period` (string): Time period for the summary (e.g., `today`, `last_7_days`, `last_30_days`, `month_to_date`, `year_to_date`, `all_time`). Default: `last_30_days`.
  - `compare_to_previous` (boolean): If true, includes comparison data from the previous period. Default: `false`.

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "period": "last_30_days",
    "generated_at": "2024-03-16T10:00:00Z",
    "summary": {
      "total_users": {
        "current": 15200,
        "change_percentage": 5.2 // if compare_to_previous=true
      },
      "new_registrations": {
        "current": 850,
        "change_percentage": 10.1
      },
      "active_users_daily_avg": {
        "current": 1200,
        "change_percentage": 2.0
      },
      "total_services_listed": {
        "current": 3500,
        "change_percentage": 3.0
      },
      "total_bookings_completed": {
        "current": 2500,
        "change_percentage": 8.5
      },
      "total_revenue": {
        "current_amount": "75000.00",
        "currency": "USD",
        "change_percentage": 12.0
      },
      "average_booking_value": {
        "current_amount": "30.00",
        "currency": "USD",
        "change_percentage": 3.5
      }
    }
  }
  ```

---

#### XIII.2. Get User Growth Report
- **Method:** `GET`
- **Endpoint:** `analytics/users/growth/`
- **Description:** Retrieves data on user registration trends over a specified period.
- **Permissions:** Admin User

  **Example cURL Request:**
  ```bash
  curl -X GET "https://yourdomain.com/api/analytics/users/growth/?start_date=2024-01-01&end_date=2024-03-15&granularity=monthly" \
    -H "Authorization: Bearer <admin_access_token>"
  ```

  **Query Parameters (Required/Optional):**
  - `start_date` (date string YYYY-MM-DD): Start of the reporting period.
  - `end_date` (date string YYYY-MM-DD): End of the reporting period.
  - `granularity` (string): Aggregation level (e.g., `daily`, `weekly`, `monthly`). Default: `daily`.
  - `user_type` (string): Filter by user type (e.g., `customer`, `provider`, `all`). Default: `all`.

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "report_period": {"start_date": "2024-01-01", "end_date": "2024-03-15"},
    "granularity": "monthly",
    "user_type": "all",
    "data_points": [
      {
        "period": "2024-01",
        "new_users": 250,
        "total_users_cumulative": 14600
      },
      {
        "period": "2024-02",
        "new_users": 300,
        "total_users_cumulative": 14900
      },
      {
        "period": "2024-03", // Partial month up to end_date
        "new_users": 300,
        "total_users_cumulative": 15200
      }
    ]
  }
  ```

---

#### XIII.3. Get Revenue Report
- **Method:** `GET`
- **Endpoint:** `analytics/revenue/`
- **Description:** Retrieves financial revenue data over a specified period.
- **Permissions:** Admin User (typically with specific financial roles)

  **Example cURL Request:**
  ```bash
  curl -X GET "https://yourdomain.com/api/analytics/revenue/?start_date=2024-03-01&end_date=2024-03-15&granularity=daily" \
    -H "Authorization: Bearer <admin_access_token_financial>"
  ```

  **Query Parameters (Required/Optional):**
  - `start_date` (date string YYYY-MM-DD): Start of the reporting period.
  - `end_date` (date string YYYY-MM-DD): End of the reporting period.
  - `granularity` (string): Aggregation level (e.g., `daily`, `weekly`, `monthly`). Default: `daily`.
  - `service_category_id` (string): Filter revenue by a specific service category.
  - `provider_id` (string): Filter revenue generated by a specific provider.

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "report_period": {"start_date": "2024-03-01", "end_date": "2024-03-15"},
    "granularity": "daily",
    "currency": "USD",
    "data_points": [
      {
        "period": "2024-03-01",
        "total_revenue": "2500.50",
        "total_bookings": 80,
        "platform_commission": "250.05"
      },
      {
        "period": "2024-03-02",
        "total_revenue": "2800.75",
        "total_bookings": 95,
        "platform_commission": "280.07"
      }
      // ... more data points
    ],
    "totals_for_period": {
      "total_revenue": "35000.00",
      "total_bookings": 1200,
      "platform_commission": "3500.00"
    }
  }
  ```
*(Note: Analytics can be very extensive. The above are just examples. Other reports might include service performance, booking trends, cancellation reasons, etc. Each might have its own endpoint or be parameters of a more generic reporting endpoint. The admin CRUD operations for users and services listed previously might be better placed under their respective main sections or a dedicated 'Admin Panel' section if they are UI-driven rather than pure analytics endpoints.)*

---

## Synchronization (Offline Support)
Base Path: `/api/sync/`

This section outlines endpoints designed to support offline functionality in client applications. It allows users to download essential data and later synchronize local changes with the server.

---

#### XIV.1. Get Data for Offline Use
- **Method:** `GET`
- **Endpoint:** `sync/data/`
- **Description:** Allows a client to download a bundle of data relevant to the user for offline access. This might include their profile, recent bookings, messages, favorite providers, etc.
- **Permissions:** Authenticated User (Customer or Provider)

  **Example cURL Request:**
  ```bash
  curl -X GET "https://yourdomain.com/api/sync/data/?since=<timestamp_or_sequence_id>" \
    -H "Authorization: Bearer <user_access_token>"
  ```

  **Query Parameters (Optional):**
  - `since` (string/integer): A timestamp (ISO 8601) or a sequence ID indicating the last sync point. If provided, only data changed since this point will be returned. If omitted, a full data download might be initiated (potentially large).
  - `data_scopes` (comma-separated string): Specific data scopes to sync (e.g., `profile,bookings,messages`). If omitted, a default set of essential data is returned.

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "sync_timestamp": "2024-03-16T12:00:00Z", // Server timestamp of this sync
    "next_sync_token": "seq_id_12345", // Token/ID to use for the next 'since' parameter
    "data": {
      "user_profile": {
        "id": "user_abc_123",
        "username": "offlineUser",
        "email": "user@example.com",
        "phone_number": "+1234567890",
        "profile_picture_url": "https://yourdomain.com/media/profiles/user_abc_123.jpg"
        // ... other profile fields
      },
      "bookings": [
        {
          "id": "booking_xyz_789",
          "service_id": "service_qwe_456",
          "service_name": "Premium Car Wash",
          "provider_id": "provider_jkl_101",
          "provider_name": "Speedy Cleaners",
          "scheduled_datetime": "2024-03-20T14:00:00Z",
          "status": "confirmed",
          "last_updated": "2024-03-15T09:30:00Z"
          // ... other booking details
        }
      ],
      "messages": [
        {
          "id": "msg_111",
          "chat_id": "chat_222",
          "sender_id": "provider_jkl_101",
          "receiver_id": "user_abc_123",
          "content": "Looking forward to your appointment!",
          "timestamp": "2024-03-15T10:00:00Z",
          "is_read": false
        }
      ]
      // ... other data scopes like 'favorites', 'service_requests', etc.
    },
    "deleted_ids": { // IDs of records deleted since last sync
        "bookings": ["booking_old_001"],
        "messages": []
    }
  }
  ```
  **Note:** The structure of the `data` object will depend heavily on the application's specific needs for offline functionality.

---

#### XIV.2. Push Local Changes to Server
- **Method:** `POST`
- **Endpoint:** `sync/data/`
- **Description:** Allows a client to send locally created or modified data back to the server. The server will process these changes, resolve conflicts if any, and persist them.
- **Permissions:** Authenticated User (Customer or Provider)

  **Example cURL Request:**
  ```bash
  curl -X POST "https://yourdomain.com/api/sync/data/" \
    -H "Authorization: Bearer <user_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "client_sync_timestamp": "2024-03-16T11:50:00Z",
          "changes": [
            {
              "type": "booking",
              "action": "update", // "create", "update", "delete"
              "id": "booking_xyz_789", // required for update/delete
              "payload": {
                "status": "cancelled",
                "cancellation_reason": "Changed my mind"
              }
            },
            {
              "type": "message",
              "action": "create",
              "payload": {
                "chat_id": "chat_222",
                "receiver_id": "provider_jkl_101",
                "content": "Can we reschedule?"
              }
            }
          ]
        }'
  ```

  **Request Body:**
  - `client_sync_timestamp` (string ISO 8601): Timestamp from the client when the sync batch was created. Useful for conflict resolution.
  - `changes` (array of objects): A list of changes to be applied.
    - `type` (string): The type of data (e.g., `booking`, `message`, `review`).
    - `action` (string): The action performed (`create`, `update`, `delete`).
    - `id` (string, optional): The ID of the record for `update` or `delete` actions.
    - `payload` (object): The data for `create` or `update` actions.

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "status": "success",
    "processed_at": "2024-03-16T12:05:00Z",
    "results": [
      {
        "client_change_index": 0, // Corresponds to the index in the request 'changes' array
        "type": "booking",
        "action": "update",
        "id": "booking_xyz_789",
        "status": "applied", // "applied", "conflict", "failed"
        "server_id": "booking_xyz_789", // Confirmed server ID
        "message": "Booking successfully cancelled."
      },
      {
        "client_change_index": 1,
        "type": "message",
        "action": "create",
        "status": "applied",
        "server_id": "msg_112", // New ID assigned by server
        "message": "Message sent."
      }
    ],
    "conflicts": [ // Optional: detailed info about conflicts if any
      // {
      //   "client_change_index": X,
      //   "type": "...", "id": "...",
      //   "conflict_type": "edit_conflict", // e.g., "edit_conflict", "delete_conflict"
      //   "server_version": { ... }, // Current server state of the conflicted item
      //   "message": "Item was modified on the server after your last sync."
      // }
    ],
    "next_sync_token": "seq_id_12346" // New token for subsequent GET /sync/data/
  }
  ```

  **Example JSON Response (Error 400 Bad Request - e.g., validation error):**
  ```json
  {
    "status": "failed",
    "message": "Validation errors in changes.",
    "errors": [
      {
        "client_change_index": 0,
        "field": "payload.status",
        "error": "Invalid status transition for booking."
      }
    ]
  }
  ```
  **Note:** Sync conflict resolution can be complex and requires a well-defined strategy (e.g., last-write-wins, client-wins, server-wins, or manual resolution). The server's response should guide the client on how to handle conflicts.

---

## System & Health Checks
Base Path: `/` (Note: Some endpoints might be under `/api/v1/` or a dedicated path depending on deployment)

This section describes endpoints used for monitoring the health and status of the application and its dependencies.

---

#### XV.1. Basic Application Health Check
- **Method:** `GET`
- **Endpoint:** `health/` (or `/api/v1/health/`)
- **Description:** A simple endpoint to check if the application is running and responsive.
- **Permissions:** Public (usually)

  **Example cURL Request:**
  ```bash
  curl -X GET "https://yourdomain.com/health/"
  ```
  *(Adjust endpoint to `/api/v1/health/` if applicable)*

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "status": "ok",
    "message": "Application is running.",
    "timestamp": "2024-03-16T14:30:00Z"
  }
  ```

  **Example JSON Response (Error 503 Service Unavailable - if app is down/unhealthy):**
  ```json
  {
    "status": "error",
    "message": "Application is currently unhealthy.",
    "details": "Specific error message or component status if available."
  }
  ```

---

#### XV.2. Database Health Check
- **Method:** `GET`
- **Endpoint:** `health/db/` (or `/api/v1/health/db/`)
- **Description:** Checks the connectivity and health of the primary database.
- **Permissions:** Public or Restricted (depending on security policy)

  **Example cURL Request:**
  ```bash
  curl -X GET "https://yourdomain.com/health/db/"
  ```
  *(Adjust endpoint to `/api/v1/health/db/` if applicable)*

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "status": "ok",
    "message": "Database connection successful.",
    "database_type": "PostgreSQL", // Example
    "timestamp": "2024-03-16T14:31:00Z"
  }
  ```

  **Example JSON Response (Error 503 Service Unavailable - if DB connection fails):**
  ```json
  {
    "status": "error",
    "message": "Database connection failed.",
    "details": "Could not connect to the database: [Error details]",
    "timestamp": "2024-03-16T14:32:00Z"
  }
  ```

---

#### XV.3. Cache Health Check (Example)
- **Method:** `GET`
- **Endpoint:** `health/cache/` (or `/api/v1/health/cache/`)
- **Description:** Checks the connectivity and health of the caching service (e.g., Redis).
- **Permissions:** Public or Restricted

  **Example cURL Request:**
  ```bash
  curl -X GET "https://yourdomain.com/health/cache/"
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "status": "ok",
    "message": "Cache service connection successful.",
    "cache_type": "Redis", // Example
    "timestamp": "2024-03-16T14:33:00Z"
  }
  ```

  **Example JSON Response (Error 503 Service Unavailable - if cache connection fails):**
  ```json
  {
    "status": "error",
    "message": "Cache service connection failed.",
    "details": "[Error details]",
    "timestamp": "2024-03-16T14:34:00Z"
  }
  ```

---

#### XV.4. Prometheus Metrics Endpoint
- **Method:** `GET`
- **Endpoint:** `metrics` (Usually at the root, e.g., `https://yourdomain.com/metrics`)
- **Description:** Exposes application and system metrics in Prometheus format. This endpoint is typically provided by a library like `django-prometheus`.
- **Permissions:** Restricted (often to internal network or specific IPs)

  **Example cURL Request:**
  ```bash
  curl -X GET "https://yourdomain.com/metrics"
  ```

  **Example Response (Success 200 OK - Prometheus format):**
  ```
  # HELP django_http_requests_latency_seconds_by_view_method Histogram of HTTP request latency, labeled by view and method.
  # TYPE django_http_requests_latency_seconds_by_view_method histogram
  django_http_requests_latency_seconds_by_view_method_bucket{le="0.005",method="GET",view="your_view_name"} 0.0
  django_http_requests_latency_seconds_by_view_method_bucket{le="0.01",method="GET",view="your_view_name"} 0.0
  # ... many more metrics
  ```
  **Note:** The response is plain text, not JSON, and follows the Prometheus exposition format.

Admin Interface:
- **ALL** `/admin/`: Django admin interface.

---

## Notifications
Base Path: `/api/v1/notifications/`

This module handles real-time notifications for users, including push notifications, in-app notifications, and managing notification status (read/unread, archived).

### Model Fields (example based on `Notification` model):
- `id` (string, Primary Key, e.g., `notif_01HABCDEFGHJKLMNPQRSTVWXYZ`)
- `recipient` (string, Foreign Key to User ID, e.g., `user_01H7XV8S5N2QJWBJ0G8X2E5Y3P`)
- `notification_type` (string, Enum: `bid_received`, `bid_accepted`, `booking_created`, `message_received`, `system`, etc.)
- `title` (string, max 255 chars)
- `message` (text)
- `is_read` (boolean, default `false`)
- `group` (string, Foreign Key to NotificationGroup ID, optional, e.g., `notif_group_01HABCDEFGHJKLMNPQRSTVWXYZ`)
- `content_type` (string, Generic Foreign Key to related model type)
- `object_id` (string, Generic Foreign Key to related object ID)
- `action_url` (string, URL to redirect to when notification is clicked, optional)
- `created_at` (datetime)
- `updated_at` (datetime)

---

#### XII.1. List Notifications
- **Method:** `GET`
- **Endpoint:** `notifications/`
- **Description:** Retrieves a list of notifications for the authenticated user. Supports filtering and pagination.
- **Permissions:** Authenticated User

  **Example cURL Request:**
  ```bash
  curl -X GET "https://yourdomain.com/api/v1/notifications/?is_read=false&notification_type=message_received" \
    -H "Authorization: Bearer <user_access_token>"
  ```

  **Query Parameters (Optional):**
  - `is_read` (boolean): Filter by read status (`true` or `false`).
  - `notification_type` (string): Filter by type (e.g., `bid_received`, `system`).
  - `group_id` (string): Filter by notification group ID.
  - `page`, `page_size` (integer): For pagination.

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": "notif_01HABCDEFGHJKLMNPQRSTVWXYZ",
        "recipient": "user_01H7XV8S5N2QJWBJ0G8X2E5Y3P",
        "notification_type": "message_received",
        "title": "New Message from John Doe",
        "message": "You have a new message regarding your booking #123.",
        "is_read": false,
        "group": null,
        "action_url": "https://yourdomain.com/messages/123",
        "created_at": "2024-05-29T10:00:00Z"
      },
      {
        "id": "notif_01HABCDEFGHJKLMNPQRSTVWXYA",
        "recipient": "user_01H7XV8S5N2QJWBJ0G8X2E5Y3P",
        "notification_type": "bid_received",
        "title": "New Bid on Your Service Request",
        "message": "A new bid has been placed on your 'Lawn Mowing' request.",
        "is_read": false,
        "group": null,
        "action_url": "https://yourdomain.com/bids/456",
        "created_at": "2024-05-29T09:30:00Z"
      }
    ]
  }
  ```

---

#### XII.2. Retrieve a Specific Notification
- **Method:** `GET`
- **Endpoint:** `notifications/{notification_id}/`
- **Description:** Retrieves details of a specific notification.
- **Permissions:** Authenticated User (must be the recipient)

  **Example cURL Request:**
  ```bash
  curl -X GET "https://yourdomain.com/api/v1/notifications/notif_01HABCDEFGHJKLMNPQRSTVWXYZ/" \
    -H "Authorization: Bearer <user_access_token>"
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "notif_01HABCDEFGHJKLMNPQRSTVWXYZ",
    "recipient": "user_01H7XV8S5N2QJWBJ0G8X2E5Y3P",
    "notification_type": "message_received",
    "title": "New Message from John Doe",
    "message": "You have a new message regarding your booking #123.",
    "is_read": false,
    "group": null,
    "action_url": "https://yourdomain.com/messages/123",
    "created_at": "2024-05-29T10:00:00Z"
  }
  ```

---

#### XII.3. Mark Notification as Read/Unread
- **Method:** `PATCH`
- **Endpoint:** `notifications/{notification_id}/`
- **Description:** Updates the `is_read` status of a specific notification.
- **Permissions:** Authenticated User (must be the recipient)

  **Example cURL Request (Mark as Read):**
  ```bash
  curl -X PATCH "https://yourdomain.com/api/v1/notifications/notif_01HABCDEFGHJKLMNPQRSTVWXYZ/" \
    -H "Authorization: Bearer <user_access_token>" \
    -H "Content-Type: application/json" \
    -d '{"is_read": true}'
  ```

  **Example JSON Request Body:**
  ```json
  {
    "is_read": true
  }
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "notif_01HABCDEFGHJKLMNPQRSTVWXYZ",
    "recipient": "user_01H7XV8S5N2QJWBJ0G8X2E5Y3P",
    "notification_type": "message_received",
    "title": "New Message from John Doe",
    "message": "You have a new message regarding your booking #123.",
    "is_read": true,
    "group": null,
    "action_url": "https://yourdomain.com/messages/123",
    "created_at": "2024-05-29T10:00:00Z"
  }
  ```

---

#### XII.4. Delete a Notification
- **Method:** `DELETE`
- **Endpoint:** `notifications/{notification_id}/`
- **Description:** Deletes a specific notification. This typically archives it or removes it from the user's view.
- **Permissions:** Authenticated User (must be the recipient)

  **Example cURL Request:**
  ```bash
  curl -X DELETE "https://yourdomain.com/api/v1/notifications/notif_01HABCDEFGHJKLMNPQRSTVWXYZ/" \
    -H "Authorization: Bearer <user_access_token>"
  ```

  **Example JSON Response (Success 204 No Content):**
  (No body content is returned on successful deletion)

---

## Notification Groups
Base Path: `/api/v1/notification-groups/`

This module manages logical groupings for notifications, allowing for better organization and management of related notifications (e.g., all notifications related to a specific booking).

### Model Fields (example based on `NotificationGroup` model):
- `id` (string, Primary Key, e.g., `notif_group_01HABCDEFGHJKLMNPQRSTVWXYZ`)
- `name` (string, max 255 chars, unique)
- `description` (text, optional)
- `created_at` (datetime)
- `updated_at` (datetime)

---

#### XIII.1. List Notification Groups
- **Method:** `GET`
- **Endpoint:** `notification-groups/`
- **Description:** Retrieves a list of notification groups. Primarily for internal use or admin purposes.
- **Permissions:** Admin User (or potentially Authenticated User for their own related groups)

  **Example cURL Request:**
  ```bash
  curl -X GET "https://yourdomain.com/api/v1/notification-groups/" \
    -H "Authorization: Bearer <admin_access_token>"
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": "notif_group_01HABCDEFGHJKLMNPQRSTVWXYZ",
        "name": "Booking #123 Updates",
        "description": "All notifications related to booking #123.",
        "created_at": "2024-05-29T08:00:00Z",
        "updated_at": "2024-05-29T08:00:00Z"
      }
    ]
  }
  ```

---

#### XIII.2. Retrieve a Specific Notification Group
- **Method:** `GET`
- **Endpoint:** `notification-groups/{group_id}/`
- **Description:** Retrieves details of a specific notification group.
- **Permissions:** Admin User (or Authenticated User if they have access to the group)

  **Example cURL Request:**
  ```bash
  curl -X GET "https://yourdomain.com/api/v1/notification-groups/notif_group_01HABCDEFGHJKLMNPQRSTVWXYZ/" \
    -H "Authorization: Bearer <admin_access_token>"
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "notif_group_01HABCDEFGHJKLMNPQRSTVWXYZ",
    "name": "Booking #123 Updates",
    "description": "All notifications related to booking #123.",
    "created_at": "2024-05-29T08:00:00Z",
    "updated_at": "2024-05-29T08:00:00Z"
  }
  ```

---

#### XIII.3. Create a Notification Group
- **Method:** `POST`
- **Endpoint:** `notification-groups/`
- **Description:** Creates a new notification group. Typically restricted to internal system processes or admin users.
- **Permissions:** Admin User

  **Example cURL Request:**
  ```bash
  curl -X POST "https://yourdomain.com/api/v1/notification-groups/" \
    -H "Authorization: Bearer <admin_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
      "name": "Service Request #789 Discussions",
      "description": "Group for all messages and updates related to service request #789."
    }'
  ```

  **Example JSON Request Body:**
  ```json
  {
    "name": "Service Request #789 Discussions",
    "description": "Group for all messages and updates related to service request #789."
  }
  ```

  **Example JSON Response (Success 201 Created):**
  ```json
  {
    "id": "notif_group_01HABCDEFGHJKLMNPQRSTWXYZ",
    "name": "Service Request #789 Discussions",
    "description": "Group for all messages and updates related to service request #789.",
    "created_at": "2024-05-29T11:00:00Z",
    "updated_at": "2024-05-29T11:00:00Z"
  }
  ```

---

#### XIII.4. Update a Notification Group
- **Method:** `PUT` or `PATCH`
- **Endpoint:** `notification-groups/{group_id}/`
- **Description:** Updates an existing notification group. `PUT` requires all fields, `PATCH` allows partial updates.
- **Permissions:** Admin User

  **Example cURL Request (PATCH):**
  ```bash
  curl -X PATCH "https://yourdomain.com/api/v1/notification-groups/notif_group_01HABCDEFGHJKLMNPQRSTWXYZ/" \
    -H "Authorization: Bearer <admin_access_token>" \
    -H "Content-Type: application/json" \
    -d '{
      "description": "Updated description for service request #789 discussions."
    }'
  ```

  **Example JSON Request Body (PATCH):**
  ```json
  {
    "description": "Updated description for service request #789 discussions."
  }
  ```

  **Example JSON Response (Success 200 OK):**
  ```json
  {
    "id": "notif_group_01HABCDEFGHJKLMNPQRSTWXYZ",
    "name": "Service Request #789 Discussions",
    "description": "Updated description for service request #789 discussions.",
    "created_at": "2024-05-29T11:00:00Z",
    "updated_at": "2024-05-29T11:05:00Z"
  }
  ```

---

#### XIII.5. Delete a Notification Group
- **Method:** `DELETE`
- **Endpoint:** `notification-groups/{group_id}/`
- **Description:** Deletes a specific notification group. Note that deleting a group might require handling associated notifications (e.g., setting their `group` field to null).
- **Permissions:** Admin User

  **Example cURL Request:**
  ```bash
  curl -X DELETE "https://yourdomain.com/api/v1/notification-groups/notif_group_01HABCDEFGHJKLMNPQRSTWXYZ/" \
    -H "Authorization: Bearer <admin_access_token>"
  ```

  **Example JSON Response (Success 204 No Content):**
  (No body content is returned on successful deletion)

---

## XVI. API Documentation Endpoints
Base Path: `/` (or as configured by your Django REST Framework documentation settings)

This section lists the endpoints where the API documentation itself (e.g., Swagger UI, ReDoc, OpenAPI schema) can be accessed. These are typically auto-generated by libraries like `drf-yasg` or `drf-spectacular`.

---

#### XVI.1. Swagger UI
- **Method:** `GET`
- **Endpoint:** `swagger/` (or `api/docs/swagger/`, `docs/`)
- **Description:** Provides an interactive API documentation UI (Swagger/OpenAPI UI) where developers can explore endpoints, view models, and test API calls directly in the browser.
- **Permissions:** Public or Restricted (configurable, often public in development/staging)

  **Example Access (Browser):**
  Navigate to `https://yourdomain.com/swagger/`

  **Expected Outcome:**
  The Swagger UI interface loads, displaying all documented API endpoints, their methods, parameters, request/response bodies, and authentication mechanisms.

---

#### XVI.2. ReDoc UI
- **Method:** `GET`
- **Endpoint:** `redoc/` (or `api/docs/redoc/`)
- **Description:** Provides an alternative, often more streamlined, API documentation UI (ReDoc).
- **Permissions:** Public or Restricted

  **Example Access (Browser):**
  Navigate to `https://yourdomain.com/redoc/`

  **Expected Outcome:**
  The ReDoc UI interface loads, presenting the API documentation in a clean, three-pane layout.

---

#### XVI.3. OpenAPI Schema File
- **Method:** `GET`
- **Endpoint:** `openapi.yaml` or `openapi.json` (or `swagger.yaml`, `swagger.json`)
  - Common paths: `/openapi?format=openapi-json`, `/openapi?format=openapi-yaml`, `/swagger.json`, `/swagger.yaml`
- **Description:** Provides the raw OpenAPI specification document (in YAML or JSON format). This file can be used by various tools for generating client SDKs, further documentation, or for API contract testing.
- **Permissions:** Public or Restricted

  **Example cURL Request (for JSON):**
  ```bash
  curl -X GET "https://yourdomain.com/openapi.json" -o prbal_openapi_schema.json
  ```
  *(Adjust the endpoint based on your specific `drf-yasg` or `drf-spectacular` configuration)*

  **Example cURL Request (for YAML):**
  ```bash
  curl -X GET "https://yourdomain.com/openapi.yaml" -o prbal_openapi_schema.yaml
  ```

  **Expected Outcome:**
  The command downloads the OpenAPI schema file. The content will be a structured JSON or YAML document describing the entire API.

  **Example JSON Snippet (Illustrative):**
  ```json
  {
    "openapi": "3.0.2",
    "info": {
      "title": "Prbal API",
      "version": "v1",
      "description": "API for Prbal Service Marketplace"
    },
    "paths": {
      "/api/v1/users/": {
        "get": {
          "operationId": "listUsers",
          "summary": "List all users",
          // ... more details
        },
        "post": {
          "operationId": "createUser",
          // ...
        }
      }
      // ... many more paths and components
    }
  }
  ```

---
*Note: CRUD typically implies GET (list, retrieve), POST (create), PUT/PATCH (update), DELETE operations.*
*Specific HTTP methods for CRUD operations depend on the ViewSet implementation in Django Rest Framework.*
