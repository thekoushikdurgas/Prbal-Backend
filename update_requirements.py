#!/usr/bin/env python3
"""
Requirements Management Script for Prbal Backend
Helps update, check, and manage Python dependencies safely.
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description=""):
    """Execute a shell command and return the result."""
    print(f"\n🔄 {description or command}")
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, check=True
        )
        print(f"✅ Success: {result.stdout.strip()}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e.stderr.strip()}")
        return None


def check_virtual_env():
    """Check if we're in a virtual environment."""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
        return True
    else:
        print("⚠️  WARNING: Not in a virtual environment!")
        response = input("Continue anyway? (y/N): ")
        return response.lower() == 'y'


def backup_current_requirements():
    """Create a backup of current requirements."""
    if os.path.exists('requirements.txt'):
        run_command('pip freeze > requirements-backup.txt', 
                   "Creating backup of current requirements")
        print("💾 Backup saved as requirements-backup.txt")


def update_pip():
    """Update pip to latest version."""
    run_command('python -m pip install --upgrade pip', 
               "Updating pip to latest version")


def install_requirements(requirements_file='requirements.txt', upgrade=False):
    """Install or upgrade requirements from file."""
    if not os.path.exists(requirements_file):
        print(f"❌ {requirements_file} not found!")
        return False
    
    upgrade_flag = '--upgrade' if upgrade else ''
    command = f'pip install {upgrade_flag} -r {requirements_file}'
    result = run_command(command, f"Installing from {requirements_file}")
    return result is not None


def check_security():
    """Check for security vulnerabilities."""
    print("\n🔒 Checking for security vulnerabilities...")
    run_command('pip install safety', "Installing safety checker")
    run_command('safety check', "Checking for known security vulnerabilities")


def generate_requirements():
    """Generate requirements.txt from current environment."""
    run_command('pip freeze > requirements-generated.txt', 
               "Generating requirements from current environment")


def main():
    """Main function to orchestrate requirements management."""
    print("🚀 Prbal Backend Requirements Management")
    print("=" * 50)
    
    if not check_virtual_env():
        sys.exit(1)
    
    # Menu options
    print("\nSelect an option:")
    print("1. Install production requirements")
    print("2. Install development requirements")
    print("3. Update all requirements")
    print("4. Check for security vulnerabilities")
    print("5. Generate requirements from current environment")
    print("6. Full setup (backup + update pip + install)")
    print("0. Exit")
    
    choice = input("\nEnter your choice (0-6): ").strip()
    
    if choice == '1':
        install_requirements('requirements.txt')
    
    elif choice == '2':
        install_requirements('requirements-dev.txt')
    
    elif choice == '3':
        backup_current_requirements()
        update_pip()
        install_requirements('requirements.txt', upgrade=True)
        if os.path.exists('requirements-dev.txt'):
            install_requirements('requirements-dev.txt', upgrade=True)
    
    elif choice == '4':
        check_security()
    
    elif choice == '5':
        generate_requirements()
    
    elif choice == '6':
        backup_current_requirements()
        update_pip()
        install_requirements('requirements.txt')
        if os.path.exists('requirements-dev.txt'):
            response = input("Install development requirements too? (y/N): ")
            if response.lower() == 'y':
                install_requirements('requirements-dev.txt')
        check_security()
    
    elif choice == '0':
        print("👋 Goodbye!")
        sys.exit(0)
    
    else:
        print("❌ Invalid choice!")
        sys.exit(1)
    
    print("\n✨ Requirements management completed!")


if __name__ == "__main__":
    main() 