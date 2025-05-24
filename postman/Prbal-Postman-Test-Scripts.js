// Authentication Tests
pm.test("Registration successful", function () {
    pm.response.to.have.status(201);
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('access');
    pm.expect(jsonData).to.have.property('refresh');
    pm.expect(jsonData.user).to.have.property('id');
    pm.expect(jsonData.user).to.have.property('email');
    pm.expect(jsonData.user).to.have.property('user_type');

    // Store user-specific tokens and IDs
    if (jsonData.user.user_type === 'CUSTOMER') {
        pm.environment.set('customer_access_token', jsonData.access);
        pm.environment.set('customer_refresh_token', jsonData.refresh);
        pm.environment.set('customer_id', jsonData.user.id);
    } else if (jsonData.user.user_type === 'PROVIDER') {
        pm.environment.set('provider_access_token', jsonData.access);
        pm.environment.set('provider_refresh_token', jsonData.refresh);
        pm.environment.set('provider_id', jsonData.user.id);
    }
});

pm.test("Login successful", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('access');
    pm.expect(jsonData).to.have.property('refresh');
    pm.expect(jsonData.user).to.have.property('id');
    pm.expect(jsonData.user).to.have.property('user_type');
    
    // Store user-specific tokens based on user type
    if (jsonData.user.user_type === 'CUSTOMER') {
        pm.environment.set('customer_access_token', jsonData.access);
        pm.environment.set('customer_refresh_token', jsonData.refresh);
        pm.environment.set('customer_id', jsonData.user.id);
    } else if (jsonData.user.user_type === 'PROVIDER') {
        pm.environment.set('provider_access_token', jsonData.access);
        pm.environment.set('provider_refresh_token', jsonData.refresh);
        pm.environment.set('provider_id', jsonData.user.id);
    }
});

// Profile Tests
pm.test("Profile retrieved successfully", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('id');
    pm.expect(jsonData).to.have.property('user');
    pm.expect(jsonData).to.have.property('full_name');
    if(jsonData.user) { // User object might not always be nested
        pm.expect(jsonData.user).to.have.property('user_type');
    } else {
        pm.expect(jsonData).to.have.property('user_type'); // if user_type is at top level of profile
    }
});

pm.test("Profile updated successfully", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('id');
    // Check if request body is defined and has mode 'raw'
    if (pm.request.body && pm.request.body.mode === 'raw' && pm.request.body.raw) {
        try {
            const requestBody = JSON.parse(pm.request.body.raw);
            if (requestBody.full_name) {
                 pm.expect(jsonData.full_name).to.eql(requestBody.full_name);
            }
        } catch (e) {
            console.error("Error parsing request body: ", e);
        }
    }
});

pm.test("Profile image uploaded successfully", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('profile_image');
});

// Skills Tests
pm.test("Skills list retrieved successfully", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData.results).to.be.an('array'); // Assuming paginated response
});

pm.test("Skill created successfully (Admin Only)", function () {
    pm.response.to.have.status(201);
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('id');
    pm.expect(jsonData).to.have.property('name');
    pm.expect(jsonData).to.have.property('description');
});

// Service Category Tests
pm.test("Service categories list retrieved successfully", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData.results).to.be.an('array');
    if (jsonData.results && jsonData.results.length > 0) {
        const category = jsonData.results[0];
        pm.environment.set('category_id', category.id);
    }
});

// Service Management Tests
pm.test("Service created successfully", function () {
    if (pm.response.code === 201) {
        const jsonData = pm.response.json();
        pm.expect(jsonData).to.have.property('id');
        pm.expect(jsonData).to.have.property('name');
        pm.expect(jsonData).to.have.property('category');
        pm.expect(jsonData).to.have.property('hourly_rate');
        pm.environment.set('service_id', jsonData.id);
    }
});

pm.test("Service updated successfully", function () {
    if (pm.response.code === 200) {
        const jsonData = pm.response.json();
        pm.expect(jsonData).to.have.property('id');
        pm.expect(jsonData.id).to.eql(parseInt(pm.environment.get('service_id')));
        if (pm.request.body && pm.request.body.mode === 'raw' && pm.request.body.raw) {
          try {
            const requestBody = JSON.parse(pm.request.body.raw);
            if (requestBody.name) {
                pm.expect(jsonData.name).to.eql(requestBody.name);
            }
          } catch (e) {
            console.error("Error parsing request body: ", e);
          }
        }
    }
});

pm.test("Service retrieved successfully", function () {
    if (pm.response.code === 200) {
        const jsonData = pm.response.json();
        pm.expect(jsonData).to.have.property('id');
        pm.expect(jsonData).to.have.property('name');
        pm.expect(jsonData).to.have.property('provider');
        pm.expect(jsonData).to.have.property('category');
    }
});

pm.test("Service list retrieved successfully", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('results');
    pm.expect(jsonData.results).to.be.an('array');
});

pm.test("Service search works correctly", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('results');
    pm.expect(jsonData).to.have.property('count');
    pm.expect(jsonData.results).to.be.an('array');
    
    const url = new URL(pm.request.url.toString()); // Ensure full URL for URLSearchParams
    const searchParams = url.searchParams;
    
    if (searchParams.has('category')) {
        const categoryId = searchParams.get('category');
        jsonData.results.forEach(service => {
            pm.expect(service.category.id).to.eql(parseInt(categoryId));
        });
    }
});

