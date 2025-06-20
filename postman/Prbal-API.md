# Prbal API Documentation

This document outlines the various API endpoints available in the Prbal backend system, derived from the project's codebase and supporting documentation.

## Table of Contents

- [Prbal API Documentation](#prbal-api-documentation)
  - [Table of Contents](#table-of-contents)
  - [Authentication](#authentication)
    - [User Registration](#user-registration)
      - [Generic User Registration](#generic-user-registration)
      - [Customer Specific Registration](#customer-specific-registration)
      - [Provider Specific Registration](#provider-specific-registration)
    - [Generic User Registration](#generic-user-registration-1)
      - [Admin Specific Registration](#admin-specific-registration)
    - [User Logout](#user-logout)
    - [Access Token Management](#access-token-management)
      - [List User's Access Tokens](#list-users-access-tokens)
      - [Revoke Specific Access Token](#revoke-specific-access-token)
      - [Refresh JWT Access Token](#refresh-jwt-access-token)
  - [User Management](#user-management)
    - [Generic User Endpoints](#generic-user-endpoints)
      - [Manage Own Profile](#manage-own-profile)
      - [Upload/Change Own Avatar](#uploadchange-own-avatar)
      - [Deactivate Own Account](#deactivate-own-account)
      - [Change Own Password](#change-own-password)
    - [Customer Specific Endpoints](#customer-specific-endpoints)
      - [Manage Own Customer Profile](#manage-own-customer-profile)
    - [Provider Specific Endpoints](#provider-specific-endpoints)
      - [Manage Own Provider Profile](#manage-own-provider-profile)
    - [Admin Specific Endpoints](#admin-specific-endpoints)
      - [Manage Own Admin Profile](#manage-own-admin-profile)
    - [User Search](#user-search)
      - [General User Search](#general-user-search)
      - [User Search by Phone Number](#user-search-by-phone-number)
  - [Services and Service Requests](#services-and-service-requests)
    - [Public Service and Category Endpoints](#public-service-and-category-endpoints)
    - [Provider Service Management](#provider-service-management)
      - [Create Service (Provider)](#create-service-provider)
      - [List Own Services (Provider)](#list-own-services-provider)
      - [Retrieve Own Service (Provider)](#retrieve-own-service-provider)
      - [Update Own Service (Provider)](#update-own-service-provider)
      - [Delete Own Service (Provider)](#delete-own-service-provider)
    - [Public Service Request Endpoints](#public-service-request-endpoints)
      - [Submit Public Service Request](#submit-public-service-request)
      - [View Public Service Request Details](#view-public-service-request-details)
    - [Service Requests (Customer)](#service-requests-customer)
      - [Create Service Request (Customer)](#create-service-request-customer)
      - [List Own Service Requests (Customer)](#list-own-service-requests-customer)
      - [Retrieve Own Service Request (Customer)](#retrieve-own-service-request-customer)
      - [Update Own Service Request (Customer)](#update-own-service-request-customer)
      - [Cancel Own Service Request (Customer)](#cancel-own-service-request-customer)
    - [Service Requests (Admin)](#service-requests-admin)
      - [List All Service Requests (Admin)](#list-all-service-requests-admin)
      - [Retrieve Service Request Details (Admin)](#retrieve-service-request-details-admin)
  - [Products](#products)
    - [Product Categories](#product-categories)
    - [Products (Individual)](#products-individual)
  - [Bids](#bids)
    - [Provider Bidding Actions](#provider-bidding-actions)
    - [Bids - Customer View](#bids---customer-view)
    - [Bids - Admin View](#bids---admin-view)
  - [Bookings](#bookings)
    - [Create Booking](#create-booking)
    - [View Booking Details](#view-booking-details)
    - [Update Booking Status](#update-booking-status)
    - [List Customer Bookings](#list-customer-bookings)
    - [List Provider Bookings](#list-provider-bookings)
    - [List Admin Bookings](#list-admin-bookings)
  - [Calendar Integration](#calendar-integration)
  - [Payment Processing](#payment-processing)
    - [Create Payment Intent](#create-payment-intent)
    - [Confirm Payment](#confirm-payment)
    - [Retrieve Payment Details](#retrieve-payment-details)
    - [List Payments (Customer/Provider/Admin)](#list-payments-customerprovideradmin)
    - [Issue Refund (Admin)](#issue-refund-admin)
    - [Payment Gateway Accounts (Provider)](#payment-gateway-accounts-provider)
      - [Link Payment Gateway Account](#link-payment-gateway-account)
      - [View Payment Gateway Account Details](#view-payment-gateway-account-details)
      - [Update Payment Gateway Account](#update-payment-gateway-account)
      - [Remove Payment Gateway Account](#remove-payment-gateway-account)
    - [Payouts (Provider/Admin)](#payouts-provideradmin)
      - [Request Payout (Provider)](#request-payout-provider)
      - [View Payout History (Provider/Admin)](#view-payout-history-provideradmin)
      - [Process Payouts (Admin)](#process-payouts-admin)
      - [View Payout Settings (Provider/Admin)](#view-payout-settings-provideradmin)
  - [Messaging](#messaging)
    - [Message Threads](#message-threads)
      - [Create Message Thread](#create-message-thread)
      - [List User Message Threads](#list-user-message-threads)
      - [View Message Thread Details](#view-message-thread-details)
      - [Archive Message Thread](#archive-message-thread)
      - [Mark Thread as Read/Unread](#mark-thread-as-readunread)
    - [Individual Messages](#individual-messages)
      - [Send Message in Thread](#send-message-in-thread)
      - [List Messages in Thread](#list-messages-in-thread)
      - [Edit Message](#edit-message)
      - [Delete Message](#delete-message)
  - [Notifications (HTTP)](#notifications-http)
    - [List User Notifications](#list-user-notifications)
    - [Mark Notification as Read](#mark-notification-as-read)
    - [Mark All Notifications as Read](#mark-all-notifications-as-read)
    - [Delete Notification](#delete-notification)
    - [Notification Settings](#notification-settings)
      - [Get Notification Settings](#get-notification-settings)
      - [Update Notification Settings](#update-notification-settings)
  - [AI Suggestions and Feedback](#ai-suggestions-and-feedback)
    - [AI Suggestions](#ai-suggestions)
      - [Get AI Suggestions for Service Request](#get-ai-suggestions-for-service-request)
      - [Get AI Suggestions for Pricing](#get-ai-suggestions-for-pricing)
      - [Get AI Suggestions for Descriptions](#get-ai-suggestions-for-descriptions)
    - [AI Feedback Logs](#ai-feedback-logs)
      - [Submit Feedback on AI Suggestion](#submit-feedback-on-ai-suggestion)
      - [List AI Feedback Logs (Admin)](#list-ai-feedback-logs-admin)
  - [Verifications (User Identity, etc.)](#verifications-user-identity-etc)
    - [Submit Verification Document](#submit-verification-document)
    - [Check Verification Status](#check-verification-status)
    - [Admin Verification Actions](#admin-verification-actions)
      - [List Pending Verifications (Admin)](#list-pending-verifications-admin)
      - [Approve/Reject Verification (Admin)](#approvereject-verification-admin)
    - [Submit Review for a Service/Provider](#submit-review-for-a-serviceprovider)
      - [Generate Financial Report](#generate-financial-report)
    - [Admin User Management](#admin-user-management)
      - [List All Users (Admin)](#list-all-users-admin)
      - [View User Details (Admin)](#view-user-details-admin)
      - [Activate/Deactivate User (Admin)](#activatedeactivate-user-admin)
      - [Assign User Roles (Admin)](#assign-user-roles-admin)
    - [Admin Service Management](#admin-service-management)
      - [List All Services (Admin)](#list-all-services-admin)
      - [Update Service Details (Admin)](#update-service-details-admin)
      - [Manage Service Categories (Admin)](#manage-service-categories-admin)
  - [WebSocket APIs](#websocket-apis)
    - [Real-time Notifications (WebSocket)](#real-time-notifications-websocket)
    - [Real-time Messaging (WebSocket)](#real-time-messaging-websocket)
    - [Real-time Booking Updates (WebSocket)](#real-time-booking-updates-websocket)
  - [Health Checks](#health-checks)
    - [System Health Endpoint](#system-health-endpoint)
    - [Database Health Endpoint](#database-health-endpoint)
    - [Service Dependency Health Endpoint](#service-dependency-health-endpoint)
  - [Metrics](#metrics)
    - [Prometheus Metrics Endpoint](#prometheus-metrics-endpoint)

## Authentication

### User Registration

#### Generic User Registration

Registers a new user in the system. If no specific user type is provided, it defaults to creating a 'customer' account.

**Endpoint:** `POST /api/users/register` (This is an assumption, please verify with your Python backend implementation)

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890"
}
```

**`curl` Command:**

```bash
curl -X POST http://localhost:8000/api/users/register \
-H "Content-Type: application/json" \
-H "Accept: application/json" \
-d '{
  "email": "user@example.com",
  "password": "securePassword123",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890"
}'
```

**Possible Output Response (Success 201 Created):**

```json
{
  "message": "User registered successfully. Please check your email to verify your account.",
  "data": {
    "user_id": "uuid-generated-by-server",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890",
    "user_type": "customer",
    "is_active": true,
    "is_verified": false,
    "created_at": "YYYY-MM-DDTHH:MM:SSZ",
    "updated_at": "YYYY-MM-DDTHH:MM:SSZ"
  }
}
```

**Possible Output Response (Error 400 Bad Request - Validation Error, e.g., email exists):**

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Input validation failed.",
    "details": [
      {
        "field": "email",
        "issue": "User with this email already exists."
      }
    ]
  }
}
```

#### Customer Specific Registration

Registers a new user with a 'customer' role, including customer-specific profile information.

**Endpoint:** `POST /api/users/register/customer`

**Request Body:**

```json
{
  "email": "customer@example.com",
  "password": "securePassword123",
  "first_name": "Jane",
  "last_name": "Smith",
  "phone_number": "+1987654321",
  "address": {
    "street": "123 Customer Lane",
    "city": "Clientville",
    "state": "CA",
    "zip_code": "90210",
    "country": "USA"
  }
}
```

**`curl` Command:**

```bash
curl -X POST http://localhost:8000/api/users/register/customer \
-H "Content-Type: application/json" \
-H "Accept: application/json" \
-d '{
  "email": "customer@example.com",
  "password": "securePassword123",
  "first_name": "Jane",
  "last_name": "Smith",
  "phone_number": "+1987654321",
  "address": {
    "street": "123 Customer Lane",
    "city": "Clientville",
    "state": "CA",
    "zip_code": "90210",
    "country": "USA"
  }
}'
```

#### Provider Specific Registration

Registers a new user with a 'provider' role, including provider-specific details like company name and service categories.

**Endpoint:** `POST /api/users/register/provider`

**Request Body:**

```json
{
  "email": "provider@example.com",
  "password": "securePasswordProvider123",
  "first_name": "Service",
  "last_name": "Pro",
  "phone_number": "+1555123456",
  "company_name": "Pro Services Ltd.",
  "service_categories": ["plumbing", "electrical"],
  "business_license_id": "BIZLICENSE789",
  "address": {
    "street": "456 Provider Ave",
    "city": "Workville",
    "state": "NY",
    "zip_code": "10001",
    "country": "USA"
  }
}
```

**`curl` Command:**

```bash
curl -X POST http://localhost:8000/api/users/register/provider \
-H "Content-Type: application/json" \
-H "Accept: application/json" \
-d '{
  "email": "provider@example.com",
  "password": "securePasswordProvider123",
  "first_name": "Service",
  "last_name": "Pro",
  "phone_number": "+1555123456",
  "company_name": "Pro Services Ltd.",
  "service_categories": ["plumbing", "electrical"],
  "business_license_id": "BIZLICENSE789",
  "address": {
    "street": "456 Provider Ave",
    "city": "Workville",
    "state": "NY",
    "zip_code": "10001",
    "country": "USA"
  }
}'
```

**Possible Output Response (Success 201 Created):**

```json
{
  "message": "Admin user registered successfully",
  "data": {
    "user_id": "uuid-generated-by-server",
    "email": "provider@example.com",
    "first_name": "Service",
    "last_name": "Pro",
    "phone_number": "+1555123456",
    "user_type": "provider",
    "is_active": true,
    "is_verified": false,
    "company_name": "Pro Services Ltd.",
    "service_categories": ["plumbing", "electrical"],
    "business_license_id": "BIZLICENSE789",
    "address": {
      "street": "456 Provider Ave",
      "city": "Workville",
      "state": "NY",
      "zip_code": "10001",
      "country": "USA"
    },
    "created_at": "YYYY-MM-DDTHH:MM:SSZ",
    "updated_at": "YYYY-MM-DDTHH:MM:SSZ"
  }
}
```

### Generic User Registration

(Section content to be added)

---

#### Admin Specific Registration

Registers a new admin user in the system. This typically requires elevated permissions (e.g., an existing admin or super admin).  

**Endpoint:** `POST /api/admins/register` (Assumption: Verify with backend implementation)

**Request Body:**

```json
{
  "username": "new_admin_user",
  "email": "admin@example.com",
  "password": "securePassword123",
  "first_name": "Admin",
  "last_name": "User",
  "phone_number": "1234567890",
  "is_staff": true,
  "is_superuser": false
}
```

**`curl` Command:**

```bash
curl -X POST http://localhost:8000/api/admins/register \
-H "Content-Type: application/json" \
-H "Authorization: Bearer <SUPER_ADMIN_ACCESS_TOKEN>" \  # Assuming this route is protected
-d '{
  "username": "new_admin_user",
  "email": "admin@example.com",
  "password": "securePassword123",
  "first_name": "Admin",
  "last_name": "User",
  "phone_number": "1234567890",
  "is_staff": true,
  "is_superuser": false
}'
```

**Possible Output Response (201 Created):**

```json
{
  "id": 3,
  "username": "new_admin_user",
  "email": "admin@example.com",
  "first_name": "Admin",
  "last_name": "User",
  "user_type": "admin",
  "is_staff": true,
  "is_superuser": false,
  "profile": {
    // Admin profile details if any
  }
}
```

**Error Response (400 Bad Request - Invalid Data):**

```json
{
  "detail": {
    "email": [
      "admin with this email already exists."
    ],
    "username": [
      "A user with that username already exists."
    ]
    // Or other field-specific errors
  }
}
```

**Error Response (401 Unauthorized / 403 Forbidden):**

```json
{
  "detail": "Authentication credentials were not provided."
  // or "You do not have permission to perform this action."
}
```

---

---

### User Logout

Logs out the currently authenticated user by invalidating their session or access token. Depending on the authentication mechanism (e.g., JWT with refresh tokens), this might involve blacklisting the token.

**Endpoint:** `POST /api/users/logout` (Assumption: Verify with backend implementation)

**Request Body:** (Usually empty, but depends on implementation. Some might accept a refresh token to invalidate.)

```json
{}
// Or for JWT with refresh token:
// {
//   "refresh_token": "<USER_REFRESH_TOKEN>"
// }
```

**`curl` Command:** ⚠️ (Verify and complete)

```bash
curl -X POST http://localhost:8000/api/users/logout \
-H "Authorization: Bearer <USER_ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-d '{}' # Or include refresh_token if applicable
```

**Possible Output Response (200 OK or 204 No Content):**

```json
// For 200 OK with a message:
{
  "message": "Successfully logged out."
}
// For 204 No Content, the response body will be empty.
```

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Error Response (400 Bad Request - e.g., if refresh token is invalid/required and not provided):**

```json
{
  "detail": "Invalid refresh token."
}
```

---

---

### Access Token Management

Endpoints related to managing user access tokens, such as listing active tokens, revoking them, or refreshing expired ones.

#### List User's Access Tokens

Retrieves a list of active access tokens or sessions for the currently authenticated user. This is useful for users to see where their account is currently logged in and to manage these sessions.

**Endpoint:** `GET /api/users/tokens` (Assumption: Verify with backend implementation)

**Request Body:** (None for GET request)

**`curl` Command:** ⚠️ (Verify and complete)

```bash
curl -X GET http://localhost:8000/api/users/tokens \
-H "Authorization: Bearer <USER_ACCESS_TOKEN>"
```

**Possible Output Response (200 OK):**

```json
{
  "tokens": [
    {
      "id": "token_id_1",
      "device_info": "Chrome on Windows 10",
      "ip_address": "192.168.1.10",
      "last_used_at": "YYYY-MM-DDTHH:MM:SSZ",
      "created_at": "YYYY-MM-DDTHH:MM:SSZ"
    },
    {
      "id": "token_id_2",
      "device_info": "Prbal App on Android",
      "ip_address": "10.0.0.5",
      "last_used_at": "YYYY-MM-DDTHH:MM:SSZ",
      "created_at": "YYYY-MM-DDTHH:MM:SSZ"
    }
    // Potentially other active tokens/sessions
  ],
  "pagination": {
    "count": 2,
    "next": null,
    "previous": null
  }
}
```

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

---

#### Revoke Specific Access Token

Allows a user to revoke a specific access token or session, effectively logging out that particular session. This is typically done by providing the ID of the token to be revoked.

**Endpoint:** `DELETE /api/users/tokens/{token_id}` (Assumption: Verify with backend implementation)

**Path Parameters:**

- `token_id` (string, required): The unique identifier of the access token/session to be revoked.

**Request Body:** (None for DELETE request)

**`curl` Command:** ⚠️ (Verify and complete)

```bash
curl -X DELETE http://localhost:8000/api/users/tokens/token_id_to_revoke \
-H "Authorization: Bearer <USER_ACCESS_TOKEN>"
```

**Possible Output Response (204 No Content):**
(Response body will be empty, indicating successful revocation.)

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Error Response (403 Forbidden):**
(If the user tries to revoke a token that doesn't belong to them, or if the token_id is malformed/not found and the system distinguishes this from a general auth error)

```json
{
  "detail": "You do not have permission to perform this action on this token."
  // or "Token not found."
}
```

**Error Response (404 Not Found):**
(If the specified `token_id` does not exist.)

```json
{
  "detail": "Not found."
}
```

---

---

#### Refresh JWT Access Token

Allows a client to obtain a new JWT access token using a valid refresh token. This is part of the standard OAuth 2.0 / JWT authentication flow to maintain user sessions without requiring frequent re-logins.

**Endpoint:** `POST /api/token/refresh/` (Common endpoint, verify with backend implementation, e.g., Django Simple JWT uses this)

**Request Body:**

```json
{
  "refresh": "<USER_REFRESH_TOKEN>"
}
```

**`curl` Command:** ⚠️ (Verify and complete)

```bash
curl -X POST http://localhost:8000/api/token/refresh/ \
-H "Content-Type: application/json" \
-d '{
  "refresh": "<USER_REFRESH_TOKEN>"
}'
```

**Possible Output Response (200 OK):**

```json
{
  "access": "<NEW_ACCESS_TOKEN>",
  "refresh": "<MAYBE_NEW_REFRESH_TOKEN>" // Some implementations might also return a new refresh token (rolling refresh tokens)
}
```

**Error Response (401 Unauthorized / 400 Bad Request - Invalid Refresh Token):**
(The specific error code might vary; 401 is common for invalid/expired tokens)

```json
{
  "detail": "Token is invalid or expired",
  "code": "token_not_valid"
  // Or for a bad request format:
  // "refresh": ["This field is required."]
}
```

---

## User Management

Endpoints for managing user accounts, profiles, and related data. This section is divided based on user roles where applicable (generic, customer, provider, admin).

### Generic User Endpoints

Endpoints applicable to any authenticated user, regardless of their specific role (customer, provider, or admin), for managing their own basic profile information.

#### Manage Own Profile

Allows an authenticated user to retrieve and update their own profile information. This typically includes details like name, email, phone number, and other general user attributes not specific to a role like customer or provider.

**Endpoints:**

- `GET /api/users/me/profile/` (Retrieve own profile)
- `PUT /api/users/me/profile/` (Update own profile - full update)
- `PATCH /api/users/me/profile/` (Update own profile - partial update)

(Assumption: Verify these common RESTful patterns with backend implementation. Django Rest Framework often uses `/api/users/me/` for the authenticated user.)

**Request Body (for PUT/PATCH):**

```json
{
  "first_name": "UpdatedFirstName",
  "last_name": "UpdatedLastName",
  "email": "user_updated@example.com",
  "phone_number": "+19876543210",
  // Other updatable generic profile fields
  "bio": "An updated bio about myself.",
  "date_of_birth": "YYYY-MM-DD", // Optional
  "gender": "other" // Optional, e.g., male, female, other, prefer_not_to_say
}
```

**`curl` Commands:** ⚠️ (Verify and complete)

**Retrieve Profile:**

```bash
curl -X GET http://localhost:8000/api/users/me/profile/ \
-H "Authorization: Bearer <USER_ACCESS_TOKEN>"
```

**Update Profile (PUT - Full Update):**

```bash
curl -X PUT http://localhost:8000/api/users/me/profile/ \
-H "Authorization: Bearer <USER_ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-d '{
  "first_name": "UpdatedFirstName",
  "last_name": "UpdatedLastName",
  "email": "user_updated@example.com",
  "phone_number": "+19876543210",
  "bio": "An updated bio for full update.",
  "date_of_birth": "1990-01-01",
  "gender": "male"
}'
```

**Update Profile (PATCH - Partial Update):**

```bash
curl -X PATCH http://localhost:8000/api/users/me/profile/ \
-H "Authorization: Bearer <USER_ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-d '{
  "phone_number": "+112233445566",
  "bio": "Just updating my bio partially."
}'
```

**Possible Output Response (200 OK for GET, PUT, PATCH):**

```json
{
  "id": 1, // User ID
  "username": "currentuser",
  "email": "user_updated@example.com",
  "first_name": "UpdatedFirstName",
  "last_name": "UpdatedLastName",
  "phone_number": "+112233445566", // Reflects PATCH if that was the last op
  "user_type": "customer", // Or provider, admin
  "profile": {
    "bio": "Just updating my bio partially.",
    "date_of_birth": "1990-01-01", 
    "gender": "male",
    "avatar_url": "http://example.com/path/to/avatar.jpg" // If avatar is part of generic profile
    // Other generic profile fields
  }
}
```

**Error Response (400 Bad Request - Validation Error for PUT/PATCH):**

```json
{
  "email": [
    "Enter a valid email address."
  ],
  "phone_number": [
    "Invalid phone number format."
  ]
  // Other field-specific validation errors
}
```

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

#### Upload/Change Own Avatar

Allows an authenticated user to upload a new avatar image or change their existing one. This typically involves a `POST` or `PUT` request with `multipart/form-data`.

**Endpoints:**

- `POST /api/users/me/avatar/` (Upload/Change avatar)
- `DELETE /api/users/me/avatar/` (Remove avatar - Optional)

(Assumption: Verify with backend. The endpoint might be part of the profile update, e.g., `PATCH /api/users/me/profile/` with a file field, or a dedicated endpoint as shown.)

**Request Body (for POST/PUT - multipart/form-data):**

- `avatar`: The image file (e.g., JPEG, PNG).

**`curl` Commands:** ⚠️ (Verify and complete)

**Upload/Change Avatar:**

```bash
# Ensure 'avatar.jpg' exists in the directory where you run curl
curl -X POST http://localhost:8000/api/users/me/avatar/ \
-H "Authorization: Bearer <USER_ACCESS_TOKEN>" \
-H "Content-Type: multipart/form-data" \
-F "avatar=@avatar.jpg"
```

**Remove Avatar (if supported):**

```bash
curl -X DELETE http://localhost:8000/api/users/me/avatar/ \
-H "Authorization: Bearer <USER_ACCESS_TOKEN>"
```

**Possible Output Response (200 OK or 201 Created for POST/PUT):**

```json
{
  "message": "Avatar updated successfully.",
  "avatar_url": "http://localhost:8000/media/avatars/user_1/avatar.jpg"
  // Or the full user profile object might be returned:
  // {
  //   "id": 1,
  //   "username": "currentuser",
  //   "profile": {
  //     "avatar_url": "http://localhost:8000/media/avatars/user_1/avatar.jpg"
  //     // ... other profile fields
  //   }
  // }
}
```

**Possible Output Response (204 No Content for DELETE):**
(Response body will be empty, indicating successful removal.)

**Error Response (400 Bad Request - e.g., invalid file type, file too large):**

```json
{
  "avatar": [
    "Invalid image format. Only JPG and PNG are allowed.",
    "File size exceeds the maximum limit of 2MB."
  ]
}
```

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

---

#### Deactivate Own Account

Allows an authenticated user to deactivate their own account. This is typically a `POST` or `DELETE` request. Deactivation might be a soft delete (marking the account inactive) rather than a hard delete (permanently removing data).

**Endpoint:**

- `POST /api/users/me/deactivate/` (Deactivate own account)
  *(Alternatively, `DELETE /api/users/me/` could be used, but `POST` to a specific `deactivate` endpoint is often preferred for clarity and to allow for a request body if needed, e.g., for password confirmation.)*

(Assumption: Verify with backend. The exact method and endpoint, and whether password confirmation is required, should be confirmed.)

**Request Body (Optional, e.g., if password confirmation is required):**

```json
{
  "password": "<USER_CURRENT_PASSWORD>"
}
```

**`curl` Commands:** ⚠️ (Verify and complete)

**Deactivate Account (without password confirmation):**

```bash
curl -X POST http://localhost:8000/api/users/me/deactivate/ \
-H "Authorization: Bearer <USER_ACCESS_TOKEN>"
```

**Deactivate Account (with password confirmation):**

```bash
curl -X POST http://localhost:8000/api/users/me/deactivate/ \
-H "Authorization: Bearer <USER_ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-d '{
  "password": "<USER_CURRENT_PASSWORD>"
}'
```

**Possible Output Response (200 OK or 204 No Content):**

```json
{
  "message": "Account deactivated successfully."
}
```

*(If 204 No Content, the response body will be empty.)*

**Error Response (400 Bad Request - e.g., incorrect password):**

```json
{
  "password": [
    "Incorrect password."
  ]
}
```

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Error Response (403 Forbidden - e.g., if account has active subscriptions or pending actions):**

```json
{
  "detail": "Account cannot be deactivated due to pending actions or active subscriptions. Please resolve these first."
}
```

---

---

#### Change Own Password

Allows an authenticated user to change their own password. This typically requires the user to provide their current password and the new password (often with confirmation).

**Endpoint:**

- `POST /api/users/me/change-password/`
  *(Common endpoint for password changes. Some systems might use `PUT` or `PATCH` to `/api/users/me/` with password fields, but a dedicated endpoint is clearer.)*

(Assumption: Verify with backend. Django's built-in views often use a specific endpoint like `/auth/password/change/` or similar, often requiring `rest_framework.authtoken` or `dj_rest_auth` patterns.)

**Request Body:**

```json
{
  "current_password": "<USER_CURRENT_PASSWORD>",
  "new_password1": "<NEW_PASSWORD>",
  "new_password2": "<NEW_PASSWORD_CONFIRMATION>"
}
```

*(Field names like `new_password1` and `new_password2` are common in Django for confirmation.)*

**`curl` Command:** ⚠️ (Verify and complete)

```bash
curl -X POST http://localhost:8000/api/users/me/change-password/ \
-H "Authorization: Bearer <USER_ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-d '{
  "current_password": "oldSecurePassword123",
  "new_password1": "newSecurePassword456",
  "new_password2": "newSecurePassword456"
}'
```

**Possible Output Response (200 OK):**

```json
{
  "detail": "Password has been changed successfully."
  // Some implementations might return an empty 200 OK or 204 No Content
}
```

**Error Response (400 Bad Request - e.g., passwords don't match, new password too weak, current password incorrect):**

```json
{
  "current_password": [
    "Incorrect current password."
  ],
  "new_password2": [
    "The two password fields didn't match.",
    "This password is too common."
    // Other password validation errors
  ]
}
```

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

### Customer Specific Endpoints

Endpoints tailored for users with the 'customer' role, allowing them to manage their customer-specific data and interactions.

---

#### Manage Own Customer Profile

Allows an authenticated customer to retrieve and update their customer-specific profile information. This is in addition to the generic user profile and might include things like addresses, preferences, loyalty status, etc.

**Endpoints:**

- `GET /api/customers/me/profile/` (Retrieve own customer profile)
- `PUT /api/customers/me/profile/` (Update own customer profile - full update)
- `PATCH /api/customers/me/profile/` (Update own customer profile - partial update)

(Assumption: Verify with backend. The endpoint `/api/customers/me/` is a common pattern for role-specific data for the authenticated user.)

**Request Body (for PUT/PATCH):**

```json
{
  "default_shipping_address": {
    "street": "123 Customer Lane",
    "city": "Clientville",
    "state": "CS",
    "zip_code": "12345",
    "country": "USA"
  },
  "payment_methods": [
    {
      "type": "card",
      "last4": "4242",
      "expiry_month": 12,
      "expiry_year": 2025,
      "is_default": true
    }
  ],
  "preferences": {
    "newsletter_subscription": true,
    "communication_channel": "email"
  },
  "loyalty_id": "CUST-LOYAL-XYZ123" // Example field
}
```

**`curl` Commands:** ⚠️ (Verify and complete)

**Retrieve Customer Profile:**

```bash
curl -X GET http://localhost:8000/api/customers/me/profile/ \
-H "Authorization: Bearer <USER_ACCESS_TOKEN>"
```

**Update Customer Profile (PUT - Full Update):**

```bash
curl -X PUT http://localhost:8000/api/customers/me/profile/ \
-H "Authorization: Bearer <USER_ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-d '{
  "default_shipping_address": {
    "street": "456 New Address St",
    "city": "UpdatedCity",
    "state": "US",
    "zip_code": "67890",
    "country": "USA"
  },
  "payment_methods": [], // Example: Clearing payment methods
  "preferences": {
    "newsletter_subscription": false,
    "communication_channel": "sms"
  },
  "loyalty_id": "CUST-LOYAL-ABC789"
}'
```

**Update Customer Profile (PATCH - Partial Update):**

```bash
curl -X PATCH http://localhost:8000/api/customers/me/profile/ \
-H "Authorization: Bearer <USER_ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-d '{
  "preferences": {
    "newsletter_subscription": true
  }
}'
```

**Possible Output Response (200 OK for GET, PUT, PATCH):**

```json
{
  "user_id": 1, // Link to the generic user ID
  "customer_id": "cust_abc123xyz", // Specific customer identifier
  "default_shipping_address": {
    "street": "123 Customer Lane", // Or "456 New Address St" if PUT was last
    "city": "Clientville",
    "state": "CS",
    "zip_code": "12345",
    "country": "USA"
  },
  "payment_methods": [
    // ... list of payment methods ...
  ],
  "preferences": {
    "newsletter_subscription": true, // Reflects PATCH if that was the last op
    "communication_channel": "email" // Or "sms" if PUT was last
  },
  "loyalty_id": "CUST-LOYAL-XYZ123",
  "date_joined_as_customer": "YYYY-MM-DDTHH:MM:SSZ"
}
```

**Error Response (400 Bad Request - Validation Error for PUT/PATCH):**

```json
{
  "default_shipping_address.zip_code": [
    "Invalid ZIP code format."
  ],
  "preferences.communication_channel": [
    "'invalid_channel' is not a valid choice."
  ]
}
```

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Error Response (403 Forbidden - User is not a customer):**

```json
{
  "detail": "You do not have permission to perform this action. User is not a customer."
}
```

---

### Provider Specific Endpoints

These endpoints are specific to users with the 'provider' role.

---

#### Manage Own Provider Profile

Allows a logged-in provider to retrieve and update their own profile information.

**1. Retrieve Own Provider Profile (GET)**

**`curl` Command:**

```bash
curl -X GET http://localhost:8000/api/users/profile/provider/me/ \
-H "Authorization: Bearer <PROVIDER_ACCESS_TOKEN>" \
-H "Accept: application/json"
```

**Possible Output Response (Success 200 OK):**

```json
{
  "user_id": "provider-uuid-123",
  "email": "provider@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890",
  "user_type": "provider",
  "profile": {
    "business_name": "John Doe Services",
    "bio": "Experienced provider offering top-notch services.",
    "website": "https://johndoe.example.com",
    "address": {
      "street": "123 Provider Street",
      "city": "Serviceville",
      "state": "CA",
      "zip_code": "90210",
      "country": "USA"
    },
    "service_categories": ["Plumbing", "Electrical"],
    "experience_years": 10,
    "portfolio_url": "https://portfolio.example.com/johndoe",
    "availability_schedule": {
      "monday": "09:00-17:00",
      "tuesday": "09:00-17:00",
      "wednesday": "09:00-17:00",
      "thursday": "09:00-17:00",
      "friday": "09:00-17:00",
      "saturday": "Closed",
      "sunday": "Closed"
    },
    "is_verified": true,
    "average_rating": 4.8,
    "avatar_url": "http://localhost:8000/media/avatars/provider-avatar.jpg"
  },
  "date_joined": "2023-01-15T10:30:00Z",
  "last_login": "2023-06-01T14:00:00Z"
}
```

**2. Update Own Provider Profile (PUT)**

**`curl` Command:**

```bash
curl -X PUT http://localhost:8000/api/users/profile/provider/me/ \
-H "Authorization: Bearer <PROVIDER_ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-d '{
  "first_name": "Jonathan",
  "last_name": "Doe",
  "phone_number": "+1234567891",
  "profile": {
    "business_name": "Jonathan Doe Premier Services",
    "bio": "Updated bio: Highly experienced provider offering a wide range of top-notch services.",
    "website": "https://jonathandoe.example.com",
    "address": {
      "street": "456 Provider Avenue",
      "city": "Servicetown",
      "state": "CA",
      "zip_code": "90211",
      "country": "USA"
    },
    "service_categories": ["Plumbing", "Electrical", "HVAC"],
    "experience_years": 12,
    "portfolio_url": "https://portfolio.example.com/jonathandoe",
    "availability_schedule": {
      "monday": "08:00-18:00",
      "tuesday": "08:00-18:00",
      "wednesday": "08:00-18:00",
      "thursday": "08:00-18:00",
      "friday": "08:00-16:00",
      "saturday": "10:00-14:00",
      "sunday": "Closed"
    }
  }
}'
```

**Possible Output Response (Success 200 OK):**

```json
{
  "user_id": "provider-uuid-123",
  "email": "provider@example.com",
  "first_name": "Jonathan",
  "last_name": "Doe",
  "phone_number": "+1234567891",
  "user_type": "provider",
  "profile": {
    "business_name": "Jonathan Doe Premier Services",
    "bio": "Updated bio: Highly experienced provider offering a wide range of top-notch services.",
    "website": "https://jonathandoe.example.com",
    "address": {
      "street": "456 Provider Avenue",
      "city": "Servicetown",
      "state": "CA",
      "zip_code": "90211",
      "country": "USA"
    },
    "service_categories": ["Plumbing", "Electrical", "HVAC"],
    "experience_years": 12,
    "portfolio_url": "https://portfolio.example.com/jonathandoe",
    "availability_schedule": {
      "monday": "08:00-18:00",
      "tuesday": "08:00-18:00",
      "wednesday": "08:00-18:00",
      "thursday": "08:00-18:00",
      "friday": "08:00-16:00",
      "saturday": "10:00-14:00",
      "sunday": "Closed"
    },
    "is_verified": true,
    "average_rating": 4.8,
    "avatar_url": "http://localhost:8000/media/avatars/provider-avatar.jpg"
  },
  "date_joined": "2023-01-15T10:30:00Z",
  "last_login": "2023-06-01T18:00:00Z"
}
```

**Common Error Responses:**

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Error Response (403 Forbidden - User is not a provider):**

```json
{
  "detail": "You do not have permission to perform this action. User is not a provider."
}
```

**Error Response (400 Bad Request - Invalid data for PUT):**

```json
{
  "phone_number": ["Enter a valid phone number."],
  "profile": {
    "experience_years": ["A valid integer is required."]
  }
}
```

---

### Admin Specific Endpoints

These endpoints are specific to users with the 'admin' role for managing their own profile information.

---

#### Manage Own Admin Profile

Allows a logged-in admin user to retrieve and update their own profile information.

**1. Retrieve Own Admin Profile (GET)**

**`curl` Command:**

```bash
curl -X GET http://localhost:8000/api/users/profile/admin/me/ \
-H "Authorization: Bearer <ADMIN_ACCESS_TOKEN>" \
-H "Accept: application/json"
```

**Possible Output Response (Success 200 OK):**

```json
{
  "user_id": "admin-uuid-789",
  "email": "admin@example.com",
  "first_name": "Super",
  "last_name": "User",
  "phone_number": "+19998887777",
  "user_type": "admin",
  "profile": {
    "department": "System Administration",
    "employee_id": "EMP001",
    "permissions_level": "superuser",
    "office_location": "Headquarters - Building A",
    "avatar_url": "http://localhost:8000/media/avatars/admin-avatar.jpg"
  },
  "is_staff": true,
  "is_superuser": true,
  "date_joined": "2022-01-01T09:00:00Z",
  "last_login": "2023-06-02T10:00:00Z"
}
```

**2. Update Own Admin Profile (PUT)**

**`curl` Command:**

```bash
curl -X PUT http://localhost:8000/api/users/profile/admin/me/ \
-H "Authorization: Bearer <ADMIN_ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-d '{
  "first_name": "System",
  "last_name": "Administrator",
  "phone_number": "+19998887766",
  "profile": {
    "department": "Global System Administration",
    "office_location": "Headquarters - Building B, Suite 100"
  }
}'
```

**Possible Output Response (Success 200 OK):**

```json
{
  "user_id": "admin-uuid-789",
  "email": "admin@example.com",
  "first_name": "System",
  "last_name": "Administrator",
  "phone_number": "+19998887766",
  "user_type": "admin",
  "profile": {
    "department": "Global System Administration",
    "employee_id": "EMP001",
    "permissions_level": "superuser",
    "office_location": "Headquarters - Building B, Suite 100",
    "avatar_url": "http://localhost:8000/media/avatars/admin-avatar.jpg"
  },
  "is_staff": true,
  "is_superuser": true,
  "date_joined": "2022-01-01T09:00:00Z",
  "last_login": "2023-06-02T10:05:00Z"
}
```

**Common Error Responses:**

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Error Response (403 Forbidden - User is not an admin):**

```json
{
  "detail": "You do not have permission to perform this action. User is not an admin or does not have sufficient privileges."
}
```

**Error Response (400 Bad Request - Invalid data for PUT):**

```json
{
  "phone_number": ["Enter a valid phone number."],
  "profile": {
    "department": ["This field may not be blank."]
  }
}
```

---

### User Search

Endpoints for searching users within the system. Access may be restricted based on user role (e.g., admin-only).

---

#### General User Search

Allows authorized users (e.g., admins) to search for users based on various criteria like name, email, or user type. Supports pagination.

**`curl` Command (Admin Example):**

```bash
curl -X GET 'http://localhost:8000/api/users/search/?query=john&user_type=customer&page=1&page_size=10' \
-H "Authorization: Bearer <ADMIN_ACCESS_TOKEN>" \
-H "Accept: application/json"
```

**Query Parameters:**

- `query` (string, optional): Search term (e.g., name, email fragment).
- `user_type` (string, optional): Filter by user type (e.g., `customer`, `provider`, `admin`).
- `is_active` (boolean, optional): Filter by active status.
- `page` (integer, optional): Page number for pagination (default: 1).
- `page_size` (integer, optional): Number of results per page (default: 10).

**Possible Output Response (Success 200 OK):**

```json
{
  "count": 150,
  "next": "http://localhost:8000/api/users/search/?query=john&user_type=customer&page=2&page_size=10",
  "previous": null,
  "results": [
    {
      "user_id": "customer-uuid-001",
      "username": "john.doe",
      "email": "john.doe@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "user_type": "customer",
      "is_active": true,
      "avatar_url": "http://localhost:8000/media/avatars/customer-john.jpg",
      "date_joined": "2023-02-10T11:00:00Z"
    },
    {
      "user_id": "provider-uuid-002",
      "username": "johnny.provider",
      "email": "johnny.provider@example.com",
      "first_name": "Johnny",
      "last_name": "Provider",
      "user_type": "provider",
      "is_active": true,
      "profile": {
        "business_name": "Johnny's Plumbing"
      },
      "avatar_url": "http://localhost:8000/media/avatars/provider-johnny.jpg",
      "date_joined": "2023-03-05T16:20:00Z"
    }
    // ... more results
  ]
}
```

**Possible Output Response (Success 200 OK - No Results):**

```json
{
  "count": 0,
  "next": null,
  "previous": null,
  "results": []
}
```

**Common Error Responses:**

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Error Response (403 Forbidden - Insufficient permissions):**

```json
{
  "detail": "You do not have permission to perform this action."
}
```

**Error Response (400 Bad Request - Invalid query parameters):**

```json
{
  "page_size": ["Must be a positive integer."],
  "user_type": ["\"unknown\" is not a valid choice."]
}
```

---

#### User Search by Phone Number

Allows authorized users (e.g., admins) to search for a specific user by their exact phone number.

**`curl` Command (Admin Example):**

```bash
curl -X GET 'http://localhost:8000/api/users/search/phone/?phone_number=%2B1234567890' \
-H "Authorization: Bearer <ADMIN_ACCESS_TOKEN>" \
-H "Accept: application/json"
```

**Query Parameters:**

- `phone_number` (string, required): The exact phone number to search for (URL-encoded if it contains special characters like '+').

**Possible Output Response (Success 200 OK - User Found):**

```json
{
  "user_id": "customer-uuid-003",
  "username": "jane.doe.phone",
  "email": "jane.doe.phone@example.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "phone_number": "+1234567890",
  "user_type": "customer",
  "is_active": true,
  "avatar_url": "http://localhost:8000/media/avatars/customer-jane.jpg",
  "date_joined": "2023-04-15T09:30:00Z"
}
```

**Possible Output Response (Success 404 Not Found - User with phone number does not exist):**

```json
{
  "detail": "User with the specified phone number not found."
}
```

**Common Error Responses:**

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Error Response (403 Forbidden - Insufficient permissions):**

```json
{
  "detail": "You do not have permission to perform this action."
}
```

**Error Response (400 Bad Request - Missing or invalid phone_number parameter):**

```json
{
  "phone_number": ["This field is required."]
}
```

Alternatively, for an invalid format:

```json
{
  "phone_number": ["Enter a valid phone number (e.g., +1234567890)."]
}
```

---

## Services and Service Requests

This section covers APIs related to service definitions, service categories, and the lifecycle of service requests made by customers.

---

### Public Service and Category Endpoints

These endpoints provide public access to view available services and service categories. No authentication is typically required.

---

### Provider Service Management

Endpoints for providers to manage their services, including creating, updating, listing, and deleting their service offerings. Requires provider authentication.

#### Create Service (Provider)

Allows a logged-in provider to create a new service offering.

**`curl` Command:**

```bash
curl -X POST http://localhost:8000/api/services/provider/ \
-H "Authorization: Bearer <PROVIDER_ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-d '{
  "title": "Professional House Cleaning",
  "description": "Detailed house cleaning services including dusting, vacuuming, and mopping. Eco-friendly products available upon request.",
  "category_id": "category-uuid-cleaning",
  "price_model": "hourly",
  "price": 25.50,
  "currency": "USD",
  "availability_details": "Available Mon-Fri, 9 AM to 5 PM. Weekends by special appointment.",
  "service_area_zip_codes": ["90210", "90211", "90212"],
  "tags": ["cleaning", "residential", "eco-friendly"],
  "is_active": true
}'
```

**Possible Output Response (Success 201 Created):**

```json
{
  "service_id": "service-uuid-newly-created",
  "provider_id": "provider-uuid-123",
  "title": "Professional House Cleaning",
  "description": "Detailed house cleaning services including dusting, vacuuming, and mopping. Eco-friendly products available upon request.",
  "category": {
    "category_id": "category-uuid-cleaning",
    "name": "Cleaning Services",
    "description": "Services related to cleaning residential and commercial properties."
  },
  "price_model": "hourly",
  "price": "25.50",
  "currency": "USD",
  "availability_details": "Available Mon-Fri, 9 AM to 5 PM. Weekends by special appointment.",
  "service_area_zip_codes": ["90210", "90211", "90212"],
  "tags": ["cleaning", "residential", "eco-friendly"],
  "is_active": true,
  "average_rating": null,
  "created_at": "2023-06-02T18:30:00Z",
  "updated_at": "2023-06-02T18:30:00Z"
}
```

**Common Error Responses:**

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Error Response (403 Forbidden - User is not a provider):**

```json
{
  "detail": "You do not have permission to perform this action. User is not a provider."
}
```

**Error Response (400 Bad Request - Invalid data):**

```json
{
  "title": ["This field may not be blank."],
  "category_id": ["Invalid pk \"invalid-category-uuid\" - object does not exist."],
  "price": ["A valid number is required."]
}
```

#### List Own Services (Provider)

Allows a logged-in provider to retrieve a list of their own service offerings. Supports pagination.

**`curl` Command:**

```bash
curl -X GET 'http://localhost:8000/api/services/provider/me/?page=1&page_size=5&is_active=true' \
-H "Authorization: Bearer <PROVIDER_ACCESS_TOKEN>" \
-H "Accept: application/json"
```

**Query Parameters:**

- `page` (integer, optional): Page number for pagination (default: 1).
- `page_size` (integer, optional): Number of results per page (default: 10).
- `is_active` (boolean, optional): Filter by active status.
- `category_id` (string, optional): Filter by category UUID.
- `q` (string, optional): Search term for service title or description.

**Possible Output Response (Success 200 OK):**

```json
{
  "count": 25,
  "next": "http://localhost:8000/api/services/provider/me/?page=2&page_size=5&is_active=true",
  "previous": null,
  "results": [
    {
      "service_id": "service-uuid-abc-123",
      "title": "Advanced Web Development",
      "category": {
        "category_id": "category-uuid-webdev",
        "name": "Web Development"
      },
      "price_model": "project-based",
      "price": "1500.00",
      "currency": "USD",
      "is_active": true,
      "average_rating": 4.9,
      "created_at": "2023-05-10T10:00:00Z",
      "updated_at": "2023-05-20T14:30:00Z"
    },
    {
      "service_id": "service-uuid-def-456",
      "title": "Graphic Design for Startups",
      "category": {
        "category_id": "category-uuid-design",
        "name": "Graphic Design"
      },
      "price_model": "fixed",
      "price": "500.00",
      "currency": "USD",
      "is_active": true,
      "average_rating": 4.7,
      "created_at": "2023-04-01T11:20:00Z",
      "updated_at": "2023-05-15T09:10:00Z"
    }
    // ... more results (up to page_size)
  ]
}
```

**Possible Output Response (Success 200 OK - No Services):**

```json
{
  "count": 0,
  "next": null,
  "previous": null,
  "results": []
}
```

**Common Error Responses:**

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Error Response (403 Forbidden - User is not a provider):**

```json
{
  "detail": "You do not have permission to perform this action. User is not a provider."
}
```

**Error Response (400 Bad Request - Invalid query parameters):**

```json
{
  "page_size": ["Must be a positive integer and not exceed 100."]
}
```

#### Retrieve Own Service (Provider)

Allows a logged-in provider to retrieve details for a specific service they own by its ID.

**`curl` Command:**

```bash
curl -X GET http://localhost:8000/api/services/provider/me/service-uuid-abc-123/ \
-H "Authorization: Bearer <PROVIDER_ACCESS_TOKEN>" \
-H "Accept: application/json"
```

**Path Parameters:**

- `service_id` (uuid, required): The UUID of the service to retrieve.

**Possible Output Response (Success 200 OK):**

```json
{
  "service_id": "service-uuid-abc-123",
  "provider_id": "provider-uuid-123",
  "title": "Advanced Web Development",
  "description": "End-to-end web development services using modern frameworks. Includes frontend, backend, and database design.",
  "category": {
    "category_id": "category-uuid-webdev",
    "name": "Web Development",
    "description": "Services related to creating and maintaining websites and web applications."
  },
  "price_model": "project-based",
  "price": "1500.00",
  "currency": "USD",
  "availability_details": "Available for new projects starting next month. Standard turnaround 2-4 weeks.",
  "service_area_zip_codes": ["90001", "90002", "90210"],
  "tags": ["web development", "full-stack", "react", "django"],
  "is_active": true,
  "average_rating": 4.9,
  "images": [
    {"image_url": "http://localhost:8000/media/services/webdev_portfolio1.jpg", "caption": "Portfolio Screenshot 1"},
    {"image_url": "http://localhost:8000/media/services/webdev_portfolio2.jpg", "caption": "Client Testimonial Graphic"}
  ],
  "created_at": "2023-05-10T10:00:00Z",
  "updated_at": "2023-05-20T14:30:00Z"
}
```

**Common Error Responses:**

**Error Response (404 Not Found - Service does not exist or does not belong to provider):**

```json
{
  "detail": "Not found."
}
```

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Error Response (403 Forbidden - User is not a provider):**

```json
{
  "detail": "You do not have permission to perform this action. User is not a provider."
}
```

#### Update Own Service (Provider)

Allows a logged-in provider to update an existing service they own by its ID. Only fields provided in the request body will be updated (partial updates can be supported via PATCH, but this example uses PUT for a full update of allowed fields).

**`curl` Command:**

```bash
curl -X PUT http://localhost:8000/api/services/provider/me/service-uuid-abc-123/ \
-H "Authorization: Bearer <PROVIDER_ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-d '{
  "title": "Advanced Full-Stack Web Development",
  "description": "End-to-end web development services using modern frameworks (React, Node.js, Python/Django). Includes frontend, backend, database design, and basic deployment consultation.",
  "category_id": "category-uuid-webdev",
  "price_model": "project-based",
  "price": 1650.00,
  "currency": "USD",
  "availability_details": "Accepting new projects. Standard turnaround 3-5 weeks. Rush projects considered.",
  "service_area_zip_codes": ["90001", "90002", "90210", "90211"],
  "tags": ["web development", "full-stack", "react", "django", "nodejs", "api"],
  "is_active": true
}'
```

**Path Parameters:**

- `service_id` (uuid, required): The UUID of the service to update.

**Possible Output Response (Success 200 OK):**

```json
{
  "service_id": "service-uuid-abc-123",
  "provider_id": "provider-uuid-123",
  "title": "Advanced Full-Stack Web Development",
  "description": "End-to-end web development services using modern frameworks (React, Node.js, Python/Django). Includes frontend, backend, database design, and basic deployment consultation.",
  "category": {
    "category_id": "category-uuid-webdev",
    "name": "Web Development"
  },
  "price_model": "project-based",
  "price": "1650.00",
  "currency": "USD",
  "availability_details": "Accepting new projects. Standard turnaround 3-5 weeks. Rush projects considered.",
  "service_area_zip_codes": ["90001", "90002", "90210", "90211"],
  "tags": ["web development", "full-stack", "react", "django", "nodejs", "api"],
  "is_active": true,
  "average_rating": 4.9,
  "images": [
    {"image_url": "http://localhost:8000/media/services/webdev_portfolio1.jpg", "caption": "Portfolio Screenshot 1"},
    {"image_url": "http://localhost:8000/media/services/webdev_portfolio2.jpg", "caption": "Client Testimonial Graphic"}
  ],
  "created_at": "2023-05-10T10:00:00Z",
  "updated_at": "2023-06-02T19:00:00Z"
}
```

**Common Error Responses:**

**Error Response (404 Not Found - Service does not exist or does not belong to provider):**

```json
{
  "detail": "Not found."
}
```

**Error Response (400 Bad Request - Invalid data):**

```json
{
  "title": ["This field may not be blank."],
  "price": ["A valid number is required."],
  "category_id": ["This field is required."]
}
```

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Error Response (403 Forbidden - User is not a provider):**

```json
{
  "detail": "You do not have permission to perform this action. User is not a provider."
}
```

#### Delete Own Service (Provider)

Allows a logged-in provider to delete a specific service they own by its ID.

**`curl` Command:**

```bash
curl -X DELETE http://localhost:8000/api/services/provider/me/service-uuid-to-delete/ \
-H "Authorization: Bearer <PROVIDER_ACCESS_TOKEN>" \
-H "Accept: application/json"
```

**Path Parameters:**

- `service_id` (uuid, required): The UUID of the service to delete.

**Possible Output Response (Success 204 No Content):**
(No JSON body is typically returned for a successful DELETE operation)

**Common Error Responses:**

**Error Response (404 Not Found - Service does not exist or does not belong to provider):**

```json
{
  "detail": "Not found."
}
```

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Error Response (403 Forbidden - User is not a provider):**

```json
{
  "detail": "You do not have permission to perform this action. User is not a provider."
}
```

**Error Response (409 Conflict - Service cannot be deleted, e.g., active bookings):**

```json
{
  "detail": "Service cannot be deleted as it has active bookings or other dependencies."
}
```

---

### Public Service Request Endpoints

These endpoints allow public users (typically not logged in, or any user type) to submit or view general service requests that may be picked up by providers.

#### Submit Public Service Request

Allows any user (authenticated or anonymous) to submit a request for a service. Contact information is required for follow-up.

**`curl` Command:**

```bash
curl -X POST http://localhost:8000/api/service-requests/public/ \
-H "Content-Type: application/json" \
-H "Accept: application/json" \
-d '{
  "title": "Need help with garden landscaping",
  "description": "Looking for someone to redesign my front yard. Approx 500 sq ft. Interested in drought-tolerant plants and a new walkway.",
  "category_id": "category-uuid-landscaping",
  "location_preference": "on-site",
  "address": {
    "street": "789 Public Request Rd",
    "city": "Anytown",
    "state": "CA",
    "zip_code": "90210",
    "country": "USA"
  },
  "preferred_contact_method": "email",
  "contact_email": "requester@example.com",
  "contact_phone": "+15551234567",
  "budget_range": "500-1500 USD",
  "desired_completion_date": "2023-08-15"
}'
```

**Possible Output Response (Success 201 Created):**

```json
{
  "request_id": "pub-req-uuid-newly-created",
  "title": "Need help with garden landscaping",
  "description": "Looking for someone to redesign my front yard. Approx 500 sq ft. Interested in drought-tolerant plants and a new walkway.",
  "category": {
    "category_id": "category-uuid-landscaping",
    "name": "Landscaping Services"
  },
  "status": "pending_assignment",
  "location_preference": "on-site",
  "address": {
    "street": "789 Public Request Rd",
    "city": "Anytown",
    "state": "CA",
    "zip_code": "90210",
    "country": "USA"
  },
  "preferred_contact_method": "email",
  "contact_email": "requester@example.com",
  "budget_range": "500-1500 USD",
  "desired_completion_date": "2023-08-15",
  "submitted_at": "2023-06-02T19:30:00Z",
  "message": "Service request submitted successfully. Providers in your area will be notified."
}
```

**Common Error Responses:**

**Error Response (400 Bad Request - Invalid data):**

```json
{
  "title": ["This field may not be blank."],
  "category_id": ["This field is required."],
  "contact_email": ["Enter a valid email address."],
  "address": {
    "zip_code": ["This field is required."]
  }
}
```

#### View Public Service Request Details

Allows anyone to view the details of a specific public service request using its ID. This might be used by the original requester to check status or by providers considering the request.

**`curl` Command:**

```bash
curl -X GET http://localhost:8000/api/service-requests/public/pub-req-uuid-newly-created/ \
-H "Accept: application/json"
```

**Path Parameters:**

- `request_id` (uuid, required): The UUID of the public service request to retrieve.

**Possible Output Response (Success 200 OK):**

```json
{
  "request_id": "pub-req-uuid-newly-created",
  "title": "Need help with garden landscaping",
  "description": "Looking for someone to redesign my front yard. Approx 500 sq ft. Interested in drought-tolerant plants and a new walkway.",
  "category": {
    "category_id": "category-uuid-landscaping",
    "name": "Landscaping Services"
  },
  "status": "pending_assignment", // Could also be 'assigned', 'in_progress', 'completed', 'cancelled'
  "location_preference": "on-site",
  "address": {
    "street": "789 Public Request Rd", // Consider privacy implications for full address display
    "city": "Anytown",
    "state": "CA",
    "zip_code": "90210",
    "country": "USA"
  },
  "preferred_contact_method": "email",
  // "contact_email": "requester@example.com", // Consider privacy: maybe hide PII on public view
  // "contact_phone": "+15551234567", // Consider privacy
  "budget_range": "500-1500 USD",
  "desired_completion_date": "2023-08-15",
  "submitted_at": "2023-06-02T19:30:00Z",
  "updated_at": "2023-06-02T19:35:00Z",
  "assigned_provider_id": null // or "provider-uuid-xyz" if assigned
}
```

**Common Error Responses:**

**Error Response (404 Not Found - Request does not exist):**

```json
{
  "detail": "Not found."
}
```

---

### Service Requests (Customer)

These endpoints are for logged-in customers to manage their specific service requests, such as creating new requests for services offered by specific providers, viewing their active requests, updating, or canceling them.

#### Create Service Request (Customer)

Allows a logged-in customer to create a service request for a specific service offered by a provider.

**`curl` Command:**

```bash
curl -X POST http://localhost:8000/api/service-requests/customer/ \
-H "Authorization: Bearer <CUSTOMER_ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-H "Accept: application/json" \
-d '{
  "service_id": "service-uuid-abc-123",
  "message_to_provider": "Hello, I am interested in your Advanced Web Development service. I have a project idea I'd like to discuss. My preferred start date is around next month. Please let me know your availability for a brief chat.",
  "preferred_start_date": "2023-09-01",
  "additional_requirements": "Integration with an existing payment gateway (Stripe) will be needed."
}'
```

**Possible Output Response (Success 201 Created):**

```json
{
  "request_id": "cust-req-uuid-789",
  "customer_id": "customer-uuid-456",
  "service_id": "service-uuid-abc-123",
  "provider_id": "provider-uuid-123"
  "status": "pending_provider_acceptance",
  "message_to_provider": "Hello, I am interested in your Advanced Web Development service. I have a project idea I'd like to discuss. My preferred start date is around next month. Please let me know your availability for a brief chat.",
  "preferred_start_date": "2023-09-01",
  "additional_requirements": "Integration with an existing payment gateway (Stripe) will be needed.",
  "created_at": "2023-07-10T11:00:00Z",
  "updated_at": "2023-07-10T11:00:00Z"
}
```

**Common Error Responses:**

**Error Response (400 Bad Request - Invalid data):**

```json
{
  "service_id": ["This field is required."],
  "message_to_provider": ["This field may not be blank."]
}
```

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Error Response (403 Forbidden - User is not a customer):**

```json
{
  "detail": "You do not have permission to perform this action. User is not a customer."
}
```

**Error Response (404 Not Found - Service ID does not exist):**

```json
{
  "detail": "Service with the provided ID not found."
}
```

#### List Own Service Requests (Customer)

Allows a logged-in customer to list all their service requests, with options for pagination and filtering by status.

**`curl` Command:**

```bash
curl -X GET 'http://localhost:8000/api/service-requests/customer/me/?page=1&page_size=10&status=pending_provider_acceptance' \
-H "Authorization: Bearer <CUSTOMER_ACCESS_TOKEN>" \
-H "Accept: application/json"
```

**Query Parameters:**

- `page` (integer, optional): Page number for pagination. Defaults to 1.
- `page_size` (integer, optional): Number of items per page. Defaults to 10.
- `status` (string, optional): Filter by request status (e.g., `pending_provider_acceptance`, `accepted`, `in_progress`, `completed`, `cancelled`, `declined`).

**Possible Output Response (Success 200 OK):**

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "request_id": "cust-req-uuid-789",
      "customer_id": "customer-uuid-456",
      "service_id": "service-uuid-abc-123",
      "service_title": "Advanced Web Development", // Title of the service requested
      "provider_id": "provider-uuid-123",
      "provider_name": "Dev Solutions Inc.", // Name of the provider
      "status": "pending_provider_acceptance",
      "message_to_provider": "Hello, I am interested in your Advanced Web Development service. I have a project idea I'd like to discuss. My preferred start date is around next month. Please let me know your availability for a brief chat.",
      "preferred_start_date": "2023-09-01",
      "additional_requirements": "Integration with an existing payment gateway (Stripe) will be needed.",
      "created_at": "2023-07-10T11:00:00Z",
      "updated_at": "2023-07-10T11:00:00Z"
    }
    // ... more requests
  ]
}
```

**Common Error Responses:**

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Error Response (403 Forbidden - User is not a customer):**

```json
{
  "detail": "You do not have permission to perform this action. User is not a customer."
}
```

#### Retrieve Own Service Request (Customer)

Allows a logged-in customer to retrieve details for a specific service request they made.

**`curl` Command:**

```bash
curl -X GET http://localhost:8000/api/service-requests/customer/me/cust-req-uuid-789/ \
-H "Authorization: Bearer <CUSTOMER_ACCESS_TOKEN>" \
-H "Accept: application/json"
```

**Path Parameters:**

- `request_id` (uuid, required): The UUID of the service request to retrieve.

**Possible Output Response (Success 200 OK):**

```json
{
  "request_id": "cust-req-uuid-789",
  "customer_id": "customer-uuid-456",
  "service_id": "service-uuid-abc-123",
  "service_title": "Advanced Web Development",
  "provider_id": "provider-uuid-123",
  "provider_name": "Dev Solutions Inc.",
  "status": "pending_provider_acceptance", // Could be other statuses like 'accepted', 'in_progress', 'completed', 'cancelled', 'declined'
  "message_to_provider": "Hello, I am interested in your Advanced Web Development service. I have a project idea I'd like to discuss. My preferred start date is around next month. Please let me know your availability for a brief chat.",
  "provider_response_message": null, // Or a message from the provider if they responded
  "preferred_start_date": "2023-09-01",
  "agreed_start_date": null, // Populated if provider accepts and sets a date
  "additional_requirements": "Integration with an existing payment gateway (Stripe) will be needed.",
  "estimated_completion_date": null,
  "actual_completion_date": null,
  "cancellation_reason": null,
  "created_at": "2023-07-10T11:00:00Z",
  "updated_at": "2023-07-10T11:05:00Z" // e.g., if provider viewed it
}
```

**Common Error Responses:**

**Error Response (404 Not Found - Request does not exist or does not belong to customer):**

```json
{
  "detail": "Not found."
}
```

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Error Response (403 Forbidden - User is not a customer):**

```json
{
  "detail": "You do not have permission to perform this action. User is not a customer."
}
```

#### Update Own Service Request (Customer)

Allows a logged-in customer to update certain details of a service request they made, typically before it's accepted or in progress. Not all fields may be updatable.

**`curl` Command:**

```bash
curl -X PUT http://localhost:8000/api/service-requests/customer/me/cust-req-uuid-789/ \
-H "Authorization: Bearer <CUSTOMER_ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-H "Accept: application/json" \
-d '{
  "message_to_provider": "Update: I've attached a more detailed brief to my profile. Could you please review it? My availability for a chat is flexible next week.",
  "preferred_start_date": "2023-09-05",
  "additional_requirements": "Integration with Stripe is key. Also, need it to be mobile-responsive."
}'
```

**Path Parameters:**

- `request_id` (uuid, required): The UUID of the service request to update.

**Possible Output Response (Success 200 OK):**

```json
{
  "request_id": "cust-req-uuid-789",
  "customer_id": "customer-uuid-456",
  "service_id": "service-uuid-abc-123",
  "service_title": "Advanced Web Development",
  "provider_id": "provider-uuid-123",
  "provider_name": "Dev Solutions Inc.",
  "status": "pending_provider_acceptance", // Status might change based on rules, e.g., if update requires re-approval
  "message_to_provider": "Update: I've attached a more detailed brief to my profile. Could you please review it? My availability for a chat is flexible next week.",
  "provider_response_message": null,
  "preferred_start_date": "2023-09-05",
  "agreed_start_date": null,
  "additional_requirements": "Integration with Stripe is key. Also, need it to be mobile-responsive.",
  "created_at": "2023-07-10T11:00:00Z",
  "updated_at": "2023-07-11T09:15:00Z"
}
```

**Common Error Responses:**

**Error Response (400 Bad Request - Invalid data or update not allowed):**

```json
{
  "message_to_provider": ["This field may not be blank."],
  "non_field_errors": ["Service request cannot be updated at its current status (e.g., 'completed' or 'cancelled')."]
}
```

**Error Response (404 Not Found - Request does not exist or does not belong to customer):**

```json
{
  "detail": "Not found."
}
```

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Error Response (403 Forbidden - User is not a customer):**

```json
{
  "detail": "You do not have permission to perform this action. User is not a customer."
}
```

#### Cancel Own Service Request (Customer)

Allows a logged-in customer to cancel a service request they made, typically if it has not yet been completed or is in a state that allows cancellation.

**`curl` Command:**

```bash
curl -X POST http://localhost:8000/api/service-requests/customer/me/cust-req-uuid-789/cancel/ \
-H "Authorization: Bearer <CUSTOMER_ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-H "Accept: application/json" \
-d '{
  "reason": "Project scope has changed, no longer need this specific service."
}'
```

**Path Parameters:**

- `request_id` (uuid, required): The UUID of the service request to cancel.

**Request Body:**

- `reason` (string, optional): Customer's reason for cancellation.

**Possible Output Response (Success 200 OK):**

```json
{
  "request_id": "cust-req-uuid-789",
  "customer_id": "customer-uuid-456",
  "service_id": "service-uuid-abc-123",
  "service_title": "Advanced Web Development",
  "provider_id": "provider-uuid-123",
  "provider_name": "Dev Solutions Inc.",
  "status": "cancelled_by_customer",
  "message_to_provider": "Update: I've attached a more detailed brief to my profile. Could you please review it? My availability for a chat is flexible next week.",
  "provider_response_message": null,
  "preferred_start_date": "2023-09-05",
  "agreed_start_date": null,
  "additional_requirements": "Integration with Stripe is key. Also, need it to be mobile-responsive.",
  "cancellation_reason": "Project scope has changed, no longer need this specific service.",
  "created_at": "2023-07-10T11:00:00Z",
  "updated_at": "2023-07-12T10:00:00Z"
}
```

**Common Error Responses:**

**Error Response (400 Bad Request - Cancellation not allowed):**

```json
{
  "non_field_errors": ["Service request cannot be cancelled at its current status (e.g., 'completed')."]
}
```

**Error Response (404 Not Found - Request does not exist or does not belong to customer):**

```json
{
  "detail": "Not found."
}
```

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Error Response (403 Forbidden - User is not a customer):**

```json
{
  "detail": "You do not have permission to perform this action. User is not a customer."
}
```

---

### Service Requests (Admin)

These endpoints are for administrators to oversee and manage all service requests within the system. This includes listing all requests, viewing details of specific requests, and potentially moderating or intervening in requests if necessary.

#### List All Service Requests (Admin)

Allows an administrator to list all service requests in the system, with pagination and filtering options (e.g., by status, customer, provider, date range).

**`curl` Command:**

```bash
curl -X GET 'http://localhost:8000/api/service-requests/admin/all/?page=1&page_size=10&status=pending_provider_acceptance&customer_id=customer-uuid-456' \
-H "Authorization: Bearer <ADMIN_ACCESS_TOKEN>" \
-H "Accept: application/json"
```

**Query Parameters:**

- `page` (integer, optional): Page number for pagination. Defaults to 1.
- `page_size` (integer, optional): Number of items per page. Defaults to 10.
- `status` (string, optional): Filter by request status.
- `customer_id` (uuid, optional): Filter by customer ID.
- `provider_id` (uuid, optional): Filter by provider ID.
- `date_from` (date, optional, YYYY-MM-DD): Filter requests created on or after this date.
- `date_to` (date, optional, YYYY-MM-DD): Filter requests created on or before this date.

**Possible Output Response (Success 200 OK):**

```json
{
  "count": 150, // Total count of matching requests
  "next": "http://localhost:8000/api/service-requests/admin/all/?page=2&page_size=10&status=pending_provider_acceptance&customer_id=customer-uuid-456",
  "previous": null,
  "results": [
    {
      "request_id": "cust-req-uuid-789",
      "customer_id": "customer-uuid-456",
      "customer_name": "Alice Wonderland", // Added for admin convenience
      "service_id": "service-uuid-abc-123",
      "service_title": "Advanced Web Development",
      "provider_id": "provider-uuid-123",
      "provider_name": "Dev Solutions Inc.",
      "status": "pending_provider_acceptance",
      "message_to_provider": "Hello, I am interested...",
      "preferred_start_date": "2023-09-01",
      "created_at": "2023-07-10T11:00:00Z",
      "updated_at": "2023-07-10T11:00:00Z"
    }
    // ... more requests
  ]
}
```

**Common Error Responses:**

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Error Response (403 Forbidden - User is not an admin):**

```json
{
  "detail": "You do not have permission to perform this action. User is not an administrator."
}
```

#### Retrieve Service Request Details (Admin)

Allows an administrator to retrieve the full details of any specific service request by its ID.

**`curl` Command:**

```bash
curl -X GET http://localhost:8000/api/service-requests/admin/all/cust-req-uuid-789/ \
-H "Authorization: Bearer <ADMIN_ACCESS_TOKEN>" \
-H "Accept: application/json"
```

**Path Parameters:**

- `request_id` (uuid, required): The UUID of the service request to retrieve.

**Possible Output Response (Success 200 OK):**

```json
{
  "request_id": "cust-req-uuid-789",
  "customer_id": "customer-uuid-456",
  "customer_profile": { 
    "user_id": "customer-uuid-456",
    "username": "alicew",
    "email": "alice@example.com",
    "phone_number": "+15551112233",
    "full_name": "Alice Wonderland",
    "profile_picture_url": "http://localhost:8000/media/users/alice.jpg"
  },
  "service_id": "service-uuid-abc-123",
  "service_title": "Advanced Web Development",
  "provider_id": "provider-uuid-123",
  "provider_profile": { 
    "user_id": "provider-uuid-123",
    "username": "devsolutions",
    "email": "contact@devsolutions.com",
    "phone_number": "+15558889900",
    "full_name": "Dev Solutions Inc.",
    "profile_picture_url": "http://localhost:8000/media/users/devsolutions.jpg"
  },
  "status": "pending_provider_acceptance",
  "message_to_provider": "Hello, I am interested in your Advanced Web Development service...",
  "provider_response_message": null,
  "preferred_start_date": "2023-09-01",
  "agreed_start_date": null,
  "additional_requirements": "Integration with Stripe...",
  "estimated_completion_date": null,
  "actual_completion_date": null,
  "cancellation_reason": null,
  "created_at": "2023-07-10T11:00:00Z",
  "updated_at": "2023-07-10T11:05:00Z",
  "admin_notes": [] 
}
```

**Common Error Responses:**

**Error Response (404 Not Found - Request does not exist):**

```json
{
  "detail": "Not found."
}
```

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Error Response (403 Forbidden - User is not an admin):**

```json
{
  "detail": "You do not have permission to perform this action. User is not an administrator."
}
```

```



#### Update Service Request (Admin)

Allows an administrator to update details of any service request. This might include changing status, assigning a provider, or adding admin notes.

**`curl` Command:** 
```bash
curl -X PUT http://localhost:8000/api/service-requests/admin/all/cust-req-uuid-789/ \
-H "Authorization: Bearer <ADMIN_ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-H "Accept: application/json" \
-d '{
  "status": "pending_manual_assignment",
  "assigned_provider_id": "provider-uuid-manual-assign",
  "admin_notes": [
    {
      "note": "Customer called, clarified requirements. Manually assigning to Provider XYZ due to specific expertise.",
      "admin_id": "admin-uuid-001",
      "timestamp": "2023-07-11T14:30:00Z"
    }
  ]
}'
```

**Path Parameters:**

- `request_id` (uuid, required): The UUID of the service request to update.

**Request Body Fields (example, actual fields may vary):**

- `status` (string, optional): New status for the request (e.g., `pending_manual_assignment`, `on_hold`, `resolved_by_admin`, `closed`).
- `assigned_provider_id` (uuid, optional): Manually assign or change the provider.
- `admin_notes` (array of objects, optional): Add or update administrative notes.
  - `note` (string, required): The content of the note.
  - `admin_id` (string, required): ID of the admin making the note (usually taken from token).
  - `timestamp` (datetime, required): Timestamp of the note.

**Possible Output Response (Success 200 OK):**

```json
{
  "request_id": "cust-req-uuid-789",
  "customer_id": "customer-uuid-456",
  "service_id": "service-uuid-abc-123",
  "status": "pending_manual_assignment",
  "assigned_provider_id": "provider-uuid-manual-assign",
  // ... other fields as in GET response ...
  "admin_notes": [
    {
      "note_id": "note-uuid-1",
      "note": "Customer called, clarified requirements. Manually assigning to Provider XYZ due to specific expertise.",
      "admin_id": "admin-uuid-001",
      "admin_username": "SuperAdmin",
      "timestamp": "2023-07-11T14:30:00Z"
    }
  ],
  "updated_at": "2023-07-11T14:30:00Z"
}
```

**Common Error Responses:**

**Error Response (400 Bad Request - Invalid data):**

```json
{
  "status": ["'invalid_status_value' is not a valid choice."],
  "admin_notes": [{"note": ["This field may not be blank."]}]
}
```

**Error Response (404 Not Found - Request does not exist):**

```json
{
  "detail": "Not found."
}
```

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Error Response (403 Forbidden - User is not an admin):**

```json
{
  "detail": "You do not have permission to perform this action. User is not an administrator."
}
```

---

## Products

This section covers APIs related to product listings, categories, and management. Products might be offered by providers as an alternative or supplement to services.

---

### Product Categories

Endpoints for managing and viewing product categories. Categories help organize products and make them discoverable.

---

### Products (Individual)

(Section content to be added)

---

## Bids

(Section content to be added)

---

### Provider Bidding Actions

(Section content to be added)

---

### Bids - Customer View

(Section content to be added)

---

### Bids - Admin View

(Section content to be added)

---

## Bookings

(Section content to be added)

---

### Create Booking

(Section content to be added)

---

### View Booking Details

(Section content to be added)

---

### Update Booking Status

(Section content to be added)

---

### List Customer Bookings

(Section content to be added)

---

### List Provider Bookings

(Section content to be added)

---

### List Admin Bookings

(Section content to be added)

---

## Calendar Integration

(Section content to be added)

---

## Payment Processing

(Section content to be added)

---

### Create Payment Intent

(Section content to be added)

---

### Confirm Payment

(Section content to be added)

---

### Retrieve Payment Details

(Section content to be added)

---

### List Payments (Customer/Provider/Admin)

(Section content to be added)

---

### Issue Refund (Admin)

(Section content to be added)

---

### Payment Gateway Accounts (Provider)

(Section content to be added)

---

#### Link Payment Gateway Account

(Section content to be added)

---

#### View Payment Gateway Account Details

(Section content to be added)

---

#### Update Payment Gateway Account

(Section content to be added)

---

#### Remove Payment Gateway Account

(Section content to be added)

---

### Payouts (Provider/Admin)

(Section content to be added)

---

#### Request Payout (Provider)

(Section content to be added)

---

#### View Payout History (Provider/Admin)

(Section content to be added)

---

#### Process Payouts (Admin)

(Section content to be added)

---

#### View Payout Settings (Provider/Admin)

(Section content to be added)

---

## Messaging

(Section content to be added)

---

### Message Threads

(Section content to be added)

---

#### Create Message Thread

(Section content to be added)

---

#### List User Message Threads

(Section content to be added)

---

#### View Message Thread Details

(Section content to be added)

---

#### Archive Message Thread

(Section content to be added)

---

#### Mark Thread as Read/Unread

(Section content to be added)

---

### Individual Messages

(Section content to be added)

---

#### Send Message in Thread

(Section content to be added)

---

#### List Messages in Thread

(Section content to be added)

---

#### Edit Message

(Section content to be added)

---

#### Delete Message

(Section content to be added)

---

## Notifications (HTTP)

(Section content to be added)

---

### List User Notifications

(Section content to be added)

---

### Mark Notification as Read

(Section content to be added)

---

### Mark All Notifications as Read

Allows a user to mark all their unread notifications as read in a single operation.

**Endpoint:** `POST /api/notifications/mark-all-read`

**Request Body:** None required

**`curl` Command:**

```bash
curl -X POST http://localhost:8000/api/notifications/mark-all-read \
-H "Authorization: Bearer <USER_ACCESS_TOKEN>"
```

**Possible Output Response (Success 200 OK):**

```json
{
  "message": "All notifications marked as read",
  "count": 5  // Number of notifications that were updated
}
```

**Error Response (401 Unauthorized):**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

### Delete Notification

(Section content to be added)

---

### Notification Settings

(Section content to be added)

---

#### Get Notification Settings

(Section content to be added)

---

#### Update Notification Settings

(Section content to be added)

---

## AI Suggestions and Feedback

(Section content to be added)

---

### AI Suggestions

(Section content to be added)

---

#### Get AI Suggestions for Service Request

(Section content to be added)

---

#### Get AI Suggestions for Pricing

(Section content to be added)

---

#### Get AI Suggestions for Descriptions

(Section content to be added)

---

### AI Feedback Logs

(Section content to be added)

---

#### Submit Feedback on AI Suggestion

(Section content to be added)

---

#### List AI Feedback Logs (Admin)

(Section content to be added)

---

## Verifications (User Identity, etc.)

(Section content to be added)

---

### Submit Verification Document

(Section content to be added)

---

### Check Verification Status

(Section content to be added)

---

### Admin Verification Actions

(Section content to be added)

---

#### List Pending Verifications (Admin)

(Section content to be added)

---

#### Approve/Reject Verification (Admin)

(Section content to be added)

---

### Submit Review for a Service/Provider

(Section content to be added)

---

#### Generate Financial Report

(Section content to be added)

---

```text
{{ ... }}
```

(Section content to be added)

---

### Admin User Management

(Section content to be added)

---

#### List All Users (Admin)

(Section content to be added)

---

#### View User Details (Admin)

(Section content to be added)

---

#### Activate/Deactivate User (Admin)

(Section content to be added)

---

#### Assign User Roles (Admin)

(Section content to be added)

---

### Admin Service Management

(Section content to be added)

---

#### List All Services (Admin)

(Section content to be added)

---

#### Update Service Details (Admin)

(Section content to be added)

---

#### Manage Service Categories (Admin)

(Section content to be added)

---

## WebSocket APIs

(Section content to be added)

---

### Real-time Notifications (WebSocket)

(Section content to be added)

---

### Real-time Messaging (WebSocket)

(Section content to be added)

---

### Real-time Booking Updates (WebSocket)

(Section content to be added)

---

## Health Checks

(Section content to be added)

---

### System Health Endpoint

(Section content to be added)

---

### Database Health Endpoint

(Section content to be added)

---

### Service Dependency Health Endpoint

(Section content to be added)

---

## Metrics

(Section content to be added)

---

### Prometheus Metrics Endpoint

(Section content to be added)

---
