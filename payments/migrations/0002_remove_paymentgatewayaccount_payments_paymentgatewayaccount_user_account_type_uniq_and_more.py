# Generated by Django 5.2.3 on 2025-06-15 03:32

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='paymentgatewayaccount',
            name='payments_paymentgatewayaccount_user_account_type_uniq',
        ),
        migrations.AlterUniqueTogether(
            name='paymentgatewayaccount',
            unique_together={('user', 'account_type')},
        ),
    ]
