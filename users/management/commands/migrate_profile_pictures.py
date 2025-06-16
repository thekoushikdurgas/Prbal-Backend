import os
import shutil
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth import get_user_model
from pathlib import Path

User = get_user_model()


class Command(BaseCommand):
    help = 'Migrate existing profile pictures to new user-specific directory structure'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually moving files',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even if destination files exist',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('Running in DRY RUN mode - no files will be moved')
            )
        
        # Get media root
        media_root = Path(settings.MEDIA_ROOT)
        old_profile_dir = media_root / 'profile_pictures'
        
        if not old_profile_dir.exists():
            self.stdout.write(
                self.style.ERROR(f'Profile pictures directory not found: {old_profile_dir}')
            )
            return
        
        # Get all users with profile pictures
        users_with_pictures = User.objects.filter(profile_picture__isnull=False).exclude(profile_picture='')
        
        self.stdout.write(
            self.style.SUCCESS(f'Found {users_with_pictures.count()} users with profile pictures')
        )
        
        migrated_count = 0
        error_count = 0
        skipped_count = 0
        
        for user in users_with_pictures:
            try:
                # Get current file path
                old_file_path = media_root / user.profile_picture.name
                
                if not old_file_path.exists():
                    self.stdout.write(
                        self.style.WARNING(f'File not found for user {user.username}: {old_file_path}')
                    )
                    error_count += 1
                    continue
                
                # Check if file is already in user-specific directory
                if f'profile_pictures/{user.id}/' in str(user.profile_picture.name):
                    self.stdout.write(
                        self.style.SUCCESS(f'User {user.username} already migrated, skipping')
                    )
                    skipped_count += 1
                    continue
                
                # Create new file path
                filename = old_file_path.name
                new_user_dir = old_profile_dir / str(user.id)
                new_file_path = new_user_dir / filename
                
                # Create user directory if it doesn't exist
                if not dry_run:
                    new_user_dir.mkdir(exist_ok=True)
                
                # Check if destination file already exists
                if new_file_path.exists() and not force:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Destination file already exists for user {user.username}: {new_file_path}'
                            f'\nUse --force to overwrite'
                        )
                    )
                    skipped_count += 1
                    continue
                
                if dry_run:
                    self.stdout.write(
                        f'Would move: {old_file_path} -> {new_file_path}'
                    )
                else:
                    # Move the file
                    shutil.move(str(old_file_path), str(new_file_path))
                    
                    # Update database record
                    new_relative_path = f'profile_pictures/{user.id}/{filename}'
                    user.profile_picture.name = new_relative_path
                    user.save(update_fields=['profile_picture'])
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'Migrated user {user.username}: {filename}')
                    )
                
                migrated_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error migrating user {user.username}: {str(e)}')
                )
                error_count += 1
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('MIGRATION SUMMARY'))
        self.stdout.write('='*50)
        
        if dry_run:
            self.stdout.write(f'Files that would be migrated: {migrated_count}')
        else:
            self.stdout.write(f'Files migrated: {migrated_count}')
        
        self.stdout.write(f'Files skipped: {skipped_count}')
        self.stdout.write(f'Errors encountered: {error_count}')
        
        if dry_run:
            self.stdout.write('\nTo actually perform the migration, run without --dry-run')
        elif migrated_count > 0:
            self.stdout.write('\n' + self.style.SUCCESS('Migration completed successfully!'))
            self.stdout.write('Note: You may want to clean up any empty directories in the old structure.')
        
        # Check for orphaned files
        if not dry_run:
            self.check_orphaned_files(old_profile_dir)
    
    def check_orphaned_files(self, profile_dir):
        """Check for files that weren't migrated"""
        orphaned_files = []
        
        for file_path in profile_dir.rglob('*'):
            if file_path.is_file():
                # Skip files that are already in user subdirectories
                relative_path = file_path.relative_to(profile_dir)
                if len(relative_path.parts) == 1:  # File is in root of profile_pictures
                    orphaned_files.append(file_path)
        
        if orphaned_files:
            self.stdout.write('\n' + self.style.WARNING('ORPHANED FILES FOUND:'))
            self.stdout.write(f'Found {len(orphaned_files)} files that were not migrated:')
            for file_path in orphaned_files[:10]:  # Show first 10
                self.stdout.write(f'  - {file_path.name}')
            
            if len(orphaned_files) > 10:
                self.stdout.write(f'  ... and {len(orphaned_files) - 10} more')
            
            self.stdout.write('These files may be from deleted users or upload errors.')
            self.stdout.write('Review them manually before deletion.') 