"""
This script will help fix the migration conflict by manually marking the problematic migration
as applied in the django_migrations table.
"""
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Prbal_backend.settings')
django.setup()

# Run after Django is set up
from django.db import connection

# Insert the problematic migration into the django_migrations table to mark it as applied
with connection.cursor() as cursor:
    # Check if the migration is already in the table
    cursor.execute(
        "SELECT id FROM django_migrations WHERE app = 'api' AND name = '0002_service_model_enhancement'"
    )
    if not cursor.fetchone():
        # If not, insert it
        cursor.execute(
            "INSERT INTO django_migrations (app, name, applied) VALUES ('api', '0002_service_model_enhancement', NOW())"
        )
        print("Migration 'api.0002_service_model_enhancement' has been marked as applied.")
    else:
        print("Migration 'api.0002_service_model_enhancement' is already marked as applied.")

print("Now try running 'python manage.py migrate' again.")
