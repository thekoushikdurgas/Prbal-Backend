from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.utils import timezone
import re

User = get_user_model()


def validate_pin(pin):
    """
    Validate that PIN is exactly 4 digits
    """
    if not pin:
        raise ValidationError(_('PIN is required'))
    
    pin_str = str(pin)
    if len(pin_str) != 4:
        raise ValidationError(_('PIN must be exactly 4 digits'))
    
    if not pin_str.isdigit():
        raise ValidationError(_('PIN must contain only numbers'))
    
    return True


def validate_phone_number(phone_number):
    """
    Validate phone number format
    """
    if not phone_number:
        raise ValidationError(_('Phone number is required'))
    
    # Remove any non-digit characters for validation
    phone_digits = re.sub(r'\D', '', phone_number)
    
    if len(phone_digits) < 10 or len(phone_digits) > 15:
        raise ValidationError(_('Phone number must be between 10 and 15 digits'))
    
    return True


def authenticate_user_with_pin(phone_number, pin):
    """
    Authenticate user using phone number and PIN
    Returns user object if authentication successful, None otherwise
    """
    try:
        validate_phone_number(phone_number)
        validate_pin(pin)
        
        # Find user by phone number
        user = User.objects.get(phone_number=phone_number, is_active=True)
        
        # Check if PIN is correct
        if user.check_pin(pin):
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            return user
        else:
            return None
            
    except (User.DoesNotExist, ValidationError):
        return None


def get_user_by_phone(phone_number):
    """
    Get user by phone number
    """
    try:
        return User.objects.get(phone_number=phone_number, is_active=True)
    except User.DoesNotExist:
        return None


def generate_random_pin():
    """
    Generate a random 4-digit PIN
    """
    import random
    return str(random.randint(1000, 9999))


def is_pin_strong(pin):
    """
    Check if PIN is strong (not sequential, not repeated digits)
    """
    pin_str = str(pin)
    
    # Check for repeated digits
    if len(set(pin_str)) == 1:
        return False, _('PIN cannot have all same digits')
    
    # Check for sequential digits (ascending)
    is_ascending = all(int(pin_str[i]) == int(pin_str[i-1]) + 1 for i in range(1, len(pin_str)))
    if is_ascending:
        return False, _('PIN cannot be sequential ascending digits')
    
    # Check for sequential digits (descending)
    is_descending = all(int(pin_str[i]) == int(pin_str[i-1]) - 1 for i in range(1, len(pin_str)))
    if is_descending:
        return False, _('PIN cannot be sequential descending digits')
    
    # Check for common weak PINs
    weak_pins = ['1234', '0000', '1111', '2222', '3333', '4444', '5555', '6666', '7777', '8888', '9999']
    if pin_str in weak_pins:
        return False, _('PIN is too common, please choose a different one')
    
    return True, _('PIN is strong')


def format_phone_number(phone_number):
    """
    Format phone number for consistent storage
    """
    if not phone_number:
        return phone_number
    
    # Remove all non-digit characters
    phone_digits = re.sub(r'\D', '', phone_number)
    
    # Add country code if missing (assuming default country)
    if len(phone_digits) == 10:
        phone_digits = '1' + phone_digits  # Assuming US (+1)
    
    return phone_digits 