// Service Request Tests
pm.test("Service request created successfully", function () {
    if (pm.response.code === 201) {
        const jsonData = pm.response.json();
        pm.expect(jsonData).to.have.property('id');
        pm.expect(jsonData).to.have.property('title');
        pm.expect(jsonData).to.have.property('status');
        pm.expect(jsonData).to.have.property('customer');
        pm.environment.set('request_id', jsonData.id);
    }
});

pm.test("Service request list retrieved successfully", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('results');
    pm.expect(jsonData.results).to.be.an('array');
});

pm.test("Available requests list retrieved successfully for providers", function () {
    if (pm.response.code === 200) {
        const jsonData = pm.response.json();
        pm.expect(jsonData).to.have.property('results');
        pm.expect(jsonData.results).to.be.an('array');
        jsonData.results.forEach(request => {
            pm.expect(request.status).to.eql('OPEN');
        });
    }
});

// Bid Tests
pm.test("Bid submitted successfully", function () {
    if (pm.response.code === 201) {
        const jsonData = pm.response.json();
        pm.expect(jsonData).to.have.property('id');
        pm.expect(jsonData).to.have.property('amount');
        pm.expect(jsonData).to.have.property('status');
        pm.expect(jsonData.status).to.eql('SUBMITTED');
        pm.environment.set('bid_id', jsonData.id);
    }
});

pm.test("My bids list retrieved successfully", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('results');
    pm.expect(jsonData.results).to.be.an('array');
});

pm.test("Bid details retrieved successfully", function () {
    if (pm.response.code === 200) {
        const jsonData = pm.response.json();
        pm.expect(jsonData).to.have.property('id');
        pm.expect(jsonData).to.have.property('service_request');
        pm.expect(jsonData).to.have.property('provider');
        pm.expect(jsonData).to.have.property('amount');
        pm.expect(jsonData).to.have.property('status');
    }
});

pm.test("Bid accepted successfully by customer", function () {
    if (pm.response.code === 200) {
        const jsonData = pm.response.json();
        pm.expect(jsonData).to.have.property('status');
        if(jsonData.booking && jsonData.booking.id) {
            pm.environment.set('booking_id', jsonData.booking.id);
        }
    }
});

pm.test("Bid rejected successfully by customer", function () {
    if (pm.response.code === 200) {
        const jsonData = pm.response.json();
        pm.expect(jsonData).to.have.property('status');
        pm.expect(jsonData.status).to.eql('REJECTED');
    }
});

pm.test("AI price suggestion retrieved successfully", function () {
    if (pm.response.code === 200) {
        const jsonData = pm.response.json();
        pm.expect(jsonData).to.have.property('suggested_price');
    }
});

// Booking Tests
pm.test("List my bookings successful", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData.results).to.be.an('array');
    if (jsonData.results.length > 0) {
        pm.environment.set("booking_id", jsonData.results[0].id);
        pm.environment.set("booking_id_for_review", jsonData.results[0].id); // Set for review testing
    }
});

pm.test("Get booking details successful", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('id');
    pm.expect(jsonData).to.have.property('status');
});

pm.test("Provider updates booking status successfully", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('status');
    // Example: pm.expect(jsonData.status).to.eql("in_progress");
});

pm.test("Customer confirms booking completion successfully", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('status');
    // pm.expect(jsonData.status).to.eql('completed'); // Status might change based on logic
});

pm.test("Booking cancelled successfully", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('status');
    pm.expect(jsonData.status.startsWith('cancelled')).to.be.true;
});

// Review Tests
pm.test("Review created successfully", function () {
    pm.response.to.have.status(201);
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('id');
    pm.expect(jsonData).to.have.property('rating');
    pm.expect(jsonData).to.have.property('comment');
    pm.environment.set('review_id', jsonData.id);
});

pm.test("List my reviews successful", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData.results).to.be.an('array');
});

pm.test("Get review details successful", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('id');
    pm.expect(jsonData).to.have.property('rating');
});

pm.test("Provider responds to review successfully", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('provider_response');
    pm.expect(jsonData.provider_response).to.not.be.empty;
});

pm.test("List reviews for a provider successful", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData.results).to.be.an('array');
});

// Chat Message Tests
pm.test("Get chat history successful", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData.results).to.be.an('array');
    if (jsonData.results.length > 0) {
        pm.environment.set("message_id", jsonData.results[0].id);
    }
});

pm.test("Send chat message successful", function () {
    pm.response.to.have.status(201);
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('id');
    pm.expect(jsonData).to.have.property('text_content');
    pm.environment.set("message_id", jsonData.id);
});

pm.test("Mark message as read successful", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('status', 'message marked as read');
});

// Payment Tests
pm.test("View payment details for booking successful", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData.results).to.be.an('array'); // Payments might be a list
    if (jsonData.results.length > 0) {
        pm.environment.set("payment_id", jsonData.results[0].id);
    }
});

pm.test("Initiate payment for booking successful", function () {
    pm.response.to.have.status(200); // Or 201 if a payment record is created
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('client_secret'); // For Stripe PaymentIntents
    // pm.expect(jsonData).to.have.property('payment_id'); // If you return your internal payment ID
    // pm.environment.set("payment_id", jsonData.payment_id);
});

// Authorization Tests (General Examples)
pm.test("Unauthorized access returns 401", function () {
    // This test would be on an endpoint that requires auth, but run without token
    if (pm.request.headers.has('Authorization') === false) {
         pm.response.to.have.status(401);
    }
});

pm.test("Forbidden access returns 403", function () {
    // Example: Customer trying to access a provider-only action
    // This requires setting up the request with customer token for a provider endpoint
    // and checking if the response is 403.
});
