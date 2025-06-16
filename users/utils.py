from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.utils import timezone
import re
import requests
import tempfile
import os
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from urllib.parse import urlparse
import uuid
import mimetypes
from PIL import Image
import io
import logging
from django.conf import settings

User = get_user_model()

# Set up logger for this module
logger = logging.getLogger(__name__)


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


class StandardizedResponseHelper:
    """
    Utility class for creating standardized JSON responses across all endpoints
    Expected format: {
        "message": "",
        "data": "",
        "time": "",
        "statusCode": ""
    }
    
    Enhanced with comprehensive debug logging and error tracking for better monitoring
    and debugging of API responses across the entire users app.
    """
    
    @staticmethod
    def success_response(message="Success", data=None, status_code=200):
        """
        Create a standardized success response
        
        Args:
            message (str): Success message
            data (any): Response data (can be dict, list, or any serializable type)
            status_code (int): HTTP status code
            
        Returns:
            dict: Standardized response dictionary
            
        Debug Information:
            - Logs response creation with detailed context
            - Tracks data types and structures
            - Monitors response performance
        """
        from django.utils import timezone
        import logging
        import time
        
        # Debug: Start performance tracking
        start_time = time.time()
        
        logger = logging.getLogger(__name__)
        logger.debug(f"🎉 Creating SUCCESS response: '{message}' | Status: {status_code}")
        
        # Debug: Analyze data structure for monitoring
        data_analysis = {
            'type': type(data).__name__,
            'is_empty': data is None or (hasattr(data, '__len__') and len(data) == 0),
            'size': len(data) if hasattr(data, '__len__') and data is not None else 'N/A'
        }
        
        response = {
            "message": message,
            "data": data,
            "time": timezone.now().isoformat(),
            "statusCode": status_code
        }
        
        # Debug: Performance and structure tracking
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        logger.debug(f"✅ Success response processed in {processing_time:.2f}ms | Data: {data_analysis['type']}({data_analysis['size']}) | Empty: {data_analysis['is_empty']}")
        
        # Debug: Log warning for potentially large responses
        if isinstance(data, (list, dict)) and hasattr(data, '__len__') and len(data) > 100:
            logger.warning(f"⚠️ Large response detected: {len(data)} items in response data")
        
        return response
    
    @staticmethod
    def error_response(message="An error occurred", errors=None, status_code=400, data=None):
        """
        Create a standardized error response
        
        Args:
            message (str): Error message
            errors (dict): Validation errors or detailed error information
            status_code (int): HTTP status code
            data (any): Additional data if needed
            
        Returns:
            dict: Standardized error response dictionary
            
        Debug Information:
            - Tracks error patterns and frequencies
            - Logs error context for debugging
            - Monitors error response performance
        """
        from django.utils import timezone
        import logging
        import time
        
        # Debug: Start performance tracking
        start_time = time.time()
        
        logger = logging.getLogger(__name__)
        
        # Debug: Categorize error types for monitoring
        error_category = "validation" if errors else "application"
        error_severity = "critical" if status_code >= 500 else "warning" if status_code >= 400 else "info"
        
        logger.debug(f"❌ Creating ERROR response: '{message}' | Status: {status_code} | Category: {error_category} | Severity: {error_severity}")
        
        response = {
            "message": message,
            "data": data,
            "time": timezone.now().isoformat(),
            "statusCode": status_code
        }
        
        # Add errors field if provided (for validation errors)
        if errors:
            response["errors"] = errors
            error_count = len(errors) if isinstance(errors, dict) else 1
            logger.debug(f"🔍 Added {error_count} validation error(s) to response: {list(errors.keys()) if isinstance(errors, dict) else 'single error'}")
        
        # Debug: Performance tracking
        processing_time = (time.time() - start_time) * 1000
        logger.debug(f"🚨 Error response processed in {processing_time:.2f}ms | Has errors: {bool(errors)} | Has data: {bool(data)}")
        
        # Debug: Log patterns for high-frequency errors
        if status_code == 400:
            logger.info(f"📊 Bad request error: {message[:50]}..." if len(message) > 50 else f"📊 Bad request error: {message}")
        elif status_code >= 500:
            logger.error(f"🚨 Server error: {message[:50]}..." if len(message) > 50 else f"🚨 Server error: {message}")
        
        return response
    
    @staticmethod
    def paginated_response(message="Data retrieved successfully", data=None, 
                          pagination_info=None, status_code=200, **kwargs):
        """
        Create a standardized paginated response
        
        Args:
            message (str): Success message
            data (list): List of data items
            pagination_info (dict): Pagination details (page, page_size, total_count, total_pages)
            status_code (int): HTTP status code
            **kwargs: Additional data fields to include
            
        Returns:
            dict: Standardized paginated response dictionary
            
        Debug Information:
            - Tracks pagination performance metrics
            - Monitors data load patterns
            - Analyzes pagination efficiency
        """
        from django.utils import timezone
        import logging
        import time
        
        # Debug: Start performance tracking
        start_time = time.time()
        
        logger = logging.getLogger(__name__)
        
        # Debug: Analyze pagination metrics
        results_count = len(data) if data else 0
        total_count = pagination_info.get('total_count', 0) if pagination_info else 0
        current_page = pagination_info.get('page', 1) if pagination_info else 1
        page_size = pagination_info.get('page_size', 10) if pagination_info else 10
        
        logger.debug(f"📄 Creating PAGINATED response: '{message}' | Status: {status_code} | Items: {results_count}/{total_count} | Page: {current_page}")
        
        response_data = {
            "results": data or [],
            "pagination": pagination_info or {}
        }
        
        # Add any additional fields from kwargs
        for key, value in kwargs.items():
            response_data[key] = value
            logger.debug(f"➕ Added additional paginated field: {key}={type(value).__name__}")
        
        response = {
            "message": message,
            "data": response_data,
            "time": timezone.now().isoformat(),
            "statusCode": status_code
        }
        
        # Debug: Performance and efficiency tracking
        processing_time = (time.time() - start_time) * 1000
        efficiency_ratio = (results_count / page_size * 100) if page_size > 0 else 0
        
        logger.debug(f"📊 Paginated response processed in {processing_time:.2f}ms | Efficiency: {efficiency_ratio:.1f}% | Additional fields: {len(kwargs)}")
        
        # Debug: Log pagination warnings
        if results_count == 0 and total_count > 0:
            logger.warning(f"⚠️ Empty page returned: Page {current_page} of {pagination_info.get('total_pages', 0)} has no results")
        
        if page_size > 50:
            logger.warning(f"⚠️ Large page size detected: {page_size} items per page may impact performance")
        
        return response
    
    @staticmethod
    def validation_error_response(serializer_errors, message="Validation failed", status_code=400):
        """
        Create a standardized validation error response from serializer errors
        
        Args:
            serializer_errors (dict): Django REST Framework serializer errors
            message (str): Error message
            status_code (int): HTTP status code
            
        Returns:
            dict: Standardized validation error response dictionary
            
        Debug Information:
            - Tracks validation error patterns
            - Analyzes field-specific error frequencies  
            - Monitors validation performance
        """
        from django.utils import timezone
        import logging
        import time
        
        # Debug: Start performance tracking
        start_time = time.time()
        
        logger = logging.getLogger(__name__)
        
        # Debug: Analyze validation error patterns
        error_fields = list(serializer_errors.keys()) if serializer_errors else []
        error_count = len(error_fields)
        
        logger.debug(f"❌ Creating VALIDATION ERROR response: '{message}' | Status: {status_code} | Fields: {error_count} | Affected: {error_fields}")
        
        # Process serializer errors to be more user-friendly
        processed_errors = {}
        error_details = {}
        
        if serializer_errors:
            for field, error_list in serializer_errors.items():
                if isinstance(error_list, list):
                    processed_errors[field] = error_list[0] if error_list else "Invalid value"
                    error_details[field] = {
                        'error_count': len(error_list),
                        'all_errors': error_list
                    }
                else:
                    processed_errors[field] = str(error_list)
                    error_details[field] = {
                        'error_count': 1,
                        'all_errors': [str(error_list)]
                    }
        
        response = {
            "message": message,
            "data": None,
            "time": timezone.now().isoformat(),
            "statusCode": status_code,
            "errors": processed_errors
        }
        
        # Debug: Performance and error analysis
        processing_time = (time.time() - start_time) * 1000
        total_error_messages = sum(details['error_count'] for details in error_details.values())
        
        logger.debug(f"🔍 Validation error response processed in {processing_time:.2f}ms | Total errors: {total_error_messages} | Processed fields: {len(processed_errors)}")
        
        # Debug: Log common validation patterns
        common_validation_fields = ['email', 'password', 'phone_number', 'username', 'pin']
        problematic_fields = [field for field in error_fields if field in common_validation_fields]
        
        if problematic_fields:
            logger.info(f"📊 Common validation errors detected in fields: {problematic_fields}")
        
        # Debug: Log if many errors are present (potential form issues)
        if error_count > 5:
            logger.warning(f"⚠️ High error count detected: {error_count} validation errors may indicate form or UI issues")
        
        return response


