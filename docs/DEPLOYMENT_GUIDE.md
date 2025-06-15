# 🚀 Django Production Deployment Guide with Gunicorn

## Overview

This guide provides step-by-step instructions for deploying your Prbal Django application to production using Gunicorn as the WSGI server. Your application is already well-configured for production with security, monitoring, and performance optimizations.

## 📋 Prerequisites

- Python 3.9+
- PostgreSQL database
- Domain name (for SSL certificates)
- Server with at least 2GB RAM

## 🖥️ Platform-Specific Instructions

### For Windows Development/Testing

#### Quick Setup

```bash
# Run the setup script
setup-dev.bat

# Start development server
python manage.py runserver

# For production testing on Windows
deploy.bat
```

### For Linux Production Server

#### Initial Server Setup

```bash
# Run the production setup (as root)
sudo ./setup-production.sh

# Copy your application files
sudo cp -r /path/to/your/source/* /opt/prbal/app/
sudo chown -R prbal:prbal /opt/prbal/app/
```

## 🔧 Configuration Steps

### 1. Environment Configuration

Create your `.env` file from the template:

```bash
# Copy the template
cp production.env.example .env

# Edit with your actual values
nano .env
```

**Required Environment Variables:**

```env
# Django Core
SECRET_KEY=your-super-secret-key-minimum-50-characters
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,your-server-ip

# Database
DB_NAME=prbal_production
DB_USER=prbal_user
DB_PASSWORD=your-strong-password
DB_HOST=localhost
DB_PORT=5432

# Frontend
FRONTEND_URL=https://your-frontend-domain.com

# Security
SENTRY_DSN=https://your-sentry-dsn
```

### 2. Database Setup

```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE prbal_production;
CREATE USER prbal_user WITH PASSWORD 'your-strong-password';
GRANT ALL PRIVILEGES ON DATABASE prbal_production TO prbal_user;
\q
```

### 3. Python Environment Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux
# OR
venv\Scripts\activate.bat  # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## 🚢 Deployment Process

### Option 1: Automated Deployment (Recommended)

#### For Linux:

```bash
# Make scripts executable
chmod +x deploy.sh setup-production.sh

# Initial setup (run once as root)
sudo ./setup-production.sh

# Deploy application
./deploy.sh
```

#### For Windows:

```batch
REM Initial setup
setup-dev.bat

REM Deploy for production testing
deploy.bat
```

### Option 2: Manual Deployment

#### Step 1: Prepare Application

```bash
# Activate virtual environment
source venv/bin/activate

# Run security checks
python manage.py check --deploy

# Collect static files
python manage.py collectstatic --noinput --clear

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

#### Step 2: Start Gunicorn Server

```bash
# Start with configuration file (recommended)
gunicorn -c gunicorn.conf.py prbal_project.wsgi:application

# OR start with custom settings
gunicorn prbal_project.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 30 \
    --max-requests 1000 \
    --preload
```

#### Step 3: Process Management (Linux)

**Using systemd (recommended):**
```bash
# Copy service file
sudo cp prbal-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable prbal-backend
sudo systemctl start prbal-backend

# Check status
sudo systemctl status prbal-backend

# View logs
sudo journalctl -u prbal-backend -f
```

**Using Supervisor (alternative):**
```bash
# Install supervisor
sudo apt install supervisor

# Create config file
sudo nano /etc/supervisor/conf.d/prbal.conf
```

```ini
[program:prbal]
command=/opt/prbal/venv/bin/gunicorn -c /opt/prbal/app/gunicorn.conf.py prbal_project.wsgi:application
directory=/opt/prbal/app
user=prbal
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/prbal/gunicorn.log
```

## 🌐 Web Server Configuration

### Nginx Setup (Recommended)

```bash
# Install Nginx
sudo apt install nginx

# Copy configuration
sudo cp nginx-prbal.conf /etc/nginx/sites-available/prbal
sudo ln -s /etc/nginx/sites-available/prbal /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Start Nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### SSL Certificate Setup

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Monitoring and Health Checks

### Built-in Health Endpoints

Your application includes several health check endpoints:

```bash
# Basic health check
curl http://localhost:8000/health/

# Database health check
curl http://localhost:8000/health/db/

# Prometheus metrics
curl http://localhost:8000/metrics/
```

### Log Monitoring

```bash
# Application logs
sudo journalctl -u prbal-backend -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Application logs (if using file logging)
tail -f /var/log/prbal/django.log
```

## 🔧 Performance Tuning

### Gunicorn Workers

The number of workers is automatically calculated in `gunicorn.conf.py`:
```python
workers = multiprocessing.cpu_count() * 2 + 1
```

**Manual adjustment:**
```bash
# For CPU-intensive apps
workers = cpu_count()

# For I/O intensive apps (recommended for Django)
workers = cpu_count() * 2 + 1
```

### Database Connection Pool

Enable in your `.env`:
```env
USE_DB_POOL=True
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

### Memory Management

Monitor memory usage and adjust worker restart settings:
```python
# In gunicorn.conf.py
max_requests = 1000
max_requests_jitter = 50
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Permission Denied

```bash
# Fix file permissions
sudo chown -R prbal:prbal /opt/prbal/
sudo chmod -R 755 /opt/prbal/app/
sudo chmod -R 775 /opt/prbal/app/media/
```

#### 2. Database Connection Failed

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
python manage.py dbshell
```

#### 3. Static Files Not Loading

```bash
# Collect static files again
python manage.py collectstatic --noinput --clear

