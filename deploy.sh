#!/bin/bash

# Django Production Deployment Script
set -e

echo "🚀 Starting Django Production Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/path/to/your/Prbal_backend"
VENV_DIR="$PROJECT_DIR/venv"
REQUIREMENTS_FILE="$PROJECT_DIR/requirements.txt"
SERVICE_NAME="prbal-backend"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check if .env file exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    print_error ".env file not found! Please create it from production.env.example"
    exit 1
fi

print_status "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

print_status "Installing/updating dependencies..."
pip install --upgrade pip
pip install -r "$REQUIREMENTS_FILE" --no-cache-dir

print_status "Running Django checks..."
cd "$PROJECT_DIR"
python manage.py check --deploy

print_status "Collecting static files..."
python manage.py collectstatic --noinput --clear

print_status "Running database migrations..."
python manage.py migrate --noinput

print_status "Creating cache table..."
python manage.py createcachetable || true

print_status "Compiling messages (if any)..."
python manage.py compilemessages || true

print_status "Testing Django configuration..."
python manage.py check

# Test database connection
print_status "Testing database connection..."
python manage.py dbshell --command="SELECT 1;" || {
    print_error "Database connection failed!"
    exit 1
}

print_status "Restarting application service..."
sudo systemctl restart "$SERVICE_NAME"

print_status "Waiting for service to start..."
sleep 5

# Check if service is running
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    print_status "✅ Service is running successfully!"
else
    print_error "❌ Service failed to start!"
    sudo systemctl status "$SERVICE_NAME"
    exit 1
fi

print_status "Reloading nginx..."
sudo nginx -t && sudo systemctl reload nginx

print_status "🎉 Deployment completed successfully!"
print_status "🔍 Check logs with: sudo journalctl -u $SERVICE_NAME -f"

# Optional: Run some basic health checks
print_status "Running health checks..."
sleep 2

# Check if the application responds
if curl -f -s http://localhost:8000/health/ > /dev/null; then
    print_status "✅ Application health check passed!"
else
    print_warning "⚠️ Application health check failed - check logs"
fi

print_status "Deployment script finished!" 