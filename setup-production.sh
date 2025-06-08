#!/bin/bash

# Initial Production Setup Script for Django + Gunicorn + Nginx
set -e

echo "🔧 Setting up Django Production Environment..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This setup script must be run as root"
   exit 1
fi

print_status "Updating system packages..."
apt update && apt upgrade -y

print_status "Installing system dependencies..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    postgresql \
    postgresql-contrib \
    nginx \
    supervisor \
    git \
    curl \
    build-essential \
    libpq-dev \
    gettext \
    certbot \
    python3-certbot-nginx

print_status "Creating application user..."
useradd --system --shell /bin/bash --home /opt/prbal --create-home prbal || true
usermod -aG www-data prbal

print_status "Setting up PostgreSQL..."
sudo -u postgres createuser --createdb --pwprompt prbal || true
sudo -u postgres createdb --owner=prbal prbal_production || true

print_status "Creating application directories..."
mkdir -p /opt/prbal/app
mkdir -p /opt/prbal/logs
mkdir -p /var/log/prbal
chown -R prbal:www-data /opt/prbal
chown -R prbal:www-data /var/log/prbal

print_status "Setting up Python virtual environment..."
sudo -u prbal python3 -m venv /opt/prbal/venv
sudo -u prbal /opt/prbal/venv/bin/pip install --upgrade pip setuptools wheel

print_status "Installing Python packages..."
sudo -u prbal /opt/prbal/venv/bin/pip install gunicorn

print_status "Setting up systemd service..."
if [ -f "prbal-backend.service" ]; then
    # Update paths in service file
    sed -i 's|/path/to/your/Prbal_backend|/opt/prbal/app|g' prbal-backend.service
    sed -i 's|User=www-data|User=prbal|g' prbal-backend.service
    sed -i 's|Group=www-data|Group=prbal|g' prbal-backend.service
    
    cp prbal-backend.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable prbal-backend
    print_status "✅ Systemd service configured"
else
    print_warning "prbal-backend.service file not found - create it manually"
fi

print_status "Setting up nginx..."
if [ -f "nginx-prbal.conf" ]; then
    # Update paths in nginx config
    sed -i 's|/path/to/your/Prbal_backend|/opt/prbal/app|g' nginx-prbal.conf
    
    cp nginx-prbal.conf /etc/nginx/sites-available/prbal
    ln -sf /etc/nginx/sites-available/prbal /etc/nginx/sites-enabled/
    
    # Remove default nginx site
    rm -f /etc/nginx/sites-enabled/default
    
    nginx -t
    systemctl enable nginx
    print_status "✅ Nginx configured"
else
    print_warning "nginx-prbal.conf file not found - create it manually"
fi

print_status "Setting up log rotation..."
cat > /etc/logrotate.d/prbal << EOF
/var/log/prbal/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 0644 prbal prbal
    postrotate
        systemctl reload prbal-backend
    endscript
}
EOF

print_status "Setting up firewall..."
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable

print_status "Creating deployment directory structure..."
sudo -u prbal mkdir -p /opt/prbal/app/{media,staticfiles,logs}

print_status "Setting proper permissions..."
chmod 755 /opt/prbal
chmod 755 /opt/prbal/app
chmod 775 /opt/prbal/app/media
chmod 775 /opt/prbal/app/staticfiles
chmod 755 /opt/prbal/logs

print_status "🎉 Production environment setup completed!"
print_status ""
print_status "Next steps:"
print_status "1. Copy your Django application to /opt/prbal/app/"
print_status "2. Create /opt/prbal/app/.env file with production settings"
print_status "3. Install requirements: sudo -u prbal /opt/prbal/venv/bin/pip install -r requirements.txt"
print_status "4. Run migrations: sudo -u prbal /opt/prbal/venv/bin/python manage.py migrate"
print_status "5. Collect static files: sudo -u prbal /opt/prbal/venv/bin/python manage.py collectstatic"
print_status "6. Start the service: systemctl start prbal-backend"
print_status "7. Get SSL certificate: certbot --nginx -d your-domain.com"
print_status ""
print_status "Monitor with: journalctl -u prbal-backend -f" 