# Check Nginx configuration
sudo nginx -t
```

#### 4. Gunicorn Won't Start

```bash
# Check configuration
gunicorn -c gunicorn.conf.py --check-config prbal_project.wsgi:application

# Run in debug mode
gunicorn -c gunicorn.conf.py prbal_project.wsgi:application --log-level debug
```

### Performance Issues

#### 1. Slow Response Times

```bash
# Check database queries
python manage.py shell
from django.db import connection
print(connection.queries)

# Monitor with Prometheus metrics
curl http://localhost:8000/metrics/ | grep django
```

#### 2. High Memory Usage

```bash
# Monitor memory
htop
free -h

# Reduce worker count or add more RAM
```

## 🔒 Security Checklist

### Essential Security Settings

- [x] `DEBUG=False` in production
- [x] Strong `SECRET_KEY` (minimum 50 characters)
- [x] HTTPS enabled with SSL certificates
- [x] Firewall configured (ports 80, 443, 22 only)
- [x] Database user with limited privileges
- [x] Regular security updates
- [x] Sentry error tracking configured
- [x] Log monitoring in place

### Advanced Security Features (Already Configured)

- [x] **HSTS Headers**: Force HTTPS for 1 year (`SECURE_HSTS_SECONDS`)
- [x] **Content Security Policy**: Prevent XSS attacks
- [x] **Rate Limiting**: API throttling configured
- [x] **CORS**: Properly configured for frontend domain
- [x] **JWT Security**: Token rotation and blacklisting
- [x] **Session Security**: Secure cookies in production
- [x] **XSS Protection**: Browser XSS filter enabled
- [x] **Clickjacking Protection**: X-Frame-Options set to DENY

### Django 5.2+ Security Compliance

```bash
# Run the comprehensive security check
python manage.py check --deploy --fail-level WARNING

# Verify HTTPS redirects
curl -I http://yourdomain.com

# Test security headers
curl -I https://yourdomain.com
```

## 🐳 Docker Deployment (Alternative)

Your application includes Docker support for containerized deployment:

### Quick Docker Setup

```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.prod.yml up --build -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Run migrations in container
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### Docker Production Benefits

- **Consistency**: Same environment across development and production
- **Scalability**: Easy horizontal scaling with orchestration
- **Isolation**: Container-level security and resource management
- **Portability**: Deploy on any Docker-compatible platform

## 📈 Scaling Considerations

### Horizontal Scaling

```bash
# Multiple Gunicorn instances
# Use load balancer (Nginx, HAProxy)
# Shared database and media storage
# Docker Swarm or Kubernetes orchestration
```

### Vertical Scaling

```bash
# Increase server resources
# Adjust worker count in gunicorn.conf.py
# Optimize database queries and indexing
# Implement database read replicas
```

## 🎯 Quick Commands Reference

### Development

```bash
python manage.py runserver          # Development server
python manage.py shell              # Django shell
python manage.py check --deploy     # Security checks
```

### Production

```bash
gunicorn -c gunicorn.conf.py prbal_project.wsgi:application  # Start production server
sudo systemctl restart prbal-backend                        # Restart service
sudo systemctl status prbal-backend                         # Check status
sudo journalctl -u prbal-backend -f                         # View logs
```

### Maintenance

```bash
python manage.py migrate                    # Run migrations
python manage.py collectstatic --noinput    # Collect static files
python manage.py clearsessions              # Clear expired sessions
python manage.py check                      # Health check
```

### Safe Database Migrations in Production

```bash
# 1. Always backup database first
pg_dump prbal_production > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Check migration plan
python manage.py showmigrations
python manage.py sqlmigrate app_name migration_number

# 3. Run migrations with monitoring
python manage.py migrate --verbosity=2

# 4. Rollback if needed (create rollback migration first)
python manage.py migrate app_name previous_migration_number
```

## 📞 Support

For deployment issues:
1. Check logs first: `sudo journalctl -u prbal-backend -f`
2. Verify configuration: `python manage.py check --deploy`
3. Test health endpoints: `curl http://localhost:8000/health/`

---

## 🚀 Quick Start Commands

**For immediate deployment testing:**

```bash
# 1. Setup environment
cp production.env.example .env
# Edit .env with your values

# 2. Setup and deploy
./setup-dev.bat              # Windows
# OR
./setup-production.sh        # Linux (as root)

# 3. Start production server
./deploy.bat                 # Windows
# OR  
./deploy.sh                  # Linux

# 4. Access your application
# http://localhost:8000/health/    (health check)
# http://localhost:8000/admin/     (admin panel)
# http://localhost:8000/docs/      (API documentation)
```

Your Django application is now ready for production! 🎉 

## 🔧 Deployment Options

### WSGI Deployment (Current - Synchronous)

Your application currently uses Gunicorn with WSGI for synchronous request handling, which is suitable for most traditional web applications.

### ASGI Deployment (Future-Ready - Asynchronous)

For applications requiring real-time features, WebSockets, or async operations, consider ASGI deployment:

```bash
# Using Daphne (recommended for Django Channels)
daphne -b 0.0.0.0 -p 8000 prbal_project.asgi:application

# Using Uvicorn (high performance)
uvicorn prbal_project.asgi:application --host 0.0.0.0 --port 8000 --workers 4

# Using Hypercorn (HTTP/2 support)
hypercorn prbal_project.asgi:application --bind 0.0.0.0:8000
```

**Note**: Your app already has ASGI configuration with Channels support, making it ready for async deployment when needed. 