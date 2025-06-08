from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Set default PIN (1234) for existing users who do not have a PIN set'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pin',
            type=str,
            default='1234',
            help='PIN to set for users (default: 1234)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        pin = options['pin']
        dry_run = options['dry_run']

        # Validate PIN
        if len(pin) != 4 or not pin.isdigit():
            self.stdout.write(
                self.style.ERROR('PIN must be exactly 4 digits')
            )
            return

        # Find users with empty or null PIN
        users_to_update = User.objects.filter(
            is_active=True,
            pin__in=['', None]
        )
        
        self.stdout.write(f'Found {users_to_update.count()} users without PIN')

        if users_to_update.count() == 0:
            self.stdout.write(
                self.style.SUCCESS('No users need PIN updates')
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN - No changes will be made')
            )
            for user in users_to_update[:10]:
                self.stdout.write(f'Would update: {user.username} ({user.email})')
            if users_to_update.count() > 10:
                self.stdout.write(f'... and {users_to_update.count() - 10} more users')
            return

        # Update users
        updated_count = 0
        failed_count = 0

        self.stdout.write('Starting PIN updates...')

        for user in users_to_update:
            try:
                user.set_pin(pin)
                user.save()
                updated_count += 1
                
                if updated_count % 50 == 0:
                    self.stdout.write(f'Updated {updated_count} users...')
                    
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'Failed to update {user.username}: {e}')
                )

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'PIN update completed: {updated_count} users updated, {failed_count} failed'
            )
        ) 