def download_file_from_url(url, max_size=10*1024*1024):  # 10MB limit
    """
    Download a file from URL and return a Django File object
    
    Args:
        url (str): URL to download from
        max_size (int): Maximum file size in bytes
        
    Returns:
        ContentFile: Django file object or None if failed
    """
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            logger.warning(f"Invalid URL provided: {url}")
            return None
        
        # Download with size and timeout limits
        headers = {
            'User-Agent': 'Prbal-App/1.0 (Document Converter)',
            'Accept': 'image/*,application/pdf,*/*'
        }
        
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        if not any(ct in content_type for ct in ['image/', 'application/pdf', 'application/msword', 'application/vnd.']):
            logger.warning(f"Unsupported content type: {content_type} for URL: {url}")
            return None
        
        # Download with size limit
        content = b''
        for chunk in response.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > max_size:
                logger.warning(f"File too large from URL: {url}")
                return None
        
        # Generate filename
        filename = generate_filename_from_url(url, content_type)
        
        # Create Django file object
        file_obj = ContentFile(content, name=filename)
        
        logger.info(f"Successfully downloaded file from URL: {url} -> {filename}")
        return file_obj
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading file from URL {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading file from URL {url}: {e}")
        return None


def generate_filename_from_url(url, content_type=None):
    """
    Generate a secure filename from URL and content type
    
    Args:
        url (str): Original URL
        content_type (str): MIME type of the content
        
    Returns:
        str: Generated filename
    """
    # Get file extension from URL or content type
    parsed_url = urlparse(url)
    original_name = os.path.basename(parsed_url.path)
    
    if original_name and '.' in original_name:
        # Use original extension if available
        ext = original_name.split('.')[-1].lower()
    elif content_type:
        # Guess extension from content type
        ext = mimetypes.guess_extension(content_type)
        if ext:
            ext = ext.lstrip('.')
        else:
            ext = 'bin'
    else:
        ext = 'bin'
    
    # Generate unique filename
    return f"{uuid.uuid4()}.{ext}"


def process_base64_file(base64_string, filename_hint=None):
    """
    Process base64 encoded file data
    
    Args:
        base64_string (str): Base64 encoded file data
        filename_hint (str): Optional filename hint
        
    Returns:
        ContentFile: Django file object or None if failed
    """
    try:
        import base64
        
        # Handle data URL format: data:mime/type;base64,data
        if base64_string.startswith('data:'):
            header, data = base64_string.split(',', 1)
            content_type = header.split(';')[0].split(':')[1]
        else:
            data = base64_string
            content_type = None
        
        # Decode base64 data
        file_data = base64.b64decode(data)
        
        # Generate filename
        if filename_hint:
            filename = filename_hint
        elif content_type:
            ext = mimetypes.guess_extension(content_type)
            filename = f"{uuid.uuid4()}{ext}" if ext else f"{uuid.uuid4()}.bin"
        else:
            filename = f"{uuid.uuid4()}.bin"
        
        # Create Django file object
        file_obj = ContentFile(file_data, name=filename)
        
        logger.info(f"Successfully processed base64 file: {filename}")
        return file_obj
        
    except Exception as e:
        logger.error(f"Error processing base64 file: {e}")
        return None


def convert_url_to_file(url_or_data, field_name="document"):
    """
    Convert URL or base64 data to a file suitable for Django FileField
    
    Args:
        url_or_data (str): URL or base64 data
        field_name (str): Name of the field for logging
        
    Returns:
        ContentFile: Django file object or None if failed
    """
    if not url_or_data:
        return None
    
    logger.debug(f"Converting {field_name}: {url_or_data[:100]}...")
    
    # Check if it's base64 data
    if url_or_data.startswith('data:') or (len(url_or_data) > 100 and not url_or_data.startswith('http')):
        return process_base64_file(url_or_data, f"{field_name}_{uuid.uuid4().hex[:8]}")
    
    # Check if it's a URL
    elif url_or_data.startswith(('http://', 'https://')):
        return download_file_from_url(url_or_data)
    
    else:
        logger.warning(f"Unrecognized format for {field_name}: {url_or_data[:50]}...")
        return None


def optimize_image(file_obj, max_width=1920, max_height=1080, quality=85):
    """
    Optimize uploaded image for storage
    
    Args:
        file_obj: Django file object
        max_width (int): Maximum width in pixels
        max_height (int): Maximum height in pixels
        quality (int): JPEG quality (1-100)
        
    Returns:
        ContentFile: Optimized image file or original if not an image
    """
    try:
        # Check if it's an image
        if not file_obj.content_type or not file_obj.content_type.startswith('image/'):
            return file_obj
        
        # Open image
        image = Image.open(file_obj)
        
        # Convert to RGB if necessary
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGB')
        
        # Resize if necessary
        if image.width > max_width or image.height > max_height:
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            logger.debug(f"Resized image from original size to {image.width}x{image.height}")
        
        # Save optimized image
        output = io.BytesIO()
        format_map = {
            'image/jpeg': 'JPEG',
            'image/jpg': 'JPEG',
            'image/png': 'PNG',
            'image/gif': 'GIF',
            'image/webp': 'WEBP'
        }
        
        image_format = format_map.get(file_obj.content_type, 'JPEG')
        
        if image_format == 'JPEG':
            image.save(output, format=image_format, quality=quality, optimize=True)
        else:
            image.save(output, format=image_format, optimize=True)
        
        # Create new file object
        optimized_file = ContentFile(output.getvalue(), name=file_obj.name)
        logger.debug(f"Optimized image: {file_obj.name}")
        
        return optimized_file
        
    except Exception as e:
        logger.warning(f"Error optimizing image {file_obj.name}: {e}")
        return file_obj


def secure_upload_path(instance, filename, subfolder):
    """
    Generate secure upload path for any file type
    
    Args:
        instance: Model instance
        filename (str): Original filename
        subfolder (str): Subfolder name (e.g., 'documents', 'images', 'profiles')
        
    Returns:
        str: Secure upload path
    """
    # Get file extension
    ext = filename.split('.')[-1].lower() if '.' in filename else 'bin'
    
    # Generate unique filename
    secure_filename = f"{uuid.uuid4()}.{ext}"
    
    # Create path based on user and type
    if hasattr(instance, 'user'):
        user_id = instance.user.id
    elif hasattr(instance, 'id'):
        user_id = instance.id
    else:
        user_id = 'unknown'
    
    return f"{subfolder}/{user_id}/{secure_filename}"


# Enhanced document path functions
def profile_picture_path(instance, filename):
    """Generate secure path for profile pictures with user-specific organization"""
    return secure_upload_path(instance, filename, f'profile_pictures/{instance.id}')


def verification_document_enhanced_path(instance, filename):
    """Enhanced path for verification documents with better organization"""
    return secure_upload_path(instance, filename, f'verification_documents/{instance.user.id}/{instance.verification_type}')


class DocumentImageProcessor:
    """
    Comprehensive document and image processing class for all endpoints.
    Handles conversion from URLs, base64, local files, and cloud storage to Django File objects.
    """
    
    SUPPORTED_IMAGE_TYPES = [
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'
    ]
    
    SUPPORTED_DOCUMENT_TYPES = [
        'application/pdf', 'application/msword', 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/plain', 'text/csv'
    ]
    
    ALL_SUPPORTED_TYPES = SUPPORTED_IMAGE_TYPES + SUPPORTED_DOCUMENT_TYPES
    
    @classmethod
    def process_document_field(cls, data, field_name="document", max_size=10*1024*1024, 
                              optimize_images=True, allowed_types=None):
        """
        Universal document/image processor for any endpoint field
        
        Args:
            data: Input data (URL, base64, file object, or file path)
            field_name: Name of the field for logging and naming
            max_size: Maximum file size in bytes
            optimize_images: Whether to optimize image files
            allowed_types: List of allowed MIME types, defaults to all supported types
            
        Returns:
            ContentFile: Django file object or None if processing failed
        """
        if not data:
            return None
            
        if allowed_types is None:
            allowed_types = cls.ALL_SUPPORTED_TYPES
            
        logger.debug(f"Processing {field_name}: {str(data)[:100]}...")
        
        try:
            # If it's already a Django file object, validate and return
            if hasattr(data, 'read') and hasattr(data, 'name'):
                logger.debug(f"{field_name} is already a file object: {data.name}")
                return cls._validate_and_process_file(data, field_name, max_size, 
                                                    optimize_images, allowed_types)
            
            # Check if it's base64 data
            if isinstance(data, str) and (data.startswith('data:') or cls._is_base64(data)):
                logger.debug(f"Processing {field_name} as base64 data")
                return cls._process_base64_data(data, field_name, max_size, 
                                              optimize_images, allowed_types)
            
            # Check if it's a URL
            elif isinstance(data, str) and data.startswith(('http://', 'https://')):
                logger.debug(f"Processing {field_name} as URL: {data}")
                return cls._process_url_data(data, field_name, max_size, 
                                           optimize_images, allowed_types)
            
            # Check if it's a local file path
            elif isinstance(data, str) and os.path.exists(data):
                logger.debug(f"Processing {field_name} as local file path: {data}")
                return cls._process_local_file(data, field_name, max_size, 
                                             optimize_images, allowed_types)
            
            # Check if it's cloud storage reference (implementation specific)
            elif isinstance(data, str) and cls._is_cloud_storage_reference(data):
                logger.debug(f"Processing {field_name} as cloud storage reference")
                return cls._process_cloud_storage_reference(data, field_name, max_size, 
                                                          optimize_images, allowed_types)
            
            else:
                logger.warning(f"Unrecognized format for {field_name}: {str(data)[:50]}...")
                return None
                
        except Exception as e:
            logger.error(f"Error processing {field_name}: {e}", exc_info=True)
            return None
    
    @classmethod
    def _is_base64(cls, data):
        """Check if string is base64 encoded"""
        try:
            import base64
            # Remove data URL prefix if present
            if data.startswith('data:'):
                return True
            # Try to decode as base64
            base64.b64decode(data, validate=True)
            return len(data) > 100  # Reasonable minimum for file data
        except Exception:
            return False
    
    @classmethod
    def _is_cloud_storage_reference(cls, data):
        """Check if string is a cloud storage reference"""
        cloud_patterns = [
            's3://',  # AWS S3
            'gs://',  # Google Cloud Storage
            'azure://',  # Azure Blob Storage
            'wasb://',  # Azure Blob Storage (alternative)
            'abfs://',  # Azure Data Lake Storage
            'gcs://',  # Google Cloud Storage (alternative)
        ]
        return any(data.startswith(pattern) for pattern in cloud_patterns)
    
    @classmethod
    def _validate_and_process_file(cls, file_obj, field_name, max_size, 
                                  optimize_images, allowed_types):
        """Validate and process an existing file object"""
        # Check file size
        if hasattr(file_obj, 'size') and file_obj.size > max_size:
            logger.warning(f"{field_name} exceeds size limit: {file_obj.size} bytes")
            return None
        
        # Check content type if available
        content_type = getattr(file_obj, 'content_type', None)
        if content_type and content_type not in allowed_types:
            logger.warning(f"{field_name} has unsupported content type: {content_type}")
            return None
        
        # Optimize if it's an image
        if optimize_images and content_type and content_type.startswith('image/'):
            return optimize_image(file_obj)
        
        return file_obj
    
    @classmethod
    def _process_base64_data(cls, data, field_name, max_size, optimize_images, allowed_types):
        """Process base64 encoded data"""
        try:
            import base64
            
            # Handle data URL format
            if data.startswith('data:'):
                header, data_part = data.split(',', 1)
                content_type = header.split(';')[0].split(':')[1]
            else:
                data_part = data
                content_type = None
            
            # Validate content type
            if content_type and content_type not in allowed_types:
                logger.warning(f"{field_name} has unsupported content type: {content_type}")
                return None
            
            # Decode data
            file_data = base64.b64decode(data_part)
            
            # Check size
            if len(file_data) > max_size:
                logger.warning(f"{field_name} base64 data exceeds size limit")
                return None
            
            # Generate filename
            ext = cls._get_extension_from_content_type(content_type) if content_type else 'bin'
            filename = f"{field_name}_{uuid.uuid4().hex[:8]}.{ext}"
            
            # Create file object
            file_obj = ContentFile(file_data, name=filename)
            file_obj.content_type = content_type
            
            # Optimize if image
            if optimize_images and content_type and content_type.startswith('image/'):
                return optimize_image(file_obj)
            
            return file_obj
            
        except Exception as e:
            logger.error(f"Error processing base64 data for {field_name}: {e}")
            return None
    
    @classmethod
    def _process_url_data(cls, url, field_name, max_size, optimize_images, allowed_types):
        """Process URL data by downloading"""
        try:
            # Use existing download function
            file_obj = download_file_from_url(url, max_size)
            if not file_obj:
                return None
            
            # Validate content type
            content_type = getattr(file_obj, 'content_type', None)
            if content_type and content_type not in allowed_types:
                logger.warning(f"{field_name} downloaded file has unsupported content type: {content_type}")
                return None
            
            # Optimize if image
            if optimize_images and content_type and content_type.startswith('image/'):
                return optimize_image(file_obj)
            
            return file_obj
            
        except Exception as e:
            logger.error(f"Error processing URL for {field_name}: {e}")
            return None
    
    @classmethod
    def _process_local_file(cls, file_path, field_name, max_size, optimize_images, allowed_types):
        """Process local file path"""
        try:
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > max_size:
                logger.warning(f"{field_name} local file exceeds size limit: {file_size} bytes")
                return None
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type and content_type not in allowed_types:
                logger.warning(f"{field_name} local file has unsupported content type: {content_type}")
                return None
            
            # Read file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Generate secure filename
            original_name = os.path.basename(file_path)
            ext = original_name.split('.')[-1] if '.' in original_name else 'bin'
            filename = f"{field_name}_{uuid.uuid4().hex[:8]}.{ext}"
            
            # Create file object
            file_obj = ContentFile(file_data, name=filename)
            file_obj.content_type = content_type
            
            # Optimize if image
            if optimize_images and content_type and content_type.startswith('image/'):
                return optimize_image(file_obj)
            
            return file_obj
            
        except Exception as e:
            logger.error(f"Error processing local file for {field_name}: {e}")
            return None
    
    @classmethod
    def _process_cloud_storage_reference(cls, reference, field_name, max_size, 
                                        optimize_images, allowed_types):
        """Process cloud storage reference"""
        # This is a placeholder for cloud storage integration
        # Implementation would depend on the specific cloud provider
        logger.info(f"Cloud storage processing not yet implemented for {field_name}: {reference}")
        return None
    
    @classmethod
    def _get_extension_from_content_type(cls, content_type):
        """Get file extension from content type"""
        ext_map = {
            'image/jpeg': 'jpg',
            'image/png': 'png',
            'image/gif': 'gif',
            'image/webp': 'webp',
            'image/bmp': 'bmp',
            'application/pdf': 'pdf',
            'application/msword': 'doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'application/vnd.ms-excel': 'xls',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
            'text/plain': 'txt',
            'text/csv': 'csv'
        }
        return ext_map.get(content_type, 'bin')
    
    @classmethod
    def process_verification_documents(cls, primary_document=None, back_document=None, 
                                     field_prefix="verification_doc"):
        """
        Specialized method for processing verification documents
        
        Args:
            primary_document: Primary verification document (any format)
            back_document: Back side of document (any format)
            field_prefix: Prefix for field naming
            
        Returns:
            tuple: (primary_file, back_file) as Django file objects
        """
        primary_file = None
        back_file = None
        
        if primary_document:
            primary_file = cls.process_document_field(
                primary_document,
                f"{field_prefix}_primary",
                max_size=15*1024*1024,  # 15MB for documents
                optimize_images=True,
                allowed_types=cls.ALL_SUPPORTED_TYPES
            )
        
        if back_document:
            back_file = cls.process_document_field(
                back_document,
                f"{field_prefix}_back",
                max_size=15*1024*1024,  # 15MB for documents
                optimize_images=True,
                allowed_types=cls.ALL_SUPPORTED_TYPES
            )
        
        return primary_file, back_file
    
    @classmethod
    def process_profile_images(cls, profile_image=None):
        """
        Specialized method for processing profile images
        
        Args:
            profile_image: Profile image (any format)
            
        Returns:
            ContentFile: Django file object or None
        """
        if not profile_image:
            return None
            
        return cls.process_document_field(
            profile_image,
            "profile_image",
            max_size=5*1024*1024,  # 5MB for profile images
            optimize_images=True,
            allowed_types=cls.SUPPORTED_IMAGE_TYPES
        )


class UniversalFileConverter:
    """
    Universal file converter that can be used across all endpoints.
    Provides a simple interface for converting any file input to Django file objects.
    """
    
    @staticmethod
    def convert_any_to_file(data, field_name="file", file_type="auto", **kwargs):
        """
        Convert any input to a Django file object
        
        Args:
            data: Input data (any format)
            field_name: Name for the field/file
            file_type: Type hint ("image", "document", "auto")
            **kwargs: Additional parameters for processing
            
        Returns:
            ContentFile: Django file object or None
        """
        if file_type == "image":
            allowed_types = DocumentImageProcessor.SUPPORTED_IMAGE_TYPES
            max_size = kwargs.get('max_size', 5*1024*1024)  # 5MB default for images
        elif file_type == "document":
            allowed_types = DocumentImageProcessor.SUPPORTED_DOCUMENT_TYPES
            max_size = kwargs.get('max_size', 15*1024*1024)  # 15MB default for documents
        else:  # auto
            allowed_types = DocumentImageProcessor.ALL_SUPPORTED_TYPES
            max_size = kwargs.get('max_size', 10*1024*1024)  # 10MB default
        
        return DocumentImageProcessor.process_document_field(
            data=data,
            field_name=field_name,
            max_size=max_size,
            optimize_images=kwargs.get('optimize_images', True),
            allowed_types=allowed_types
        )
    
    @staticmethod
    def convert_multiple_files(file_list, field_prefix="file", file_type="auto", **kwargs):
        """
        Convert multiple files at once
        
        Args:
            file_list: List of file data
            field_prefix: Prefix for field naming
            file_type: Type hint ("image", "document", "auto")
            **kwargs: Additional parameters
            
        Returns:
            list: List of Django file objects
        """
        converted_files = []
        
        for i, file_data in enumerate(file_list):
            field_name = f"{field_prefix}_{i+1}"
            converted_file = UniversalFileConverter.convert_any_to_file(
                file_data, field_name, file_type, **kwargs
            )
            if converted_file:
                converted_files.append(converted_file)
        
        return converted_files


# Update the existing FileConversionHelper to use the new processors
class FileConversionHelper:
    """
    Enhanced helper class for handling file conversions in serializers and views.
    Now uses the new DocumentImageProcessor for better functionality.
    """
    
    @staticmethod
    def process_file_field(data, field_name, optimize_images=True, file_type="auto", **kwargs):
        """
        Process a file field that might contain URL, base64 data, or file object
        Now uses the enhanced DocumentImageProcessor
        """
        return UniversalFileConverter.convert_any_to_file(
            data=data,
            field_name=field_name,
            file_type=file_type,
            optimize_images=optimize_images,
            **kwargs
        )
    
    @staticmethod
    def process_multiple_files(file_data_list, field_prefix="file", file_type="auto", **kwargs):
        """
        Process multiple files using the enhanced converter
        """
        return UniversalFileConverter.convert_multiple_files(
            file_list=file_data_list,
            field_prefix=field_prefix,
            file_type=file_type,
            **kwargs
        )
    
    @staticmethod
    def process_verification_documents(primary_doc=None, back_doc=None):
        """Convenience method for verification documents"""
        return DocumentImageProcessor.process_verification_documents(primary_doc, back_doc)
    
    @staticmethod
    def process_profile_image(image_data):
        """Convenience method for profile images"""
        return DocumentImageProcessor.process_profile_images(image_data)


def get_media_url(file_field, request=None):
    """
    Helper function to get the proper media URL for a file field.
    Handles both development and production URLs consistently.
    """
    if not file_field:
        return None
    
    if hasattr(file_field, 'url'):
        url = file_field.url
        
        # Handle different URL formats
        if url.startswith('/media/'):
            return url
        elif url.startswith('media/'):
            return f'/{url}'
        elif not url.startswith(('http://', 'https://')):
            return f'/media/{url}'
        else:
            return url
    
    return None


def clean_media_url(url):
    """
    Clean and normalize media URLs to prevent duplicate /media/ prefixes
    """
    if not url:
        return None
    
    # Remove any duplicate /media/ prefixes
    if url.count('/media/') > 1:
        # Find the last occurrence of /media/ and use that
        last_media_index = url.rfind('/media/')
        url = url[last_media_index:]
    
    # Ensure proper format
    if not url.startswith('/media/') and not url.startswith(('http://', 'https://')):
        if url.startswith('media/'):
            url = f'/{url}'
        else:
            url = f'/media/{url}'
    
    return url


def get_absolute_media_url(relative_url, request=None):
    """
    Convert a relative media URL to an absolute URL with domain
    
    Args:
        relative_url (str): Relative URL path (e.g., '/media/path/file.jpg')
        request: HTTP request object for building absolute URI
        
    Returns:
        str: Absolute URL with domain or relative URL if no request/domain available
    """
    if not relative_url:
        return None
        
    # Clean the URL first
    cleaned_url = clean_media_url(relative_url)
    
    # If request is provided, use it to build absolute URI
    if request:
        return request.build_absolute_uri(cleaned_url)
    
    # Fallback: try to get domain from Django settings
    try:
        from django.contrib.sites.models import Site
        current_site = Site.objects.get_current()
        protocol = 'https' if getattr(settings, 'SECURE_SSL_REDIRECT', False) else 'http'
        return f"{protocol}://{current_site.domain}{cleaned_url}"
    except:
        # If Sites framework is not available, try getting from settings
        try:
            from django.conf import settings
            allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
            if allowed_hosts and allowed_hosts[0] != '*':
                host = allowed_hosts[0]
                protocol = 'https' if getattr(settings, 'SECURE_SSL_REDIRECT', False) else 'http'
                return f"{protocol}://{host}{cleaned_url}"
        except:
            pass
    
    # Final fallback: return relative URL
    return cleaned_url 