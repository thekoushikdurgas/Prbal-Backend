#!/usr/bin/env python3
"""
Windows-compatible server runner using Waitress
This replaces Gunicorn for Windows environments
"""

import os
import sys
import multiprocessing
from waitress import serve

# Ensure Django settings are loaded
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prbal_project.settings')

# Import Django WSGI application
try:
    from prbal_project.wsgi import application
except ImportError:
    print("Error: Could not import Django WSGI application.")
    print("Make sure you're in the correct directory and Django is installed.")
    sys.exit(1)

def run_server():
    """Start the Waitress server with optimized settings for production"""
    
    # Calculate optimal thread count based on CPU cores
    cpu_count = multiprocessing.cpu_count()
    threads = cpu_count * 2 + 1
    
    print(f"Starting Prbal Backend Server...")
    print(f"CPU cores detected: {cpu_count}")
    print(f"Using {threads} threads")
    print(f"Server will be available at: http://0.0.0.0:8000")
    print(f"Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Start Waitress server with production-ready configuration
        serve(
            application,
            host='0.0.0.0',
            port=8000,
            threads=threads,
            connection_limit=1000,
            cleanup_interval=30,
            channel_timeout=120,
            log_untrusted_proxy_headers=True,
            clear_untrusted_proxy_headers=True,
            # Enable IPv6 if needed
            # ipv6=True,
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_server() 