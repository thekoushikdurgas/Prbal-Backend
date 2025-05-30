# Prbal API Postman Collection

This directory contains Postman configuration files for testing the Prbal service marketplace backend API.

## Contents

- `Prbal API.postman_collection.json` - The main Postman collection with all API endpoints
- `Prbal-Postman-Environment.json` - Environment variables for different deployment environments
- `Prbal-API.md` - Comprehensive API documentation
- `Prbal-Postman-README.md` - This README file with usage instructions

## Setup Instructions

### 1. Import the Collection and Environment

1. Open Postman
2. Click on "Import" button in the top left
3. Select the `Prbal-Postman-Collection.json` and `Prbal-Postman-Environment.json` files
4. Both should appear in your Postman workspace

### 2. Select the Environment

1. In the top right corner of Postman, select the "Prbal API" environment from the dropdown
2. This will load all the necessary environment variables

### 3. Authentication

1. Start by using the "User Registration" or "User Login" requests in the Auth folder
2. The authentication token will be automatically stored in the environment variables
3. Subsequent requests will use this token automatically

## Environment Variables

- `base_url` - The base URL for the API (e.g., http://localhost:8000 for local development)
- `access_token` - JWT access token for authenticated requests (set automatically after login)
- `refresh_token` - JWT refresh token for refreshing access tokens
- `user_id` - Current user's ID (set automatically after login)
- `product_id` - ID of a test product (can be set manually after creating a product)
- `order_id` - ID of a test order (set automatically after purchasing a product)
- `bid_id` - ID of a test bid (can be set manually after creating a bid)
- `booking_id` - ID of a test booking (can be set manually after creating a booking)
- `service_id` - ID of a test service (can be set manually after creating a service)
- `category_id` - ID of a service category (set automatically after creating a category)
- `subcategory_id` - ID of a service subcategory (set automatically after creating a subcategory)

## Collection Structure

The collection is organized into folders corresponding to the API's resource groups as outlined in the `Prbal-API.md` documentation:

- **Authentication APIs** - Registration, login, and token refresh endpoints for all user types
  - Generic Authentication - General authentication endpoints for all users
  - Customer Authentication - Customer-specific registration and login
  - Provider Authentication - Service provider-specific registration and login
  - Admin Authentication - Admin-specific registration and login
  - JWT Token - Token management endpoints

- **User Management APIs** - User profile management endpoints
  - Profile Management - General profile endpoints for all user types
  - Customer-specific - Customer-specific profile endpoints
  - Provider-specific - Provider-specific profile endpoints
  - Admin-specific - Admin-specific profile endpoints
  - User Interaction
    - `POST /api/v1/users/<uuid:id>/like/` - Like a user profile
    - `POST /api/v1/users/<uuid:id>/pass/` - Pass on a user profile

- **User Search** - Endpoints for searching and discovering users
  - General User Search - Search by username, email, phone, name, or user type
  - Phone Search - Specialized search specifically by phone number

- **Verification APIs** - User verification endpoints
  - Verifications
    - `GET /api/v1/verifications/` - List all verifications for current user
    - `POST /api/v1/verifications/` - Submit a new verification
    - `GET /api/v1/verifications/<id>/` - Get verification details
    - `PUT /api/v1/verifications/<id>/` - Update verification
    - `POST /api/v1/verifications/<id>/documents/` - Upload verification documents
    - `POST /api/v1/users/verify/` - General user verification endpoint
  - Admin Verification Management
    - `GET /api/v1/admin/verifications/` - List all verifications (admin only)
    - `POST /api/v1/verifications/<id>/approve/` - Approve verification (admin only)
    - `POST /api/v1/verifications/<id>/reject/` - Reject verification (admin only)

- **Service APIs** - Service creation and management endpoints
  - Service Categories - List, create, and manage service categories
  - Service Subcategories - List, create, and manage service subcategories
  - Services - Browse, create, and manage services
  - Service Requests - Create and manage service requests

- **Bid APIs** - Bidding system endpoints
  - Bids
    - `GET /api/v1/bids/` - List all bids (filtered by user role)
    - `POST /api/v1/bids/` - Create a new bid (provider only)
    - `GET /api/v1/bids/<id>/` - Get bid details
    - `PUT /api/v1/bids/<id>/` - Update bid (owner only)
    - `DELETE /api/v1/bids/<id>/` - Delete bid (owner only)
    - `PATCH /api/v1/bids/<id>/` - Update bid status (accept, reject, complete, cancel)

- **Booking APIs** - Booking management endpoints
  - Bookings - Create, manage, cancel, complete, and reschedule bookings
  - Calendar Integration - Sync with external calendars, import/export events

- **Payment APIs** - Payment processing endpoints
  - Payments - Create, manage, and refund payments
  - Payment Methods - Add, list, and remove payment methods

- **Product APIs** - Product-related endpoints
  - Products
    - `GET /api/v1/products/` - List all products
    - `POST /api/v1/products/` - Create a new product
    - `GET /api/v1/products/<id>/` - Get product details
    - `PUT /api/v1/products/<id>/` - Update product (owner or admin only)
    - `DELETE /api/v1/products/<id>/` - Delete product (owner or admin only)

- **Messaging APIs** - Messaging system endpoints
  - Messages - List conversations, get details, create conversations, send messages

- **Sync APIs** - Offline functionality endpoints
  - Offline Sync
    - `GET /api/sync/status/` - Get sync status
    - `POST /api/sync/pull/` - Pull updates since last sync
    - `POST /api/sync/push/` - Push local changes to server

- **Analytics APIs** - Analytics endpoints
  - Usage Analytics
    - `GET /api/analytics/dashboard/` - Get dashboard analytics
    - `GET /api/analytics/users/` - Get user analytics
    - `GET /api/analytics/services/` - Get service analytics
    - `GET /api/analytics/bookings/` - Get booking analytics
    - `GET /api/analytics/revenue/` - Get revenue analytics

- **Notification APIs** - Notification endpoints
  - Notifications - Get, mark as read, and manage notification settings

- **AI Suggestion APIs** - AI-powered suggestion endpoints
  - AI Suggestions
    - `POST /api/v1/ai-suggestions/price/` - Get price suggestions for a service
    - `POST /api/v1/ai-suggestions/schedule/` - Get scheduling suggestions
    - `POST /api/v1/ai-suggestions/services/` - Get service recommendations

- **Review APIs** - Review management endpoints
  - Reviews
    - `GET /api/v1/reviews/` - List reviews (filtered by query params)
    - `POST /api/v1/reviews/` - Create a new review
    - `GET /api/v1/reviews/<id>/` - Get review details
    - `PUT /api/v1/reviews/<id>/` - Update review (owner only)
    - `DELETE /api/v1/reviews/<id>/` - Delete review (owner or admin only)
    - `POST /api/v1/reviews/<id>/report/` - Report inappropriate review

- **Sync APIs** - Offline functionality endpoints
  - Offline Sync - Sync status, pull updates, push local changes

- **Analytics APIs** - Analytics endpoints
  - Usage Analytics - Dashboard, user, service, booking, and revenue analytics

- **System APIs** - System maintenance endpoints
  - Health Checks
    - `GET /health/` - Basic system health check
    - `GET /health/db/` - Database connection health check
  - Documentation
    - `GET /swagger/` - Swagger UI API documentation
    - `GET /redoc/` - ReDoc API documentation
    - `GET /api/schema/` - OpenAPI schema in JSON format
    - `GET /api/schema/swagger-ui/` - drf-spectacular Swagger UI
    - `GET /api/schema/redoc/` - drf-spectacular ReDoc UI

## Test Scripts

Each request in the collection includes test scripts that validate the API responses. These scripts check for:

- Correct HTTP status codes
- Response structure and schema validation
- Expected business logic behavior
- Proper error handling

The tests use the functions defined in `Prbal-Postman-Test-Scripts.js`.

## Workflow Examples

### User Registration and Authentication Flow

1. Run "User Registration" to create a new user
2. Run "User Login" to authenticate and obtain tokens
3. Access protected resources like "Get User Profile"

### Service Creation and Bidding Flow

1. Authenticate as a service provider
2. Create a new service using "Create Service"
3. Authenticate as a different user
4. Create a bid for the service using "Create Bid"

### Verification Flow

1. Authenticate as a user
2. Submit a new verification using "Submit New Verification"
3. Upload documents using "Upload Verification Documents"
4. Authenticate as an admin
5. Review and approve/reject the verification

### User Search Flow

1. Authenticate as a user
2. Search for users by various criteria using "General User Search"
3. Or search specifically by phone number using "Search Users by Phone Number"

### Product Management and Purchase Flow

1. Authenticate as a service provider
2. Create a new product using "Create New Product (Provider)"
3. Authenticate as a customer
4. Purchase the product using "Purchase Product (Customer)"
5. View your orders using "List Customer Orders"

### Admin Product Review Flow

1. Authenticate as an admin
2. Review pending products using "Admin: Review Pending Products"
3. Approve or reject a product using "Admin: Approve/Reject Product"

## Troubleshooting

- If you receive 401 Unauthorized errors, your access token may have expired. Use the "Refresh Token" request to obtain a new access token.
- If environment variables aren't being set correctly, check the "Tests" tab in the request to ensure the script is executing properly.
- For local development, ensure your Django server is running on the port specified in the `base_url` environment variable.

## Contributing

To add new endpoints to this collection:

1. Use the "Save As" feature in Postman to duplicate an existing request
2. Update the URL, method, and request body as needed
3. Add appropriate test scripts
4. Export the updated collection and commit the changes
