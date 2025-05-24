# Prbal API Postman Collection

This repository contains a Postman collection for testing the Prbal marketplace API endpoints. The collection is organized by user types (Customer and Provider) and includes authentication, profile management, service management, bidding, booking, payment, review, chat, notifications, and payout endpoints.

## Setup Instructions

1. Install [Postman](https://www.postman.com/downloads/)
2. Import the following files into Postman:
   - `Prbal-Postman-Collection.json`: Contains all API requests
   - `Prbal-Postman-Environment.json`: Contains environment variables
   - `Prbal-Postman-Test-Scripts.js`: Contains automated tests (Apply to root collection or relevant folders)

## Environment Variables

The collection uses environment variables to manage different configurations and separate tokens for customers and providers:

### Base Configuration
- `base_url`: API base URL (default: http://localhost:8000)
- `base_url_ws`: WebSocket base URL (default: ws://localhost:8000)

### General Access Token (Can be set to customer or provider token for general endpoints)
- `access_token`: JWT access token for general authenticated endpoints

### Customer Variables
- `customer_email`: Test customer email
- `customer_password`: Test customer password
- `customer_access_token`: JWT access token for customer
- `customer_refresh_token`: JWT refresh token for customer
- `customer_id`: Customer's user ID

### Provider Variables
- `provider_email`: Test service provider email
- `provider_password`: Test service provider password
- `provider_access_token`: JWT access token for provider
- `provider_refresh_token`: JWT refresh token for provider
- `provider_id`: Provider's user ID

### Admin Variables (Requires separate login/setup for an admin user)
- `admin_access_token`: JWT access token for an admin user
- `admin_refresh_token`: JWT refresh token for an admin user

### Common Resource IDs (Often set by test scripts)
- `service_id`: ID of the created/selected service
- `category_id`: ID of the selected service category
- `request_id`: ID of the created/selected service request
- `bid_id`: ID of the created/selected bid
- `booking_id`: ID of the created/selected booking
- `booking_id_for_review`: ID of a booking to be reviewed
- `review_id`: ID of a created review
- `provider_id_to_view_reviews`: User ID of a provider whose reviews are to be fetched
- `payment_id`: ID of the created/selected payment record
- `message_id`: ID of a specific chat message
- `notification_id`: ID of a specific notification
- `payout_id`: ID of a specific payout

It is recommended to add the following to your environment if not present:
- `user_id_to_get`, `skill_id`, `skill_id_to_update`, `skill_id_to_delete`
- `category_id_to_get`, `category_id_to_update`, `category_id_to_delete`
- `request_id_to_get`, `my_request_id_to_update`, `my_request_id_to_delete`
- `bid_id_to_get`, `my_bid_id_to_update`, `my_bid_id_to_withdraw` (Note: Withdraw is DELETE /bids/{id}/)
- `booking_id_to_get`, `booking_id_to_update`
- `message_id_to_get`
- `customer_profile_id`, `provider_profile_id` (for admin access to specific profiles)

## API Structure

### Authentication APIs (Both Users) - Base Path: `/api/v1/users/`
- `POST /register/` - Register a new user (customer or provider)
- `POST /login/` - Login for both user types
- `POST /token/refresh/` - Refresh JWT token
- `GET /me/` - Get current authenticated user details
- `POST /profile/image/` - Upload profile image for authenticated user

### Customer-Specific APIs

1.  **Profile Management** - Base Path: `/api/v1/customer-profiles/`
    *   `GET /me/` - Get authenticated customer's profile
    *   `PATCH /me/` - Update authenticated customer's profile
    *   (Admin/Restricted: `GET /`, `POST /`, `GET /{id}/`, `PUT /{id}/`, `PATCH /{id}/`)

2.  **Service Requests** - Base Path: `/api/v1/requests/`
    *   `POST /` - Create a new service request
    *   `GET /me/` - List own service requests
    *   `GET /{id}/` - Get specific request details
    *   `PATCH /{id}/` - Update own service request
    *   `DELETE /{id}/` - Cancel own service request

3.  **Bid Management (as Customer)** - Base Path: `/api/v1/`
    *   `GET /bids/` - View bids on their service requests (filtered by backend)
    *   `GET /requests/{request_id}/bids/` - View bids for a specific service request (nested)
    *   `POST /bids/{bid_id}/accept/` - Accept a bid
    *   `POST /bids/{bid_id}/reject/` - Reject a bid

4.  **Bookings (as Customer)** - Base Path: `/api/v1/bookings/`
    *   `GET /` - List own bookings (filtered by backend, e.g., `?status=scheduled`)
    *   `GET /{id}/` - Get booking details
    *   `POST /{id}/confirm_completion/` - Confirm service completion
    *   `POST /{id}/cancel/` - Cancel booking (provide `reason` in body)

5.  **Reviews (as Customer)** - Base Path: `/api/v1/reviews/`
    *   `POST /` - Create a review for a completed service (requires `booking` ID in body)
    *   `POST /bookings/{booking_id}/reviews/` - Create review for a specific booking (nested)
    *   `GET /` - List reviews given by the customer (filtered by backend)
    *   `GET /{id}/` - Get specific review details
    *   `PUT, PATCH /{id}/` - Update own review (if allowed)
    *   `DELETE /{id}/` - Delete own review (if allowed)

### Service Provider-Specific APIs

1.  **Profile Management** - Base Path: `/api/v1/provider-profiles/`
    *   `GET /me/` - Get authenticated provider's profile
    *   `PATCH /me/` - Update authenticated provider's profile
    *   `GET /api/v1/skills/` - List available skills (used for selection)
    *   `POST /me/skills/` (Example path, actual might be part of profile PATCH) - Add/update skills for provider profile
    *   (Admin/Restricted: `GET /`, `POST /`, `GET /{id}/`, `PUT /{id}/`, `PATCH /{id}/` for provider-profiles)

2.  **Service Management** - Base Path: `/api/v1/services/`
    *   `POST /` - Create a new service
    *   `GET /` - List own services (filtered by backend)
    *   `GET /{id}/` - Get service details
    *   `PATCH /{id}/` - Update own service
    *   `DELETE /{id}/` - Delete own service

3.  **Bid Management (as Provider)** - Base Path: `/api/v1/`
    *   `GET /requests/available/` - View available service requests
    *   `POST /bids/` - Submit a new bid for a `service_request_id`
    *   `GET /bids/me/` - List own submitted bids
    *   `PATCH /bids/{id}/` - Update own bid (if status allows)
    *   `DELETE /bids/{id}/` - Withdraw own bid (if status allows)
    *   `POST /bids/suggest_price/` - Get AI price suggestion for a service request

4.  **Bookings (as Provider)** - Base Path: `/api/v1/bookings/`
    *   `GET /` - List assigned bookings (filtered by backend, e.g., `?status=scheduled`)
    *   `GET /{id}/` - Get booking details
    *   `PATCH /{id}/status/` - Update booking status (e.g., `in_progress`)
    *   `POST /{id}/complete/` - Mark service as completed by provider
    *   `POST /{id}/cancel/` - Cancel booking (provide `reason` in body)

5.  **Reviews (as Provider)** - Base Path: `/api/v1/reviews/`
    *   `GET /` - List reviews received by the provider (filtered by backend)
    *   `POST /{id}/respond/` - Add a response to a received review

6.  **Payouts** - Base Path: `/api/v1/payouts/`
    *   `GET /` - List provider's payout history
    *   `POST /initiate/` - Request a new payout
    *   `GET /{id}/` - Get specific payout details

### Common APIs (Both Users)

1.  **Service Categories** - Base Path: `/api/v1/categories/`
    *   `GET /` - List all service categories (authenticated)
    *   (Admin only for POST, PUT, PATCH, DELETE on `/` and `/{id}/`)

2.  **Skills (Viewing)** - Base Path: `/api/v1/skills/`
    *   `GET /` - List all skills (authenticated)
    *   (Admin only for POST, PUT, PATCH, DELETE on `/` and `/{id}/`)

3.  **Chat/Messages** - Base Path: `/api/v1/bookings/{booking_id}/messages/`
    *   `GET /` - Get chat history for the booking
    *   `POST /` - Send new message (text or media) for the booking
    *   `GET /{message_id}/` - Get specific chat message by ID
    *   `PATCH /{message_id}/read/` - Mark a received message as read
    *   WebSocket Connection: `WS {{base_url_ws}}/ws/chat/{{booking_id}}/`

4.  **Payments (Viewing)** - Base Path: `/api/v1/payments/`
    *   `GET /` - List payment history user is involved in
    *   `GET /{id}/` - Get specific payment details
    *   `GET /bookings/{booking_id}/payments/` - View payment details for a specific booking (nested alternative)
    *   `POST /bookings/{booking_id}/payments/initiate/` - (Internal) Initiate payment intent for booking
    *   `POST /payments/webhook/stripe/` - (Webhook) Stripe payment event notifications

5.  **Notifications** - Base Path: `/api/v1/notifications/`
    *   `GET /` - List user's notifications
    *   `GET /unread_count/` - Get count of unread notifications
    *   `PATCH /{id}/` - Mark a specific notification as read (body: `{"is_read": true}`)
    *   `POST /mark_all_read/` - Mark all notifications as read

6.  **Service Search & Filtering** - Base Path: `/api/v1/services/`
    *   `GET /?search=query` - Search services by keyword
    *   `GET /?category=id` - Filter services by category ID
    *   `GET /?service_area=CityName` - Filter services by location/area
    *   `GET /?min_rating=4` - Filter services by minimum rating
    *   (Combine query parameters for more specific search)

### Admin-Only API Examples (Illustrative)
- Manage Service Categories: `GET, POST, PUT, PATCH, DELETE /api/v1/categories/` and `api/v1/categories/{id}/`
- Manage Skills: `GET, POST, PUT, PATCH, DELETE /api/v1/skills/` and `api/v1/skills/{id}/`
- Full access to Django Admin interface at `/admin/` for comprehensive data management.

## API Flow (General Overview)

1.  **Authentication**: Users register and log in.
2.  **Profile Setup**: Users complete their profiles.
3.  **Service Listing (Provider)**: Providers list services.
4.  **Service Request (Customer)**: Customers create requests.
5.  **Bidding (Provider)**: Providers bid.
6.  **Bid Acceptance (Customer)**: Customers accept bids, creating bookings.
7.  **Booking Management**: Manage bookings (view, status, cancel).
8.  **Service Completion**: Provider completes, customer confirms.
9.  **Payment Settlement**: Stripe integration handles payments & escrow.
10. **Payouts (Provider)**: Providers initiate payouts.
11. **Reviews**: Customers review; providers respond.
12. **Notifications**: Users receive alerts for key events.
13. **Chat**: Communication throughout booking.

## Test Scripts

The `Prbal-Postman-Test-Scripts.js` file should contain tests to:
- Validate successful operations (2xx status codes).
- Store tokens and IDs in environment variables.
- Verify access controls and error responses (4xx status codes).
- Check basic business logic and response data structures.

## Error Handling

- 200: OK
- 201: Created
- 204: No Content
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error

## Notes

- Update environment variables for your setup.
- Attach test scripts to relevant requests/folders in Postman.
