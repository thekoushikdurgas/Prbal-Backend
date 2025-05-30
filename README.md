# Prbal App Backend

This is the backend API for the Prbal App, a service marketplace platform built with Django and Django REST Framework. The backend provides RESTful APIs, real-time communication capabilities, and secure authentication for the Flutter frontend.

## Project Setup

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Virtual environment
- PostgreSQL database (using Supabase)
- Redis server (for Channels/WebSockets)

### Environment Setup

1. Create and activate a virtual environment:
```
python -m venv venv
venv\Scripts\activate  # On Windows
source venv/bin/activate  # On macOS/Linux
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Configure environment variables:
Create a `.env` file in the project root with the following variables:
```
# Django settings
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database settings
DB_NAME=postgres
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_HOST=your-db-host
DB_PORT=5432

# Redis settings (for Channels)
REDIS_HOST=localhost
REDIS_PORT=6379

# Stripe settings
STRIPE_PUBLISHABLE_KEY=your-publishable-key-here
STRIPE_SECRET_KEY=your-secret-key-here
STRIPE_WEBHOOK_SECRET=your-webhook-secret-here

# Frontend URL
FRONTEND_URL=http://localhost:3000

# Email settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
```

4. Run migrations:
```
python manage.py makemigrations
python manage.py migrate
```

5. Create a superuser:
```
python manage.py createsuperuser
```

6. Run the development server:
```
python manage.py runserver
```

## Project Structure

- `prbal_project/`: Main project directory containing settings and configuration
- `api/`: Main application directory containing models, views, and serializers
  - `models.py`: Database models (ServiceCategory, Service, etc.)
  - `views.py`: API viewsets and endpoints
  - `serializers.py`: Model serializers for API responses
  - `urls.py`: API URL routing

## API Endpoints

### Admin & Documentation
- `/admin/`: Django admin interface
- `/swagger/`: Interactive API documentation (Swagger UI)
- `/redoc/`: Alternative API documentation (ReDoc)

### Authentication
- `/api/token/`: Obtain JWT token pair (access and refresh tokens)
- `/api/token/refresh/`: Refresh JWT token
- `/api/token/verify/`: Verify JWT token
- `/api-auth/`: DRF browsable API authentication

### API Resources
- `/api/users/`: User listing and details
- `/api/categories/`: Service categories
- `/api/services/`: Services offered in the marketplace

## Database Configuration

The project uses Django's ORM with PostgreSQL as the database backend. The database connection is configured using the DB_* environment variables in your .env file. The project is set up to work with Supabase PostgreSQL.

## Features

- **RESTful API**: Built with Django REST Framework
- **JWT Authentication**: Secure token-based authentication
- **PostgreSQL Database**: Robust relational database with Supabase
- **Real-time Communication**: WebSockets support via Django Channels
- **API Documentation**: Interactive Swagger/OpenAPI documentation
- **CORS Support**: Cross-Origin Resource Sharing enabled
- **Payment Processing**: Stripe integration
- **Email Notifications**: SMTP email configuration
- **Static File Handling**: WhiteNoise for efficient static file serving

## Next Steps for Development

1. Create additional models for orders, reviews, and payments
2. Implement custom user profiles and authentication flows
3. Set up WebSocket consumers for real-time features
4. Implement file upload functionality for service images
5. Add advanced filtering and search functionality
6. Set up automated testing and CI/CD pipeline
7. Implement caching for improved performance
