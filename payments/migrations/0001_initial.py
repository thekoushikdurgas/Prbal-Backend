# Generated by Django 5.2.1 on 2025-01-27 12:00

from django.conf import settings
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('bookings', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentGatewayAccount',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('account_type', models.CharField(choices=[('stripe', 'Stripe Connect'), ('paypal', 'PayPal'), ('bank', 'Direct Bank Transfer'), ('other', 'Other')], max_length=20)),
                ('account_id', models.CharField(help_text='External account ID in the payment gateway', max_length=255)),
                ('is_verified', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('account_details', models.JSONField(blank=True, default=dict, help_text='Additional account details as JSON')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_accounts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Payment Gateway Account',
                'verbose_name_plural': 'Payment Gateway Accounts',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='Unique identifier for the payment transaction', primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, help_text='Amount of the transaction', max_digits=10)),
                ('currency', models.CharField(choices=[('INR', 'Indian Rupee'), ('USD', 'US Dollar'), ('EUR', 'Euro'), ('GBP', 'British Pound')], default='INR', help_text='Currency of the transaction', max_length=3)),
                ('payment_method', models.CharField(choices=[('credit_card', 'Credit Card'), ('debit_card', 'Debit Card'), ('bank_transfer', 'Bank Transfer'), ('upi', 'UPI'), ('wallet', 'Wallet'), ('paypal', 'PayPal'), ('cash', 'Cash'), ('other', 'Other')], help_text='Method used for payment', max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed'), ('refunded', 'Refunded'), ('cancelled', 'Cancelled')], default='pending', help_text='Status of the transaction', max_length=20)),
                ('transaction_id', models.CharField(blank=True, help_text='External transaction ID from payment processor', max_length=100, null=True)),
                ('payment_date', models.DateTimeField(auto_now_add=True, help_text='Date and time of the payment')),
                ('platform_fee', models.DecimalField(decimal_places=2, default=0.0, help_text='Fee charged by the platform', max_digits=10)),
                ('notes', models.TextField(blank=True, help_text='Additional notes about the payment', null=True)),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Additional transaction metadata as JSON', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('booking', models.ForeignKey(help_text='Related booking for this payment', on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='bookings.booking')),
                ('payee', models.ForeignKey(help_text='User receiving the payment', on_delete=django.db.models.deletion.CASCADE, related_name='payments_received', to=settings.AUTH_USER_MODEL)),
                ('payer', models.ForeignKey(help_text='User making the payment', on_delete=django.db.models.deletion.CASCADE, related_name='payments_made', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(help_text='User initiating the payment', on_delete=django.db.models.deletion.CASCADE, related_name='payments_initiated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Payment',
                'verbose_name_plural': 'Payments',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Payout',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('transaction_fee', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('net_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('transaction_id', models.CharField(blank=True, max_length=100, null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('notes', models.TextField(blank=True, null=True)),
                ('external_reference', models.CharField(blank=True, help_text='Reference ID in external payment system', max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('payment_account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payouts', to='payments.paymentgatewayaccount')),
                ('provider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payouts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Payout',
                'verbose_name_plural': 'Payouts',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='paymentgatewayaccount',
            constraint=models.UniqueConstraint(fields=('user', 'account_type'), name='payments_paymentgatewayaccount_user_account_type_uniq'),
        ),
    ] 