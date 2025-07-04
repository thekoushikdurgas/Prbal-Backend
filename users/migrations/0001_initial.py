# Generated by Django 4.2.0

import uuid
import django.contrib.postgres.search
from django.contrib.postgres.indexes import GinIndex
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        # Create User model
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=150, unique=True)),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email address')),
                ('first_name', models.CharField(blank=True, max_length=150)),
                ('last_name', models.CharField(blank=True, max_length=150)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('user_type', models.CharField(choices=[('customer', 'Customer'), ('provider', 'Service Provider'), ('admin', 'Administrator')], default='customer', max_length=20)),
                ('phone_number', models.CharField(blank=True, max_length=15, null=True, unique=True)),
                # PIN Authentication fields
                ('pin', models.CharField(help_text='4-digit PIN for authentication (hashed)', max_length=128)),
                ('pin_created_at', models.DateTimeField(auto_now_add=True)),
                ('pin_updated_at', models.DateTimeField(auto_now=True)),
                ('failed_pin_attempts', models.IntegerField(default=0)),
                ('pin_locked_until', models.DateTimeField(blank=True, null=True)),
                # Verification fields
                ('is_verified', models.BooleanField(default=False)),
                ('is_email_verified', models.BooleanField(default=False)),
                ('is_phone_verified', models.BooleanField(default=False)),
                # Profile fields
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='profile_pictures/')),
                ('bio', models.TextField(blank=True, null=True)),
                ('location', models.CharField(blank=True, max_length=100, null=True)),
                ('address', models.TextField(blank=True, null=True)),
                # Provider specific fields
                ('rating', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=3, null=True)),
                ('total_bookings', models.IntegerField(default=0)),
                ('skills', models.JSONField(blank=True, default=dict, null=True)),
                # User preferences and financial info
                ('preferences', models.JSONField(blank=True, default=dict, null=True)),
                ('balance', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                # Timestamps
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                # Search vector field (PostgreSQL specific)
                ('search_vector', django.contrib.postgres.search.SearchVectorField(blank=True, editable=False, null=True)),
                # Django permissions
                ('groups', models.ManyToManyField(
                    blank=True,
                    help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
                    related_name='user_set',
                    related_query_name='user',
                    to='auth.group',
                    verbose_name='groups'
                )),
                ('user_permissions', models.ManyToManyField(
                    blank=True,
                    help_text='Specific permissions for this user.',
                    related_name='user_set',
                    related_query_name='user',
                    to='auth.permission',
                    verbose_name='user permissions'
                )),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        
        # Create Pass model
        migrations.CreateModel(
            name='Pass',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user_passed', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='passes_received', to='users.user')),
                ('user_passing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='passes_made', to='users.user')),
            ],
            options={
                'verbose_name': 'Pass',
                'verbose_name_plural': 'Passes',
            },
        ),
        
        # Create AccessToken model
        migrations.CreateModel(
            name='AccessToken',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('token_jti', models.CharField(help_text='JWT token ID', max_length=255, unique=True)),
                ('device_type', models.CharField(choices=[('web', 'Web Browser'), ('mobile', 'Mobile App'), ('tablet', 'Tablet'), ('desktop', 'Desktop App'), ('other', 'Other')], default='web', max_length=20)),
                ('device_name', models.CharField(blank=True, help_text='User agent or device identifier', max_length=255, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_used_at', models.DateTimeField(auto_now=True)),
                ('last_refreshed_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='access_tokens', to='users.user')),
            ],
            options={
                'verbose_name': 'Access Token',
                'verbose_name_plural': 'Access Tokens',
                'ordering': ['-created_at'],
            },
        ),
        
        # Add unique constraint for Pass model
        migrations.AddConstraint(
            model_name='pass',
            constraint=models.UniqueConstraint(fields=('user_passing', 'user_passed'), name='unique_user_pass'),
        ),
        
        # Add GIN index for search_vector field (PostgreSQL specific)
        migrations.AddIndex(
            model_name='user',
            index=GinIndex(fields=['search_vector'], name='user_search_vector_idx'),
        ),
        
        # Add database indexes for performance
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['user_type'], name='users_user_type_idx'),
        ),
        
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['is_verified'], name='users_user_verified_idx'),
        ),
        
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['created_at'], name='users_user_created_idx'),
        ),
        
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['rating'], name='users_user_rating_idx'),
        ),
        
        migrations.AddIndex(
            model_name='accesstoken',
            index=models.Index(fields=['user', 'is_active'], name='users_accesstoken_user_active_idx'),
        ),
        
        migrations.AddIndex(
            model_name='accesstoken',
            index=models.Index(fields=['created_at'], name='users_accesstoken_created_idx'),
        ),
    ] 