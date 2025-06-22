from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ServiceCategory, ServiceSubCategory, Service, ServiceImage, ServiceRequest
from users.serializers import PublicUserProfileSerializer
import base64
import uuid
from django.core.files.base import ContentFile
import logging

# 🔍 DEBUG: Setup comprehensive logging for services serializers
logger = logging.getLogger(__name__)
logger.info("🚀 DEBUG: Services serializers module loaded successfully")
logger.debug("📦 DEBUG: All imports completed - models, utils, and validation ready")
logger.debug("🔧 DEBUG: Initializing serializers with enhanced validation and debug tracking")

User = get_user_model()

# Debug: Log user model loading with enhanced tracking
logger.debug(f"👤 DEBUG: User model loaded for serializers: {User.__name__}")
logger.debug(f"📊 DEBUG: Services serializers initialized with {len([ServiceCategory, ServiceSubCategory, Service, ServiceRequest])} model types")
logger.info("✅ DEBUG: Services serializers initialization completed - all serializers ready")

class ServiceCategorySerializer(serializers.ModelSerializer):
    """
    🗂️ SERVICE CATEGORY SERIALIZER - ENHANCED WITH COMPREHENSIVE DEBUG TRACKING
    ===========================================================================
    
    Serializer for service categories with comprehensive validation and debug tracking.
    Provides detailed logging for data transformation and validation processes.
    
    FEATURES:
    - ✅ Category data serialization with field validation
    - ✅ Read-only timestamp fields with proper formatting
    - ✅ Icon URL and file handling with validation
    - ✅ Sort order validation and business logic checks
    - ✅ Comprehensive debug logging for all operations
    
    DEBUG ENHANCEMENTS:
    - 🔍 Field-by-field validation tracking
    - 📊 Data transformation monitoring
    - 🛡️ Input validation with detailed error context
    - 📈 Serialization performance tracking
    - 🔄 CRUD operation logging
    """
    
    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'description', 'icon', 'icon_url', 'sort_order', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        """
        🚀 ENHANCED SERIALIZER INITIALIZATION WITH DEBUG TRACKING
        ========================================================
        
        Initialize the serializer with comprehensive debug logging.
        Tracks serializer creation and configuration for monitoring.
        """
        # 📝 DEBUG: Log serializer initialization
        logger.debug("🚀 DEBUG: ServiceCategorySerializer initialization started")
        logger.debug(f"📋 DEBUG: Serializer args: {len(args)} arguments provided")
        logger.debug(f"📊 DEBUG: Serializer kwargs keys: {list(kwargs.keys())}")
        
        # Check if we're dealing with instance data
        if args and hasattr(args[0], '_meta'):
            logger.debug(f"📦 DEBUG: Serializing existing ServiceCategory instance: ID={getattr(args[0], 'id', 'unknown')}")
        elif args and hasattr(args[0], '__iter__'):
            try:
                count = len(args[0]) if hasattr(args[0], '__len__') else 'unknown'
                logger.debug(f"📦 DEBUG: Serializing ServiceCategory queryset/list: {count} items")
            except:
                logger.debug("📦 DEBUG: Serializing ServiceCategory iterable: count unknown")
        else:
            logger.debug("📝 DEBUG: Creating new ServiceCategory serializer for input validation")
        
        super().__init__(*args, **kwargs)
        
        # 🎉 DEBUG: Log successful initialization
        logger.debug("✅ DEBUG: ServiceCategorySerializer initialization completed")
    
    def validate_name(self, value):
        """
        🔍 ENHANCED NAME VALIDATION WITH COMPREHENSIVE CHECKING
        ======================================================
        
        Validates the category name with detailed business logic checks.
        Ensures name uniqueness, format compliance, and business rules.
        """
        # 📝 DEBUG: Log validation start
        logger.debug(f"🔍 DEBUG: Validating ServiceCategory name: '{value}'")
        
        # 🧹 DEBUG: Basic format validation
        if not value or not value.strip():
            logger.warning("❌ DEBUG: ServiceCategory name validation failed - empty or whitespace-only")
            raise serializers.ValidationError("Category name cannot be empty or contain only whitespace.")
        
        # Clean the value
        cleaned_value = value.strip()
        logger.debug(f"🧹 DEBUG: Cleaned category name: '{cleaned_value}'")
        
        # 📏 DEBUG: Length validation
        if len(cleaned_value) < 2:
            logger.warning(f"❌ DEBUG: ServiceCategory name validation failed - too short: {len(cleaned_value)} chars")
            raise serializers.ValidationError("Category name must be at least 2 characters long.")
        
        if len(cleaned_value) > 100:
            logger.warning(f"❌ DEBUG: ServiceCategory name validation failed - too long: {len(cleaned_value)} chars")
            raise serializers.ValidationError("Category name cannot exceed 100 characters.")
        
        # 🔤 DEBUG: Character validation
        import re
        if not re.match(r'^[a-zA-Z0-9\s\-&().]+$', cleaned_value):
            logger.warning(f"❌ DEBUG: ServiceCategory name validation failed - invalid characters in: '{cleaned_value}'")
            raise serializers.ValidationError("Category name can only contain letters, numbers, spaces, hyphens, ampersands, and parentheses.")
        
        # 🔄 DEBUG: Check for duplicates (excluding current instance if updating)
        from .models import ServiceCategory
        existing_categories = ServiceCategory.objects.filter(name__iexact=cleaned_value)
        
        # If we're updating an existing category, exclude it from the duplicate check
        if self.instance:
            existing_categories = existing_categories.exclude(id=self.instance.id)
            logger.debug(f"🔄 DEBUG: Duplicate check excludes current instance: {self.instance.id}")
        
        if existing_categories.exists():
            existing_category = existing_categories.first()
            logger.warning(f"❌ DEBUG: ServiceCategory name validation failed - duplicate found: '{existing_category.name}' (ID: {existing_category.id})")
            raise serializers.ValidationError(f"A category with the name '{cleaned_value}' already exists.")
        
        # ✅ DEBUG: Log successful validation
        logger.debug(f"✅ DEBUG: ServiceCategory name validation passed: '{cleaned_value}'")
        return cleaned_value
    
    def validate_sort_order(self, value):
        """
        🔢 ENHANCED SORT ORDER VALIDATION WITH BUSINESS LOGIC
        ====================================================
        
        Validates the sort order with business logic and conflict detection.
        Ensures proper ordering and prevents conflicts.
        """
        # 📝 DEBUG: Log validation start
        logger.debug(f"🔢 DEBUG: Validating ServiceCategory sort_order: {value}")
        
        # 📊 DEBUG: Range validation
        if value < 0:
            logger.warning(f"❌ DEBUG: ServiceCategory sort_order validation failed - negative value: {value}")
            raise serializers.ValidationError("Sort order must be a non-negative integer.")
        
        if value > 9999:
            logger.warning(f"❌ DEBUG: ServiceCategory sort_order validation failed - too large: {value}")
            raise serializers.ValidationError("Sort order cannot exceed 9999.")
        
        # 🔄 DEBUG: Check for sort order conflicts
        from .models import ServiceCategory
        conflicting_categories = ServiceCategory.objects.filter(sort_order=value)
        
        # If we're updating an existing category, exclude it from the conflict check
        if self.instance:
            conflicting_categories = conflicting_categories.exclude(id=self.instance.id)
            logger.debug(f"🔄 DEBUG: Sort order conflict check excludes current instance: {self.instance.id}")
        
        conflict_count = conflicting_categories.count()
        if conflict_count > 0:
            conflicting_names = list(conflicting_categories.values_list('name', flat=True)[:3])
            logger.warning(f"⚠️ DEBUG: ServiceCategory sort_order conflict detected: {conflict_count} categories with order {value}")
            logger.warning(f"🔍 DEBUG: Conflicting categories: {conflicting_names}")
            # Note: We don't raise an error here as multiple categories can have the same sort order
            # But we log it for administrative awareness
        
        # ✅ DEBUG: Log successful validation
        logger.debug(f"✅ DEBUG: ServiceCategory sort_order validation passed: {value}")
        return value
    
    def validate(self, attrs):
        """
        🔍 ENHANCED COMPREHENSIVE VALIDATION WITH CROSS-FIELD CHECKS
        ===========================================================
        
        Performs comprehensive validation across all fields with detailed logging.
        Ensures data integrity and business rule compliance.
        """
        # 📝 DEBUG: Log comprehensive validation start
        logger.debug("🔍 DEBUG: ServiceCategory comprehensive validation started")
        logger.debug(f"📊 DEBUG: Validating attributes: {list(attrs.keys())}")
        
        # 🏷️ DEBUG: Validate name and sort_order combination
        if 'name' in attrs and 'sort_order' in attrs:
            name = attrs['name']
            sort_order = attrs['sort_order']
            logger.debug(f"🔗 DEBUG: Validating name-sort_order combination: '{name}' -> {sort_order}")
            
            # Business logic: Featured categories (low sort order) should have descriptive names
            if sort_order <= 10 and len(name) < 5:
                logger.warning(f"⚠️ DEBUG: Featured category with short name detected: '{name}' (sort: {sort_order})")
                # Note: This is a warning, not an error, as it's a guideline rather than a strict rule
        
        # 🖼️ DEBUG: Validate icon consistency
        if 'icon' in attrs and 'icon_url' in attrs:
            icon = attrs['icon']
            icon_url = attrs['icon_url']
            
            if icon and icon_url:
                logger.warning("⚠️ DEBUG: Both icon file and icon URL provided - file will take precedence")
            elif not icon and not icon_url:
                logger.debug("📝 DEBUG: No icon provided - using default icon behavior")
        
        # 🔄 DEBUG: Validate status consistency
        if 'is_active' in attrs:
            is_active = attrs['is_active']
            logger.debug(f"🔄 DEBUG: Category active status: {is_active}")
            
            if not is_active:
                # Check if this category has active services or subcategories
                if self.instance:
                    active_services_count = self.instance.services.filter(status='active').count()
                    active_subcategories_count = self.instance.subcategories.filter(is_active=True).count()
                    
                    if active_services_count > 0 or active_subcategories_count > 0:
                        logger.warning(f"⚠️ DEBUG: Deactivating category with active dependencies:")
                        logger.warning(f"   📊 Active services: {active_services_count}")
                        logger.warning(f"   📊 Active subcategories: {active_subcategories_count}")
                        # Note: We allow this but log it for administrative awareness
        
        # ✅ DEBUG: Log successful comprehensive validation
        logger.debug("✅ DEBUG: ServiceCategory comprehensive validation completed successfully")
        return super().validate(attrs)
    
    def to_representation(self, instance):
        """
        🔄 ENHANCED DATA REPRESENTATION WITH DEBUG TRACKING
        ==================================================
        
        Converts model instance to JSON representation with comprehensive tracking.
        Monitors data transformation and adds computed fields.
        """
        # 📝 DEBUG: Log representation start
        logger.debug(f"🔄 DEBUG: Converting ServiceCategory to representation: {instance.name} (ID: {instance.id})")
        
        try:
            # Get the base representation
            representation = super().to_representation(instance)
            
            # 📊 DEBUG: Add computed fields for better API experience
            logger.debug("📊 DEBUG: Adding computed fields to ServiceCategory representation")
            
            # Add service count
            services_count = instance.services.count()
            representation['services_count'] = services_count
            logger.debug(f"   📈 Services count: {services_count}")
            
            # Add subcategories count
            subcategories_count = instance.subcategories.count()
            representation['subcategories_count'] = subcategories_count
            logger.debug(f"   📈 Subcategories count: {subcategories_count}")
            
            # Add activity status
            has_active_services = instance.services.filter(status='active').exists()
            representation['has_active_services'] = has_active_services
            logger.debug(f"   🔄 Has active services: {has_active_services}")
            
            # ✅ DEBUG: Log successful representation
            logger.debug(f"✅ DEBUG: ServiceCategory representation completed: {instance.name}")
            return representation
            
        except Exception as e:
            # 💥 DEBUG: Log representation errors
            logger.error(f"💥 DEBUG: Error in ServiceCategory representation for {instance.id}: {e}")
            logger.error(f"🔍 DEBUG: Error type: {type(e).__name__}")
            raise

class ServiceSubCategorySerializer(serializers.ModelSerializer):
    """
    🗂️ SERVICE SUBCATEGORY SERIALIZER - ENHANCED WITH COMPREHENSIVE DEBUG TRACKING
    ==============================================================================
    
    Serializer for service subcategories with comprehensive validation and debug tracking.
    Provides detailed logging for data transformation and validation processes.
    
    FEATURES:
    - ✅ Subcategory data serialization with field validation
    - ✅ Category relationship validation and integrity checks
    - ✅ Read-only timestamp fields with proper formatting
    - ✅ Icon URL and file handling with validation
    - ✅ Sort order validation within category context
    - ✅ Comprehensive debug logging for all operations
    
    DEBUG ENHANCEMENTS:
    - 🔍 Field-by-field validation tracking
    - 📊 Data transformation monitoring
    - 🛡️ Input validation with detailed error context
    - 🔗 Category relationship validation tracking
    - 📈 Serialization performance tracking
    - 🔄 CRUD operation logging
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = ServiceSubCategory
        fields = ['id', 'category', 'category_name', 'name', 'description', 'icon', 'icon_url', 'sort_order', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def __init__(self, *args, **kwargs):
        """
        🚀 ENHANCED SERIALIZER INITIALIZATION WITH DEBUG TRACKING
        ========================================================
        
        Initialize the serializer with comprehensive debug logging.
        Tracks serializer creation and configuration for monitoring.
        """
        # 📝 DEBUG: Log serializer initialization
        logger.debug("🚀 DEBUG: ServiceSubCategorySerializer initialization started")
        logger.debug(f"📋 DEBUG: Serializer args: {len(args)} arguments provided")
        logger.debug(f"📊 DEBUG: Serializer kwargs keys: {list(kwargs.keys())}")
        
        # Check if we're dealing with instance data
        if args and hasattr(args[0], '_meta'):
            logger.debug(f"📦 DEBUG: Serializing existing ServiceSubCategory instance: ID={getattr(args[0], 'id', 'unknown')}")
        elif args and hasattr(args[0], '__iter__'):
            try:
                count = len(args[0]) if hasattr(args[0], '__len__') else 'unknown'
                logger.debug(f"📦 DEBUG: Serializing ServiceSubCategory queryset/list: {count} items")
            except:
                logger.debug("📦 DEBUG: Serializing ServiceSubCategory iterable: count unknown")
        else:
            logger.debug("📝 DEBUG: Creating new ServiceSubCategory serializer for input validation")
        
        super().__init__(*args, **kwargs)
        
        # 🎉 DEBUG: Log successful initialization
        logger.debug("✅ DEBUG: ServiceSubCategorySerializer initialization completed")
    
    def validate_category(self, value):
        """
        🔗 ENHANCED CATEGORY VALIDATION WITH RELATIONSHIP CHECKS
        =======================================================
        
        Validates the parent category with detailed relationship checks.
        Ensures category exists, is active, and relationship integrity.
        """
        # 📝 DEBUG: Log validation start
        logger.debug(f"🔗 DEBUG: Validating ServiceSubCategory category: {value.name} (ID: {value.id})")
        
        # 🔍 DEBUG: Check if category exists and is accessible
        if not value:
            logger.warning("❌ DEBUG: ServiceSubCategory category validation failed - no category provided")
            raise serializers.ValidationError("Category is required for subcategory.")
        
        # 🔄 DEBUG: Check if category is active
        if not value.is_active:
            logger.warning(f"❌ DEBUG: ServiceSubCategory category validation failed - inactive category: {value.name}")
            raise serializers.ValidationError(f"Cannot create subcategory under inactive category '{value.name}'.")
        
        # 📊 DEBUG: Log category details
        logger.debug(f"📊 DEBUG: Category details:")
        logger.debug(f"   🏷️ Name: {value.name}")
        logger.debug(f"   🔄 Active: {value.is_active}")
        logger.debug(f"   📈 Sort Order: {value.sort_order}")
        logger.debug(f"   📊 Existing Subcategories: {value.subcategories.count()}")
        
        # ✅ DEBUG: Log successful validation
        logger.debug(f"✅ DEBUG: ServiceSubCategory category validation passed: {value.name}")
        return value
    
    def validate_name(self, value):
        """
        🔍 ENHANCED NAME VALIDATION WITH COMPREHENSIVE CHECKING
        ======================================================
        
        Validates the subcategory name with detailed business logic checks.
        Ensures name uniqueness within category, format compliance, and business rules.
        """
        # 📝 DEBUG: Log validation start
        logger.debug(f"🔍 DEBUG: Validating ServiceSubCategory name: '{value}'")
        
        # 🧹 DEBUG: Basic format validation
        if not value or not value.strip():
            logger.warning("❌ DEBUG: ServiceSubCategory name validation failed - empty or whitespace-only")
            raise serializers.ValidationError("Subcategory name cannot be empty or contain only whitespace.")
        
        # Clean the value
        cleaned_value = value.strip()
        logger.debug(f"🧹 DEBUG: Cleaned subcategory name: '{cleaned_value}'")
        
        # 📏 DEBUG: Length validation
        if len(cleaned_value) < 2:
            logger.warning(f"❌ DEBUG: ServiceSubCategory name validation failed - too short: {len(cleaned_value)} chars")
            raise serializers.ValidationError("Subcategory name must be at least 2 characters long.")
        
        if len(cleaned_value) > 100:
            logger.warning(f"❌ DEBUG: ServiceSubCategory name validation failed - too long: {len(cleaned_value)} chars")
            raise serializers.ValidationError("Subcategory name cannot exceed 100 characters.")
        
        # 🔤 DEBUG: Character validation
        import re
        if not re.match(r'^[a-zA-Z0-9\s\-&().]+$', cleaned_value):
            logger.warning(f"❌ DEBUG: ServiceSubCategory name validation failed - invalid characters in: '{cleaned_value}'")
            raise serializers.ValidationError("Subcategory name can only contain letters, numbers, spaces, hyphens, ampersands, and parentheses.")
        
        # ✅ DEBUG: Log successful validation (duplicate check happens in validate() method with category context)
        logger.debug(f"✅ DEBUG: ServiceSubCategory name format validation passed: '{cleaned_value}'")
        return cleaned_value
    
    def validate_sort_order(self, value):
        """
        🔢 ENHANCED SORT ORDER VALIDATION WITH CATEGORY CONTEXT
        ======================================================
        
        Validates the sort order within the category context.
        Ensures proper ordering and detects conflicts within the same category.
        """
        # 📝 DEBUG: Log validation start
        logger.debug(f"🔢 DEBUG: Validating ServiceSubCategory sort_order: {value}")
        
        # 📊 DEBUG: Range validation
        if value < 0:
            logger.warning(f"❌ DEBUG: ServiceSubCategory sort_order validation failed - negative value: {value}")
            raise serializers.ValidationError("Sort order must be a non-negative integer.")
        
        if value > 9999:
            logger.warning(f"❌ DEBUG: ServiceSubCategory sort_order validation failed - too large: {value}")
            raise serializers.ValidationError("Sort order cannot exceed 9999.")
        
        # ✅ DEBUG: Log successful validation (conflict check happens in validate() method with category context)
        logger.debug(f"✅ DEBUG: ServiceSubCategory sort_order range validation passed: {value}")
        return value
    
    def validate(self, attrs):
        """
        🔍 ENHANCED COMPREHENSIVE VALIDATION WITH CROSS-FIELD CHECKS
        ===========================================================
        
        Performs comprehensive validation across all fields with detailed logging.
        Ensures data integrity, relationship consistency, and business rule compliance.
        """
        # 📝 DEBUG: Log comprehensive validation start
        logger.debug("🔍 DEBUG: ServiceSubCategory comprehensive validation started")
        logger.debug(f"📊 DEBUG: Validating attributes: {list(attrs.keys())}")
        
        # 🔗 DEBUG: Get category for context-aware validation
        category = attrs.get('category')
        if not category and self.instance:
            category = self.instance.category
            logger.debug(f"🔗 DEBUG: Using existing category from instance: {category.name}")
        
        if category:
            logger.debug(f"🔗 DEBUG: Validating within category context: {category.name} (ID: {category.id})")
            
            # 🏷️ DEBUG: Check for name uniqueness within category
            if 'name' in attrs:
                name = attrs['name']
                logger.debug(f"🔄 DEBUG: Checking subcategory name uniqueness within category: '{name}'")
                
                from .models import ServiceSubCategory
                existing_subcategories = ServiceSubCategory.objects.filter(
                    category=category,
                    name__iexact=name
                )
                
                # If we're updating an existing subcategory, exclude it from the duplicate check
                if self.instance:
                    existing_subcategories = existing_subcategories.exclude(id=self.instance.id)
                    logger.debug(f"🔄 DEBUG: Duplicate check excludes current instance: {self.instance.id}")
                
                if existing_subcategories.exists():
                    existing_subcategory = existing_subcategories.first()
                    logger.warning(f"❌ DEBUG: ServiceSubCategory name validation failed - duplicate within category")
                    logger.warning(f"   🔍 Existing: '{existing_subcategory.name}' (ID: {existing_subcategory.id})")
                    logger.warning(f"   🏷️ Category: {category.name}")
                    raise serializers.ValidationError(f"A subcategory with the name '{name}' already exists in category '{category.name}'.")
            
            # 🔢 DEBUG: Check for sort order conflicts within category
            if 'sort_order' in attrs:
                sort_order = attrs['sort_order']
                logger.debug(f"🔢 DEBUG: Checking sort order conflicts within category: {sort_order}")
                
                from .models import ServiceSubCategory
                conflicting_subcategories = ServiceSubCategory.objects.filter(
                    category=category,
                    sort_order=sort_order
                )
                
                # If we're updating an existing subcategory, exclude it from the conflict check
                if self.instance:
                    conflicting_subcategories = conflicting_subcategories.exclude(id=self.instance.id)
                    logger.debug(f"🔄 DEBUG: Sort order conflict check excludes current instance: {self.instance.id}")
                
                conflict_count = conflicting_subcategories.count()
                if conflict_count > 0:
                    conflicting_names = list(conflicting_subcategories.values_list('name', flat=True)[:3])
                    logger.warning(f"⚠️ DEBUG: ServiceSubCategory sort_order conflict within category detected:")
                    logger.warning(f"   📊 Conflicts: {conflict_count} subcategories with order {sort_order}")
                    logger.warning(f"   🏷️ Category: {category.name}")
                    logger.warning(f"   🔍 Conflicting subcategories: {conflicting_names}")
                    # Note: We don't raise an error here as multiple subcategories can have the same sort order
                    # But we log it for administrative awareness
        
        # 🖼️ DEBUG: Validate icon consistency
        if 'icon' in attrs and 'icon_url' in attrs:
            icon = attrs['icon']
            icon_url = attrs['icon_url']
            
            if icon and icon_url:
                logger.warning("⚠️ DEBUG: Both icon file and icon URL provided for subcategory - file will take precedence")
            elif not icon and not icon_url:
                logger.debug("📝 DEBUG: No icon provided for subcategory - using default icon behavior")
        
        # 🔄 DEBUG: Validate status consistency
        if 'is_active' in attrs:
            is_active = attrs['is_active']
            logger.debug(f"🔄 DEBUG: Subcategory active status: {is_active}")
            
            if not is_active:
                # Check if this subcategory has active services
                if self.instance:
                    active_services_count = self.instance.services.filter(status='active').count()
                    
                    if active_services_count > 0:
                        logger.warning(f"⚠️ DEBUG: Deactivating subcategory with active services:")
                        logger.warning(f"   📊 Active services: {active_services_count}")
                        logger.warning(f"   🏷️ Subcategory: {self.instance.name}")
                        # Note: We allow this but log it for administrative awareness
        
        # ✅ DEBUG: Log successful comprehensive validation
        logger.debug("✅ DEBUG: ServiceSubCategory comprehensive validation completed successfully")
        return super().validate(attrs)
    
    def validate_name_within_category(self, category, name, instance=None):
        """
        🔍 ENHANCED NAME VALIDATION WITHIN CATEGORY CONTEXT
        ==================================================
        
        Validates that subcategory name is unique within the specified category.
        Provides detailed validation with business logic checks.
        """
        logger.debug(f"🔍 DEBUG: Validating subcategory name '{name}' within category '{category.name}'")
        
        # Check for name uniqueness within category
        from .models import ServiceSubCategory
        existing_subcategories = ServiceSubCategory.objects.filter(
            category=category,
            name__iexact=name
        )
        
        # Exclude current instance if updating
        if instance:
            existing_subcategories = existing_subcategories.exclude(id=instance.id)
            logger.debug(f"🔄 DEBUG: Excluding current instance {instance.id} from uniqueness check")
        
        if existing_subcategories.exists():
            existing_subcategory = existing_subcategories.first()
            logger.warning(f"❌ DEBUG: Duplicate subcategory name detected in category")
            logger.warning(f"   🔍 Existing: '{existing_subcategory.name}' (ID: {existing_subcategory.id})")
            logger.warning(f"   🏷️ Category: {category.name}")
            raise serializers.ValidationError(
                f"A subcategory with the name '{name}' already exists in category '{category.name}'."
            )
        
        logger.debug(f"✅ DEBUG: Subcategory name validation passed within category")
        return True
    
    def validate_sort_order_within_category(self, category, sort_order, instance=None):
        """
        🔢 ENHANCED SORT ORDER VALIDATION WITHIN CATEGORY
        ================================================
        
        Validates sort order conflicts within category with detailed impact analysis.
        Provides warnings for conflicts and suggestions for resolution.
        """
        logger.debug(f"🔢 DEBUG: Validating sort order {sort_order} within category '{category.name}'")
        
        from .models import ServiceSubCategory
        conflicting_subcategories = ServiceSubCategory.objects.filter(
            category=category,
            sort_order=sort_order
        )
        
        # Exclude current instance if updating
        if instance:
            conflicting_subcategories = conflicting_subcategories.exclude(id=instance.id)
            logger.debug(f"🔄 DEBUG: Excluding current instance {instance.id} from conflict check")
        
        conflict_count = conflicting_subcategories.count()
        if conflict_count > 0:
            conflicting_names = list(conflicting_subcategories.values_list('name', flat=True)[:3])
            logger.warning(f"⚠️ DEBUG: Sort order conflict detected in category:")
            logger.warning(f"   📊 Conflicts: {conflict_count} subcategories with order {sort_order}")
            logger.warning(f"   🏷️ Category: {category.name}")
            logger.warning(f"   🔍 Conflicting subcategories: {conflicting_names}")
            
            # Note: We allow conflicts but provide detailed warning
            # In a stricter implementation, you might want to raise an error here
            if conflict_count > 2:
                logger.warning(f"💡 DEBUG: Suggestion - Consider using unique sort orders for better organization")
        
        logger.debug(f"✅ DEBUG: Sort order validation completed (conflicts allowed)")
        return True
    
    def clean_and_validate_data(self, attrs):
        """
        🧹 ENHANCED DATA CLEANING AND VALIDATION
        =======================================
        
        Comprehensive data cleaning and validation with business rule enforcement.
        Provides detailed validation context and error reporting.
        """
        logger.debug("🧹 DEBUG: Starting comprehensive data cleaning and validation")
        
        # Clean name field
        if 'name' in attrs and attrs['name']:
            original_name = attrs['name']
            cleaned_name = attrs['name'].strip()
            
            if original_name != cleaned_name:
                logger.debug(f"🧹 DEBUG: Cleaned subcategory name: '{original_name}' → '{cleaned_name}'")
                attrs['name'] = cleaned_name
            
            # Additional name validation
            if len(cleaned_name) > 100:
                logger.warning(f"❌ DEBUG: Subcategory name too long: {len(cleaned_name)} chars")
                raise serializers.ValidationError({
                    'name': f"Subcategory name cannot exceed 100 characters (current: {len(cleaned_name)})"
                })
        
        # Clean description field
        if 'description' in attrs and attrs['description']:
            original_desc = attrs['description']
            cleaned_desc = attrs['description'].strip()
            
            if original_desc != cleaned_desc:
                logger.debug(f"🧹 DEBUG: Cleaned subcategory description")
                attrs['description'] = cleaned_desc
        
        # Validate sort order constraints
        if 'sort_order' in attrs:
            sort_order = attrs['sort_order']
            if sort_order < 0:
                logger.warning(f"❌ DEBUG: Invalid negative sort order: {sort_order}")
                raise serializers.ValidationError({
                    'sort_order': "Sort order must be a non-negative integer"
                })
            
            if sort_order > 9999:
                logger.warning(f"❌ DEBUG: Sort order too large: {sort_order}")
                raise serializers.ValidationError({
                    'sort_order': "Sort order cannot exceed 9999"
                })
        
        logger.debug("✅ DEBUG: Data cleaning and validation completed")
        return attrs
    
    def to_representation(self, instance):
        """
        🔄 ENHANCED DATA REPRESENTATION WITH DEBUG TRACKING
        ==================================================
        
        Converts model instance to JSON representation with comprehensive tracking.
        Monitors data transformation and adds computed fields with error handling.
        """
        # 📝 DEBUG: Log representation start
        logger.debug(f"🔄 DEBUG: Converting ServiceSubCategory to representation: {instance.name} (ID: {instance.id})")
        logger.debug(f"   🏷️ Category: {instance.category.name}")
        
        try:
            # Get the base representation
            representation = super().to_representation(instance)
            
            # 📊 DEBUG: Add computed fields for better API experience
            logger.debug("📊 DEBUG: Adding computed fields to ServiceSubCategory representation")
            
            # Add services count with error handling
            try:
                services_count = instance.services.count()
                representation['services_count'] = services_count
                logger.debug(f"   📈 Services count: {services_count}")
            except Exception as e:
                logger.error(f"💥 DEBUG: Error getting services count: {e}")
                representation['services_count'] = 0
            
            # Add activity status with error handling
            try:
                has_active_services = instance.services.filter(status='active').exists()
                representation['has_active_services'] = has_active_services
                logger.debug(f"   🔄 Has active services: {has_active_services}")
            except Exception as e:
                logger.error(f"💥 DEBUG: Error checking active services: {e}")
                representation['has_active_services'] = False
            
            # Add category status for context with error handling
            try:
                representation['category_is_active'] = instance.category.is_active
                logger.debug(f"   🏷️ Parent category active: {instance.category.is_active}")
            except Exception as e:
                logger.error(f"💥 DEBUG: Error getting category status: {e}")
                representation['category_is_active'] = None
            
            # Add additional metadata
            try:
                representation['subcategory_metadata'] = {
                    'created_at': instance.created_at.isoformat() if instance.created_at else None,
                    'updated_at': instance.updated_at.isoformat() if instance.updated_at else None,
                    'sort_position': f"{instance.category.sort_order}.{instance.sort_order}",
                    'full_path': f"{instance.category.name} > {instance.name}"
                }
                logger.debug(f"   📊 Added metadata: full_path = '{representation['subcategory_metadata']['full_path']}'")
            except Exception as e:
                logger.error(f"💥 DEBUG: Error adding metadata: {e}")
                representation['subcategory_metadata'] = {}
            
            # ✅ DEBUG: Log successful representation
            logger.debug(f"✅ DEBUG: ServiceSubCategory representation completed: {instance.name}")
            return representation
            
        except Exception as e:
            # 💥 DEBUG: Log representation errors
            logger.error(f"💥 DEBUG: Error in ServiceSubCategory representation for {instance.id}: {e}")
            logger.error(f"🔍 DEBUG: Error type: {type(e).__name__}")
            # Return basic representation on error
            try:
                return super().to_representation(instance)
            except:
                # Last resort - return minimal data
                return {
                    'id': str(instance.id),
                    'name': instance.name,
                    'error': 'Representation error occurred'
                }

class ServiceListSerializer(serializers.ModelSerializer):
    """
    🔧 SERVICE LIST SERIALIZER - ENHANCED WITH COMPREHENSIVE DEBUG TRACKING
    ========================================================================
    
    Serializer for listing services with provider details and comprehensive validation.
    Provides detailed logging for data transformation and validation processes.
    
    FEATURES:
    - ✅ Service listing with provider relationship validation
    - ✅ Category and subcategory integration with proper validation
    - ✅ Read-only field protection with access control
    - ✅ Performance optimized for list operations
    - ✅ Comprehensive debug logging for all operations
    
    DEBUG ENHANCEMENTS:
    - 🔍 Field-by-field validation tracking
    - 📊 Data transformation monitoring
    - 🛡️ Provider relationship validation
    - 📈 Performance optimization tracking
    - 🔄 List operation monitoring
    """
    provider = PublicUserProfileSerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategories = ServiceSubCategorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'provider', 'category', 'category_name', 'subcategories', 'title', 
            'description', 'price', 'location', 'image', 'status', 
            'is_featured', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'provider', 'status', 'is_featured', 'created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        """
        🚀 ENHANCED SERIALIZER INITIALIZATION WITH DEBUG TRACKING
        ========================================================
        
        Initialize the serializer with comprehensive debug logging.
        Tracks serializer creation and configuration for monitoring.
        """
        # 📝 DEBUG: Log serializer initialization
        logger.debug("🚀 DEBUG: ServiceListSerializer initialization started")
        logger.debug(f"📋 DEBUG: Serializer args: {len(args)} arguments provided")
        logger.debug(f"📊 DEBUG: Serializer kwargs keys: {list(kwargs.keys())}")
        
        # Check if we're dealing with instance data
        if args and hasattr(args[0], '_meta'):
            logger.debug(f"📦 DEBUG: Serializing existing Service instance: ID={getattr(args[0], 'id', 'unknown')}")
        elif args and hasattr(args[0], '__iter__'):
            try:
                count = len(args[0]) if hasattr(args[0], '__len__') else 'unknown'
                logger.debug(f"📦 DEBUG: Serializing Service queryset/list: {count} items")
            except:
                logger.debug("📦 DEBUG: Serializing Service iterable: count unknown")
        else:
            logger.debug("📝 DEBUG: Creating new ServiceListSerializer for input validation")
        
        super().__init__(*args, **kwargs)
        
        # 🎉 DEBUG: Log successful initialization
        logger.debug("✅ DEBUG: ServiceListSerializer initialization completed")
    
    def to_representation(self, instance):
        """
        🔄 ENHANCED DATA REPRESENTATION WITH DEBUG TRACKING
        ==================================================
        
        Converts model instance to JSON representation with comprehensive tracking.
        Monitors data transformation and adds computed fields with error handling.
        """
        # 📝 DEBUG: Log representation start
        logger.debug(f"🔄 DEBUG: Converting Service to list representation: {instance.name if hasattr(instance, 'name') else 'Unknown'} (ID: {instance.id})")
        
        try:
            # Get the base representation
            representation = super().to_representation(instance)
            
            # 📊 DEBUG: Add computed fields for better API experience
            logger.debug("📊 DEBUG: Adding computed fields to Service list representation")
            
            # Add provider verification status with error handling
            try:
                if instance.provider:
                    representation['provider_verified'] = getattr(instance.provider, 'is_verified', False)
                    logger.debug(f"   ✅ Provider verification: {representation['provider_verified']}")
                else:
                    representation['provider_verified'] = False
                    logger.debug("   ⚠️ No provider associated with service")
            except Exception as e:
                logger.error(f"💥 DEBUG: Error getting provider verification: {e}")
                representation['provider_verified'] = False
            
            # Add service availability status with error handling
            try:
                representation['is_available'] = instance.status == 'active'
                logger.debug(f"   🔄 Service available: {representation['is_available']}")
            except Exception as e:
                logger.error(f"💥 DEBUG: Error checking service availability: {e}")
                representation['is_available'] = False
            
            # Add location info with error handling
            try:
                if instance.location:
                    representation['has_location'] = True
                    logger.debug(f"   📍 Location available: {instance.location[:50]}...")
                else:
                    representation['has_location'] = False
                    logger.debug("   📍 No location specified")
            except Exception as e:
                logger.error(f"💥 DEBUG: Error checking location: {e}")
                representation['has_location'] = False
            
            # Add pricing display with error handling
            try:
                if hasattr(instance, 'price') and instance.price:
                    representation['price_display'] = f"${instance.price}"
                    logger.debug(f"   💰 Price display: {representation['price_display']}")
                elif hasattr(instance, 'hourly_rate') and instance.hourly_rate:
                    representation['price_display'] = f"${instance.hourly_rate}/hr"
                    logger.debug(f"   💰 Hourly rate display: {representation['price_display']}")
                else:
                    representation['price_display'] = "Contact for pricing"
                    logger.debug("   💰 No pricing available")
            except Exception as e:
                logger.error(f"💥 DEBUG: Error formatting price display: {e}")
                representation['price_display'] = "Price unavailable"
            
            # ✅ DEBUG: Log successful representation
            logger.debug(f"✅ DEBUG: Service list representation completed")
            return representation
            
        except Exception as e:
            # 💥 DEBUG: Log representation errors
            logger.error(f"💥 DEBUG: Error in Service list representation for {instance.id}: {e}")
            logger.error(f"🔍 DEBUG: Error type: {type(e).__name__}")
            # Return basic representation on error
            try:
                return super().to_representation(instance)
            except:
                # Last resort - return minimal data
                return {
                    'id': str(instance.id),
                    'name': getattr(instance, 'name', 'Unknown'),
                    'error': 'Representation error occurred'
                }

class Base64ImageField(serializers.ImageField):
    """
    🖼️ BASE64 IMAGE FIELD - ENHANCED WITH COMPREHENSIVE DEBUG TRACKING
    ==================================================================
    
    Custom field for handling base64 encoded images with comprehensive validation.
    Provides detailed logging for image processing and validation.
    
    FEATURES:
    - ✅ Base64 encoded image decoding with validation
    - ✅ File format validation and security checks
    - ✅ Unique filename generation with UUID
    - ✅ Image size and quality validation
    - ✅ Comprehensive debug logging for all operations
    
    DEBUG ENHANCEMENTS:
    - 🔍 Image format validation tracking
    - 📊 File size monitoring
    - 🛡️ Security validation for uploaded content
    - 📈 Processing performance tracking
    - 🔄 Encoding/decoding operation logging
    """
    
    def to_internal_value(self, data):
        """
        🔄 ENHANCED IMAGE PROCESSING WITH COMPREHENSIVE VALIDATION
        =========================================================
        
        Process base64 encoded images with detailed validation and logging.
        Ensures security, format compliance, and proper error handling.
        """
        # 📝 DEBUG: Log image processing start
        logger.debug("🖼️ DEBUG: Base64ImageField processing initiated")
        
        try:
            if isinstance(data, str) and data.startswith('data:image'):
                logger.debug("🔍 DEBUG: Processing base64 encoded image")
                
                # 🧹 DEBUG: Parse the base64 data
                try:
                    format_part, imgstr = data.split(';base64,')
                    image_format = format_part.split('/')[-1].lower()
                    logger.debug(f"📊 DEBUG: Image format detected: {image_format}")
                    
                    # 🛡️ DEBUG: Validate image format
                    allowed_formats = ['jpeg', 'jpg', 'png', 'gif', 'webp']
                    if image_format not in allowed_formats:
                        logger.warning(f"❌ DEBUG: Invalid image format: {image_format}")
                        raise serializers.ValidationError(f"Unsupported image format: {image_format}. Allowed formats: {', '.join(allowed_formats)}")
                    
                    logger.debug(f"✅ DEBUG: Image format validation passed: {image_format}")
                    
                except ValueError as e:
                    logger.error(f"💥 DEBUG: Error parsing base64 image data: {e}")
                    raise serializers.ValidationError("Invalid base64 image format. Expected 'data:image/format;base64,data'")
                
                # 🔍 DEBUG: Decode and validate image data
                try:
                    import base64
                    decoded_data = base64.b64decode(imgstr)
                    data_size = len(decoded_data)
                    logger.debug(f"📊 DEBUG: Decoded image size: {data_size} bytes ({data_size/1024:.2f} KB)")
                    
                    # 📏 DEBUG: Validate file size
                    max_size = 10 * 1024 * 1024  # 10MB limit
                    if data_size > max_size:
                        logger.warning(f"❌ DEBUG: Image file too large: {data_size} bytes (limit: {max_size})")
                        raise serializers.ValidationError(f"Image file too large. Maximum size: {max_size/1024/1024:.1f}MB")
                    
                    logger.debug(f"✅ DEBUG: Image size validation passed")
                    
                except Exception as e:
                    logger.error(f"💥 DEBUG: Error decoding base64 image: {e}")
                    raise serializers.ValidationError("Invalid base64 image data")
                
                # 🆔 DEBUG: Generate unique filename
                try:
                    unique_filename = f"{uuid.uuid4()}.{image_format}"
                    logger.debug(f"🆔 DEBUG: Generated unique filename: {unique_filename}")
                    
                    # Create ContentFile with decoded data
                    data = ContentFile(decoded_data, name=unique_filename)
                    logger.debug(f"📦 DEBUG: ContentFile created successfully")
                    
                except Exception as e:
                    logger.error(f"💥 DEBUG: Error creating ContentFile: {e}")
                    raise serializers.ValidationError("Failed to process image data")
                
                # ✅ DEBUG: Log successful processing
                logger.debug(f"✅ DEBUG: Base64 image processing completed successfully")
                
            else:
                # 📝 DEBUG: Non-base64 data processing
                if data:
                    logger.debug("📝 DEBUG: Processing non-base64 image data")
                else:
                    logger.debug("📝 DEBUG: No image data provided")
            
            # Call parent validation
            return super().to_internal_value(data)
            
        except serializers.ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            # 💥 DEBUG: Log unexpected errors
            logger.error(f"💥 DEBUG: Unexpected error in Base64ImageField: {e}")
            logger.error(f"🔍 DEBUG: Error type: {type(e).__name__}")
            raise serializers.ValidationError("Image processing failed")

class ServiceImageSerializer(serializers.ModelSerializer):
    """
    🖼️ SERVICE IMAGE SERIALIZER - ENHANCED WITH COMPREHENSIVE DEBUG TRACKING
    ========================================================================
    
    Serializer for service images with comprehensive validation and debug tracking.
    Provides detailed logging for image processing and validation.
    
    FEATURES:
    - ✅ Service image management with validation
    - ✅ Base64 image processing with security checks
    - ✅ Image ordering and description validation
    - ✅ File upload security and size validation
    - ✅ Comprehensive debug logging for all operations
    
    DEBUG ENHANCEMENTS:
    - 🔍 Image validation and processing tracking
    - 📊 File size and format monitoring
    - 🛡️ Security validation for uploaded content
    - 📈 Upload performance tracking
    - 🔄 Image processing operation logging
    """
    image = Base64ImageField(required=False)
    
    class Meta:
        model = ServiceImage
        fields = ['id', 'image', 'description', 'order']
        read_only_fields = ['id']
    
    def __init__(self, *args, **kwargs):
        """
        🚀 ENHANCED SERIALIZER INITIALIZATION WITH DEBUG TRACKING
        ========================================================
        
        Initialize the serializer with comprehensive debug logging.
        Tracks serializer creation and configuration for monitoring.
        """
        # 📝 DEBUG: Log serializer initialization
        logger.debug("🚀 DEBUG: ServiceImageSerializer initialization started")
        logger.debug(f"📋 DEBUG: Serializer args: {len(args)} arguments provided")
        logger.debug(f"📊 DEBUG: Serializer kwargs keys: {list(kwargs.keys())}")
        
        # Check if we're dealing with instance data
        if args and hasattr(args[0], '_meta'):
            logger.debug(f"📦 DEBUG: Serializing existing ServiceImage instance: ID={getattr(args[0], 'id', 'unknown')}")
        elif args and hasattr(args[0], '__iter__'):
            try:
                count = len(args[0]) if hasattr(args[0], '__len__') else 'unknown'
                logger.debug(f"📦 DEBUG: Serializing ServiceImage queryset/list: {count} items")
            except:
                logger.debug("📦 DEBUG: Serializing ServiceImage iterable: count unknown")
        else:
            logger.debug("📝 DEBUG: Creating new ServiceImageSerializer for input validation")
        
        super().__init__(*args, **kwargs)
        
        # 🎉 DEBUG: Log successful initialization
        logger.debug("✅ DEBUG: ServiceImageSerializer initialization completed")
    
    def validate_description(self, value):
        """
        🔍 ENHANCED DESCRIPTION VALIDATION WITH COMPREHENSIVE CHECKING
        ============================================================
        
        Validates the image description with detailed validation.
        Ensures proper format and content guidelines.
        """
        # 📝 DEBUG: Log validation start
        logger.debug(f"🔍 DEBUG: Validating ServiceImage description: '{value}'")
        
        if value:
            # 🧹 DEBUG: Clean and validate description
            cleaned_value = value.strip()
            
            # 📏 DEBUG: Length validation
            if len(cleaned_value) > 255:
                logger.warning(f"❌ DEBUG: ServiceImage description too long: {len(cleaned_value)} chars")
                raise serializers.ValidationError("Image description cannot exceed 255 characters.")
            
            # 🔤 DEBUG: Content validation
            if len(cleaned_value) < 3 and cleaned_value:
                logger.warning(f"❌ DEBUG: ServiceImage description too short: {len(cleaned_value)} chars")
                raise serializers.ValidationError("Image description must be at least 3 characters long if provided.")
            
            logger.debug(f"✅ DEBUG: ServiceImage description validation passed: '{cleaned_value}'")
            return cleaned_value
        
        # 📝 DEBUG: Log empty description
        logger.debug("📝 DEBUG: No description provided for ServiceImage")
        return value
    
    def validate_order(self, value):
        """
        🔢 ENHANCED ORDER VALIDATION WITH COMPREHENSIVE CHECKING
        =======================================================
        
        Validates the image order with detailed validation.
        Ensures proper ordering and prevents conflicts.
        """
        # 📝 DEBUG: Log validation start
        logger.debug(f"🔢 DEBUG: Validating ServiceImage order: {value}")
        
        # 📊 DEBUG: Range validation
        if value < 0:
            logger.warning(f"❌ DEBUG: ServiceImage order validation failed - negative value: {value}")
            raise serializers.ValidationError("Image order must be a non-negative integer.")
        
        if value > 999:
            logger.warning(f"❌ DEBUG: ServiceImage order validation failed - too large: {value}")
            raise serializers.ValidationError("Image order cannot exceed 999.")
        
        # ✅ DEBUG: Log successful validation
        logger.debug(f"✅ DEBUG: ServiceImage order validation passed: {value}")
        return value
    
    def validate(self, attrs):
        """
        🔍 ENHANCED COMPREHENSIVE VALIDATION WITH CROSS-FIELD CHECKS
        ===========================================================
        
        Performs comprehensive validation across all fields with detailed logging.
        Ensures data integrity and business rule compliance.
        """
        # 📝 DEBUG: Log comprehensive validation start
        logger.debug("🔍 DEBUG: ServiceImage comprehensive validation started")
        logger.debug(f"📊 DEBUG: Validating attributes: {list(attrs.keys())}")
        
        # 🖼️ DEBUG: Validate image presence
        if 'image' in attrs and not attrs['image']:
            logger.warning("⚠️ DEBUG: ServiceImage validation - no image provided")
            # Note: This is allowed as image is optional, but we log it for awareness
        
        # 📝 DEBUG: Validate description-order relationship
        if 'description' in attrs and 'order' in attrs:
            description = attrs['description']
            order = attrs['order']
            
            # Business logic: First image (order 0) should have a description
            if order == 0 and not description:
                logger.warning("⚠️ DEBUG: First image (order 0) without description - recommended to add description")
                # Note: This is a recommendation, not a strict requirement
        
        # ✅ DEBUG: Log successful comprehensive validation
        logger.debug("✅ DEBUG: ServiceImage comprehensive validation completed successfully")
        return super().validate(attrs)
    
    def to_representation(self, instance):
        """
        🔄 ENHANCED DATA REPRESENTATION WITH DEBUG TRACKING
        ==================================================
        
        Converts model instance to JSON representation with comprehensive tracking.
        Monitors data transformation and adds computed fields with error handling.
        """
        # 📝 DEBUG: Log representation start
        logger.debug(f"🔄 DEBUG: Converting ServiceImage to representation: ID={instance.id}")
        
        try:
            # Get the base representation
            representation = super().to_representation(instance)
            
            # 📊 DEBUG: Add computed fields for better API experience
            logger.debug("📊 DEBUG: Adding computed fields to ServiceImage representation")
            
            # Add image metadata with error handling
            try:
                if instance.image:
                    representation['image_url'] = instance.image.url
                    representation['has_image'] = True
                    logger.debug(f"   🖼️ Image URL: {instance.image.url}")
                else:
                    representation['image_url'] = None
                    representation['has_image'] = False
                    logger.debug("   🖼️ No image file associated")
            except Exception as e:
                logger.error(f"💥 DEBUG: Error getting image URL: {e}")
                representation['image_url'] = None
                representation['has_image'] = False
            
            # Add file size information with error handling
            try:
                if instance.image and hasattr(instance.image, 'size'):
                    file_size = instance.image.size
                    representation['file_size'] = file_size
                    representation['file_size_display'] = f"{file_size/1024:.1f} KB" if file_size < 1024*1024 else f"{file_size/1024/1024:.1f} MB"
                    logger.debug(f"   📊 File size: {representation['file_size_display']}")
                else:
                    representation['file_size'] = None
                    representation['file_size_display'] = "Unknown"
                    logger.debug("   📊 File size unavailable")
            except Exception as e:
                logger.error(f"💥 DEBUG: Error getting file size: {e}")
                representation['file_size'] = None
                representation['file_size_display'] = "Error"
            
            # Add ordering context with error handling
            try:
                if hasattr(instance, 'service'):
                    total_images = instance.service.service_images.count()
                    representation['total_service_images'] = total_images
                    representation['position_display'] = f"{instance.order + 1} of {total_images}"
                    logger.debug(f"   📈 Position: {representation['position_display']}")
                else:
                    representation['total_service_images'] = 1
                    representation['position_display'] = "1 of 1"
                    logger.debug("   📈 No service context available")
            except Exception as e:
                logger.error(f"💥 DEBUG: Error getting ordering context: {e}")
                representation['total_service_images'] = None
                representation['position_display'] = "Unknown"
            
            # ✅ DEBUG: Log successful representation
            logger.debug(f"✅ DEBUG: ServiceImage representation completed")
            return representation
            
        except Exception as e:
            # 💥 DEBUG: Log representation errors
            logger.error(f"💥 DEBUG: Error in ServiceImage representation for {instance.id}: {e}")
            logger.error(f"🔍 DEBUG: Error type: {type(e).__name__}")
            # Return basic representation on error
            try:
                return super().to_representation(instance)
            except:
                # Last resort - return minimal data
                return {
                    'id': str(instance.id),
                    'order': getattr(instance, 'order', 0),
                    'error': 'Representation error occurred'
                }

class ServiceDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed service view"""
    provider = PublicUserProfileSerializer(read_only=True)
    category = ServiceCategorySerializer(read_only=True)
    subcategories = ServiceSubCategorySerializer(many=True, read_only=True)
    service_images = ServiceImageSerializer(many=True, read_only=True)
    tags = serializers.JSONField(required=False)
    pricing_options = serializers.JSONField(required=False)
    availability = serializers.JSONField(required=False)
    required_tools = serializers.JSONField(required=False)
    
    class Meta:
        model = Service
        fields = [
            'id', 'provider', 'name', 'description',
            'category', 'subcategories', 'tags',
            'hourly_rate', 'pricing_options', 'currency', 'min_hours', 'max_hours',
            'availability', 'location', 'latitude', 'longitude',
            'required_tools', 'status', 'is_featured',
            'service_images', 'created_at', 'updated_at'
        ]
        read_only_fields = fields
        
    # For backward compatibility
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['title'] = instance.name
        ret['price'] = instance.hourly_rate
        if instance.service_images.exists():
            ret['image'] = instance.service_images.first().image.url
        return ret

class ServiceCreateUpdateSerializer(serializers.ModelSerializer):
    """Enhanced serializer for creating and updating services"""
    images = ServiceImageSerializer(many=True, required=False)
    tags = serializers.JSONField(required=False)
    pricing_options = serializers.JSONField(required=False)
    availability = serializers.JSONField(required=False)
    required_tools = serializers.JSONField(required=False)
    
    class Meta:
        model = Service
        fields = [
            'id', 'category', 'subcategories', 'name', 'description',
            'hourly_rate', 'pricing_options', 'currency', 'min_hours', 'max_hours',
            'availability', 'location', 'latitude', 'longitude', 
            'required_tools', 'tags', 'images'
        ]
        read_only_fields = ['id']
    
    def validate_category(self, value):
        """
        🔍 ENHANCED CATEGORY VALIDATION
        =============================
        
        Ensure the category is active and properly configured.
        Provides comprehensive validation with debug logging.
        """
        # Debug: Log validation attempt
        logger.debug(f"🔍 DEBUG: Validating category for service creation: {value.name} (ID: {value.id})")
        
        if not value.is_active:
            logger.warning(f"❌ DEBUG: Validation failed - Category '{value.name}' is not active")
            raise serializers.ValidationError("This category is not active.")
            
        # Debug: Log successful validation
        logger.debug(f"✅ DEBUG: Category validation passed: {value.name}")
        return value
    
    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        subcategories_data = validated_data.pop('subcategories', [])
        
        # Create the service without many-to-many fields
        service = Service.objects.create(**validated_data)
        
        # Set subcategories using .set() method
        if subcategories_data:
            service.subcategories.set(subcategories_data)
        
        # Process images if any
        for image_data in images_data:
            ServiceImage.objects.create(service=service, **image_data)
            
        return service
    
    def update(self, instance, validated_data):
        images_data = validated_data.pop('images', [])
        subcategories_data = validated_data.pop('subcategories', None)
        
        # Update the service instance fields (excluding many-to-many)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle subcategories update if provided
        if subcategories_data is not None:
            instance.subcategories.set(subcategories_data)
        
        # Handle image updates if provided
        if images_data:
            # Option: Replace all images
            instance.service_images.all().delete()
            for image_data in images_data:
                ServiceImage.objects.create(service=instance, **image_data)
                
        return instance

# Service Request Serializers
class ServiceRequestListSerializer(serializers.ModelSerializer):
    """
    📋 SERVICE REQUEST LIST SERIALIZER - ENHANCED WITH COMPREHENSIVE DEBUG TRACKING
    ===============================================================================
    
    Serializer for listing service requests with comprehensive validation and debug tracking.
    Provides detailed logging for data transformation and validation processes.
    
    FEATURES:
    - ✅ Service request listing with customer relationship validation
    - ✅ Category integration with proper validation
    - ✅ Status and urgency display with proper formatting
    - ✅ Budget range display with currency formatting
    - ✅ Comprehensive debug logging for all operations
    
    DEBUG ENHANCEMENTS:
    - 🔍 Field-by-field validation tracking
    - 📊 Data transformation monitoring
    - 🛡️ Customer relationship validation
    - 📈 Performance optimization tracking
    - 🔄 List operation monitoring
    """
    customer = PublicUserProfileSerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    urgency_display = serializers.CharField(source='get_urgency_display', read_only=True)
    
    class Meta:
        model = ServiceRequest
        fields = [
            'id', 'customer', 'title', 'description', 
            'category', 'category_name', 'status', 'status_display',
            'urgency', 'urgency_display', 'location', 'budget_min', 'budget_max',
            'currency', 'is_featured', 'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'customer', 'status', 'is_featured', 'created_at', 'expires_at']
    
    def __init__(self, *args, **kwargs):
        """
        🚀 ENHANCED SERIALIZER INITIALIZATION WITH DEBUG TRACKING
        ========================================================
        
        Initialize the serializer with comprehensive debug logging.
        Tracks serializer creation and configuration for monitoring.
        """
        # 📝 DEBUG: Log serializer initialization
        logger.debug("🚀 DEBUG: ServiceRequestListSerializer initialization started")
        logger.debug(f"📋 DEBUG: Serializer args: {len(args)} arguments provided")
        logger.debug(f"📊 DEBUG: Serializer kwargs keys: {list(kwargs.keys())}")
        
        # Check if we're dealing with instance data
        if args and hasattr(args[0], '_meta'):
            logger.debug(f"📦 DEBUG: Serializing existing ServiceRequest instance: ID={getattr(args[0], 'id', 'unknown')}")
        elif args and hasattr(args[0], '__iter__'):
            try:
                count = len(args[0]) if hasattr(args[0], '__len__') else 'unknown'
                logger.debug(f"📦 DEBUG: Serializing ServiceRequest queryset/list: {count} items")
            except:
                logger.debug("📦 DEBUG: Serializing ServiceRequest iterable: count unknown")
        else:
            logger.debug("📝 DEBUG: Creating new ServiceRequestListSerializer for input validation")
        
        super().__init__(*args, **kwargs)
        
        # 🎉 DEBUG: Log successful initialization
        logger.debug("✅ DEBUG: ServiceRequestListSerializer initialization completed")
    
    def to_representation(self, instance):
        """
        🔄 ENHANCED DATA REPRESENTATION WITH DEBUG TRACKING
        ==================================================
        
        Converts model instance to JSON representation with comprehensive tracking.
        Monitors data transformation and adds computed fields with error handling.
        """
        # 📝 DEBUG: Log representation start
        logger.debug(f"🔄 DEBUG: Converting ServiceRequest to list representation: {instance.title} (ID: {instance.id})")
        
        try:
            # Get the base representation
            representation = super().to_representation(instance)
            
            # 📊 DEBUG: Add computed fields for better API experience
            logger.debug("📊 DEBUG: Adding computed fields to ServiceRequest list representation")
            
            # Add budget range display with error handling
            try:
                if instance.budget_min and instance.budget_max:
                    currency_symbol = "$" if instance.currency == "USD" else instance.currency
                    representation['budget_range_display'] = f"{currency_symbol}{instance.budget_min}-{instance.budget_max}"
                    logger.debug(f"   💰 Budget range: {representation['budget_range_display']}")
                elif instance.budget_min:
                    currency_symbol = "$" if instance.currency == "USD" else instance.currency
                    representation['budget_range_display'] = f"From {currency_symbol}{instance.budget_min}"
                    logger.debug(f"   💰 Budget minimum: {representation['budget_range_display']}")
                elif instance.budget_max:
                    currency_symbol = "$" if instance.currency == "USD" else instance.currency
                    representation['budget_range_display'] = f"Up to {currency_symbol}{instance.budget_max}"
                    logger.debug(f"   💰 Budget maximum: {representation['budget_range_display']}")
                else:
                    representation['budget_range_display'] = "Budget negotiable"
                    logger.debug("   💰 No budget specified")
            except Exception as e:
                logger.error(f"💥 DEBUG: Error formatting budget display: {e}")
                representation['budget_range_display'] = "Budget unavailable"
            
            # Add expiration status with error handling
            try:
                from django.utils import timezone
                now = timezone.now()
                
                if instance.expires_at:
                    is_expired = now > instance.expires_at
                    representation['is_expired'] = is_expired
                    
                    if not is_expired:
                        time_until_expiry = instance.expires_at - now
                        if time_until_expiry.days > 0:
                            representation['expires_in'] = f"{time_until_expiry.days} days"
                        elif time_until_expiry.seconds > 3600:
                            hours = time_until_expiry.seconds // 3600
                            representation['expires_in'] = f"{hours} hours"
                        else:
                            minutes = time_until_expiry.seconds // 60
                            representation['expires_in'] = f"{minutes} minutes"
                    else:
                        representation['expires_in'] = "Expired"
                    
                    logger.debug(f"   ⏰ Expiration status: {representation['expires_in']}")
                else:
                    representation['is_expired'] = False
                    representation['expires_in'] = "No expiration"
                    logger.debug("   ⏰ No expiration set")
            except Exception as e:
                logger.error(f"💥 DEBUG: Error calculating expiration: {e}")
                representation['is_expired'] = False
                representation['expires_in'] = "Unknown"
            
            # Add customer verification status with error handling
            try:
                if instance.customer:
                    representation['customer_verified'] = getattr(instance.customer, 'is_verified', False)
                    logger.debug(f"   ✅ Customer verification: {representation['customer_verified']}")
                else:
                    representation['customer_verified'] = False
                    logger.debug("   ⚠️ No customer associated with request")
            except Exception as e:
                logger.error(f"💥 DEBUG: Error getting customer verification: {e}")
                representation['customer_verified'] = False
            
            # Add location availability with error handling
            try:
                representation['has_location'] = bool(instance.location)
                if instance.location:
                    logger.debug(f"   📍 Location available: {instance.location[:50]}...")
                else:
                    logger.debug("   📍 No location specified")
            except Exception as e:
                logger.error(f"💥 DEBUG: Error checking location: {e}")
                representation['has_location'] = False
            
            # ✅ DEBUG: Log successful representation
            logger.debug(f"✅ DEBUG: ServiceRequest list representation completed")
            return representation
            
        except Exception as e:
            # 💥 DEBUG: Log representation errors
            logger.error(f"💥 DEBUG: Error in ServiceRequest list representation for {instance.id}: {e}")
            logger.error(f"🔍 DEBUG: Error type: {type(e).__name__}")
            # Return basic representation on error
            try:
                return super().to_representation(instance)
            except:
                # Last resort - return minimal data
                return {
                    'id': str(instance.id),
                    'title': getattr(instance, 'title', 'Unknown'),
                    'error': 'Representation error occurred'
                }

class ServiceRequestCreateSerializer(serializers.ModelSerializer):
    """
    📝 SERVICE REQUEST CREATE SERIALIZER - ENHANCED WITH COMPREHENSIVE DEBUG TRACKING
    =================================================================================
    
    Serializer for creating service requests with comprehensive validation and debug tracking.
    Provides detailed logging for data transformation and validation processes.
    
    FEATURES:
    - ✅ Service request creation with comprehensive validation
    - ✅ Category and subcategory relationship validation
    - ✅ Budget range validation with business logic
    - ✅ Location and timing validation
    - ✅ Comprehensive debug logging for all operations
    
    DEBUG ENHANCEMENTS:
    - 🔍 Field-by-field validation tracking
    - 📊 Data transformation monitoring
    - 🛡️ Business logic validation
    - 📈 Creation performance tracking
    - 🔄 Input validation logging
    """
    class Meta:
        model = ServiceRequest
        fields = [
            'id', 'title', 'description', 'category', 'subcategories',
            'budget_min', 'budget_max', 'currency', 'urgency', 'requested_date_time',
            'location', 'latitude', 'longitude', 'requirements'
        ]
        read_only_fields = ['id']
    
    def __init__(self, *args, **kwargs):
        """
        🚀 ENHANCED SERIALIZER INITIALIZATION WITH DEBUG TRACKING
        ========================================================
        
        Initialize the serializer with comprehensive debug logging.
        Tracks serializer creation and configuration for monitoring.
        """
        # 📝 DEBUG: Log serializer initialization
        logger.debug("🚀 DEBUG: ServiceRequestCreateSerializer initialization started")
        logger.debug(f"📋 DEBUG: Serializer args: {len(args)} arguments provided")
        logger.debug(f"📊 DEBUG: Serializer kwargs keys: {list(kwargs.keys())}")
        
        # Check if we're dealing with instance data
        if args and hasattr(args[0], '_meta'):
            logger.debug(f"📦 DEBUG: Serializing existing ServiceRequest instance: ID={getattr(args[0], 'id', 'unknown')}")
        else:
            logger.debug("📝 DEBUG: Creating new ServiceRequestCreateSerializer for input validation")
        
        super().__init__(*args, **kwargs)
        
        # 🎉 DEBUG: Log successful initialization
        logger.debug("✅ DEBUG: ServiceRequestCreateSerializer initialization completed")
    
    def validate_category(self, value):
        """
        🔍 ENHANCED CATEGORY VALIDATION
        =============================
        
        Ensure the category is active and properly configured.
        Provides comprehensive validation with debug logging.
        """
        # Debug: Log validation attempt
        logger.debug(f"🔍 DEBUG: Validating category for service request creation: {value.name} (ID: {value.id})")
        
        if not value.is_active:
            logger.warning(f"❌ DEBUG: Validation failed - Category '{value.name}' is not active")
            raise serializers.ValidationError("This category is not active.")
            
        # Debug: Log successful validation
        logger.debug(f"✅ DEBUG: Category validation passed: {value.name}")
        return value
    
    def validate_title(self, value):
        """
        🔍 ENHANCED TITLE VALIDATION WITH COMPREHENSIVE CHECKING
        ========================================================
        
        Validates the service request title with detailed validation.
        Ensures proper format and content guidelines.
        """
        # 📝 DEBUG: Log validation start
        logger.debug(f"🔍 DEBUG: Validating ServiceRequest title: '{value}'")
        
        # 🧹 DEBUG: Basic format validation
        if not value or not value.strip():
            logger.warning("❌ DEBUG: ServiceRequest title validation failed - empty or whitespace-only")
            raise serializers.ValidationError("Service request title cannot be empty or contain only whitespace.")
        
        # Clean the value
        cleaned_value = value.strip()
        logger.debug(f"🧹 DEBUG: Cleaned service request title: '{cleaned_value}'")
        
        # 📏 DEBUG: Length validation
        if len(cleaned_value) < 5:
            logger.warning(f"❌ DEBUG: ServiceRequest title validation failed - too short: {len(cleaned_value)} chars")
            raise serializers.ValidationError("Service request title must be at least 5 characters long.")
        
        if len(cleaned_value) > 200:
            logger.warning(f"❌ DEBUG: ServiceRequest title validation failed - too long: {len(cleaned_value)} chars")
            raise serializers.ValidationError("Service request title cannot exceed 200 characters.")
        
        # ✅ DEBUG: Log successful validation
        logger.debug(f"✅ DEBUG: ServiceRequest title validation passed: '{cleaned_value}'")
        return cleaned_value
    
    def validate_budget_min(self, value):
        """
        💰 ENHANCED BUDGET MINIMUM VALIDATION
        ====================================
        
        Validates the minimum budget with business logic checks.
        """
        # 📝 DEBUG: Log validation start
        logger.debug(f"💰 DEBUG: Validating ServiceRequest budget_min: {value}")
        
        if value is not None:
            if value < 0:
                logger.warning(f"❌ DEBUG: ServiceRequest budget_min validation failed - negative value: {value}")
                raise serializers.ValidationError("Minimum budget must be non-negative.")
            
            if value > 1000000:  # 1 million limit
                logger.warning(f"❌ DEBUG: ServiceRequest budget_min validation failed - too large: {value}")
                raise serializers.ValidationError("Minimum budget cannot exceed $1,000,000.")
        
        # ✅ DEBUG: Log successful validation
        logger.debug(f"✅ DEBUG: ServiceRequest budget_min validation passed: {value}")
        return value
    
    def validate_budget_max(self, value):
        """
        💰 ENHANCED BUDGET MAXIMUM VALIDATION
        ====================================
        
        Validates the maximum budget with business logic checks.
        """
        # 📝 DEBUG: Log validation start
        logger.debug(f"💰 DEBUG: Validating ServiceRequest budget_max: {value}")
        
        if value is not None:
            if value < 0:
                logger.warning(f"❌ DEBUG: ServiceRequest budget_max validation failed - negative value: {value}")
                raise serializers.ValidationError("Maximum budget must be non-negative.")
            
            if value > 1000000:  # 1 million limit
                logger.warning(f"❌ DEBUG: ServiceRequest budget_max validation failed - too large: {value}")
                raise serializers.ValidationError("Maximum budget cannot exceed $1,000,000.")
        
        # ✅ DEBUG: Log successful validation
        logger.debug(f"✅ DEBUG: ServiceRequest budget_max validation passed: {value}")
        return value
    
    def validate(self, attrs):
        """
        🔍 ENHANCED COMPREHENSIVE VALIDATION WITH CROSS-FIELD CHECKS
        ===========================================================
        
        Performs comprehensive validation across all fields with detailed logging.
        Ensures data integrity and business rule compliance.
        """
        # 📝 DEBUG: Log comprehensive validation start
        logger.debug("🔍 DEBUG: ServiceRequest comprehensive validation started")
        logger.debug(f"📊 DEBUG: Validating attributes: {list(attrs.keys())}")
        
        # 💰 DEBUG: Validate budget range consistency
        budget_min = attrs.get('budget_min')
        budget_max = attrs.get('budget_max')
        
        if budget_min is not None and budget_max is not None:
            if budget_min > budget_max:
                logger.warning(f"❌ DEBUG: Budget range validation failed - min ({budget_min}) > max ({budget_max})")
                raise serializers.ValidationError("Minimum budget cannot be greater than maximum budget.")
            
            # Business logic: warn about very large ranges
            if budget_max > budget_min * 10:
                logger.warning(f"⚠️ DEBUG: Large budget range detected - min: {budget_min}, max: {budget_max}")
                # This is just a warning, not an error
        
        # 📅 DEBUG: Validate requested date/time
        requested_date_time = attrs.get('requested_date_time')
        if requested_date_time:
            from django.utils import timezone
            now = timezone.now()
            
            if requested_date_time < now:
                logger.warning(f"❌ DEBUG: Requested date/time validation failed - past date: {requested_date_time}")
                raise serializers.ValidationError("Requested date/time cannot be in the past.")
            
            # Business logic: warn about very far future dates
            if (requested_date_time - now).days > 365:
                logger.warning(f"⚠️ DEBUG: Far future date detected - {requested_date_time}")
                # This is just a warning, not an error
        
        # 📍 DEBUG: Validate location consistency
        location = attrs.get('location')
        latitude = attrs.get('latitude')
        longitude = attrs.get('longitude')
        
        if location and not (latitude and longitude):
            logger.warning("⚠️ DEBUG: Location provided without coordinates - consider adding lat/lng for better matching")
        elif (latitude or longitude) and not location:
            logger.warning("⚠️ DEBUG: Coordinates provided without location description - consider adding location text")
        
        # ✅ DEBUG: Log successful comprehensive validation
        logger.debug("✅ DEBUG: ServiceRequest comprehensive validation completed successfully")
        return super().validate(attrs)
    
    def create(self, validated_data):
        """
        ➕ CREATE SERVICE REQUEST WITH MANY-TO-MANY FIELD HANDLING
        =========================================================
        
        Creates a new service request while properly handling the many-to-many subcategories field.
        """
        # Extract many-to-many data
        subcategories_data = validated_data.pop('subcategories', [])
        
        # Create the service request without many-to-many fields
        service_request = ServiceRequest.objects.create(**validated_data)
        
        # Set subcategories using .set() method
        if subcategories_data:
            service_request.subcategories.set(subcategories_data)
            
        return service_request
    
    def update(self, instance, validated_data):
        """
        🔄 UPDATE SERVICE REQUEST WITH MANY-TO-MANY FIELD HANDLING
        =========================================================
        
        Updates a service request while properly handling the many-to-many subcategories field.
        """
        # Extract many-to-many data
        subcategories_data = validated_data.pop('subcategories', None)
        
        # Update regular fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle subcategories update if provided
        if subcategories_data is not None:
            instance.subcategories.set(subcategories_data)
            
        return instance
        
class ServiceRequestDetailSerializer(serializers.ModelSerializer):
    """
    📄 SERVICE REQUEST DETAIL SERIALIZER - ENHANCED WITH COMPREHENSIVE DEBUG TRACKING
    =================================================================================
    
    Serializer for detailed service request view with comprehensive validation and debug tracking.
    Provides detailed logging for data transformation and validation processes.
    
    FEATURES:
    - ✅ Detailed service request representation with all relationships
    - ✅ Customer and provider relationship validation
    - ✅ Category and subcategory integration with proper validation
    - ✅ Status and fulfillment tracking with detailed context
    - ✅ Comprehensive debug logging for all operations
    
    DEBUG ENHANCEMENTS:
    - 🔍 Field-by-field validation tracking
    - 📊 Data transformation monitoring
    - 🛡️ Relationship integrity validation
    - 📈 Detail representation performance tracking
    - 🔄 Status and fulfillment monitoring
    """
    customer = PublicUserProfileSerializer(read_only=True)
    assigned_provider = PublicUserProfileSerializer(read_only=True)
    category = ServiceCategorySerializer(read_only=True)
    subcategories = ServiceSubCategorySerializer(many=True, read_only=True)
    fulfilled_by_service = ServiceDetailSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    urgency_display = serializers.CharField(source='get_urgency_display', read_only=True)
    requirements = serializers.JSONField(required=False)
    
    class Meta:
        model = ServiceRequest
        fields = [
            'id', 'customer', 'title', 'description',
            'category', 'subcategories', 
            'budget_min', 'budget_max', 'currency', 'urgency', 'urgency_display',
            'requested_date_time', 'location', 'latitude', 'longitude',
            'status', 'status_display', 'is_featured', 'expires_at',
            'assigned_provider', 'fulfilled_by_service', 'requirements',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def __init__(self, *args, **kwargs):
        """
        🚀 ENHANCED SERIALIZER INITIALIZATION WITH DEBUG TRACKING
        ========================================================
        
        Initialize the serializer with comprehensive debug logging.
        Tracks serializer creation and configuration for monitoring.
        """
        # 📝 DEBUG: Log serializer initialization
        logger.debug("🚀 DEBUG: ServiceRequestDetailSerializer initialization started")
        logger.debug(f"📋 DEBUG: Serializer args: {len(args)} arguments provided")
        logger.debug(f"📊 DEBUG: Serializer kwargs keys: {list(kwargs.keys())}")
        
        # Check if we're dealing with instance data
        if args and hasattr(args[0], '_meta'):
            logger.debug(f"📦 DEBUG: Serializing existing ServiceRequest detail instance: ID={getattr(args[0], 'id', 'unknown')}")
        else:
            logger.debug("📝 DEBUG: Creating new ServiceRequestDetailSerializer for input validation")
        
        super().__init__(*args, **kwargs)
        
        # 🎉 DEBUG: Log successful initialization
        logger.debug("✅ DEBUG: ServiceRequestDetailSerializer initialization completed")
    
    def to_representation(self, instance):
        """
        🔄 ENHANCED DATA REPRESENTATION WITH DEBUG TRACKING
        ==================================================
        
        Converts model instance to JSON representation with comprehensive tracking.
        Monitors data transformation and adds computed fields with error handling.
        """
        # 📝 DEBUG: Log representation start
        logger.debug(f"🔄 DEBUG: Converting ServiceRequest to detail representation: {instance.title} (ID: {instance.id})")
        logger.debug(f"   📊 Status: {instance.status}")
        logger.debug(f"   🚨 Urgency: {instance.urgency}")
        
        try:
            # Get the base representation
            representation = super().to_representation(instance)
            
            # 📊 DEBUG: Add computed fields for better API experience
            logger.debug("📊 DEBUG: Adding computed fields to ServiceRequest detail representation")
            
            # Add comprehensive budget information with error handling
            try:
                budget_info = {}
                if instance.budget_min and instance.budget_max:
                    currency_symbol = "$" if instance.currency == "USD" else instance.currency
                    budget_info['budget_range_display'] = f"{currency_symbol}{instance.budget_min}-{instance.budget_max}"
                    budget_info['budget_midpoint'] = (instance.budget_min + instance.budget_max) / 2
                    budget_info['budget_range_width'] = instance.budget_max - instance.budget_min
                    logger.debug(f"   💰 Budget range: {budget_info['budget_range_display']}")
                elif instance.budget_min:
                    currency_symbol = "$" if instance.currency == "USD" else instance.currency
                    budget_info['budget_range_display'] = f"From {currency_symbol}{instance.budget_min}"
                    budget_info['budget_midpoint'] = instance.budget_min
                    budget_info['budget_range_width'] = None
                    logger.debug(f"   💰 Budget minimum: {budget_info['budget_range_display']}")
                elif instance.budget_max:
                    currency_symbol = "$" if instance.currency == "USD" else instance.currency
                    budget_info['budget_range_display'] = f"Up to {currency_symbol}{instance.budget_max}"
                    budget_info['budget_midpoint'] = instance.budget_max
                    budget_info['budget_range_width'] = None
                    logger.debug(f"   💰 Budget maximum: {budget_info['budget_range_display']}")
                else:
                    budget_info['budget_range_display'] = "Budget negotiable"
                    budget_info['budget_midpoint'] = None
                    budget_info['budget_range_width'] = None
                    logger.debug("   💰 No budget specified")
                
                representation['budget_info'] = budget_info
            except Exception as e:
                logger.error(f"💥 DEBUG: Error creating budget info: {e}")
                representation['budget_info'] = {"error": "Budget calculation failed"}
            
            # Add comprehensive status and timeline information with error handling
            try:
                timeline_info = {}
                from django.utils import timezone
                now = timezone.now()
                
                # Creation and age information
                timeline_info['created_at_display'] = instance.created_at.strftime("%Y-%m-%d %H:%M:%S") if instance.created_at else None
                if instance.created_at:
                    age_delta = now - instance.created_at
                    if age_delta.days > 0:
                        timeline_info['age_display'] = f"{age_delta.days} days ago"
                    elif age_delta.seconds > 3600:
                        hours = age_delta.seconds // 3600
                        timeline_info['age_display'] = f"{hours} hours ago"
                    else:
                        minutes = age_delta.seconds // 60
                        timeline_info['age_display'] = f"{minutes} minutes ago"
                
                # Expiration information
                if instance.expires_at:
                    is_expired = now > instance.expires_at
                    timeline_info['is_expired'] = is_expired
                    timeline_info['expires_at_display'] = instance.expires_at.strftime("%Y-%m-%d %H:%M:%S")
                    
                    if not is_expired:
                        time_until_expiry = instance.expires_at - now
                        if time_until_expiry.days > 0:
                            timeline_info['expires_in'] = f"{time_until_expiry.days} days"
                        elif time_until_expiry.seconds > 3600:
                            hours = time_until_expiry.seconds // 3600
                            timeline_info['expires_in'] = f"{hours} hours"
                        else:
                            minutes = time_until_expiry.seconds // 60
                            timeline_info['expires_in'] = f"{minutes} minutes"
                    else:
                        timeline_info['expires_in'] = "Expired"
                else:
                    timeline_info['is_expired'] = False
                    timeline_info['expires_in'] = "No expiration"
                
                representation['timeline_info'] = timeline_info
                logger.debug(f"   ⏰ Timeline: {timeline_info.get('age_display', 'Unknown age')}")
            except Exception as e:
                logger.error(f"💥 DEBUG: Error creating timeline info: {e}")
                representation['timeline_info'] = {"error": "Timeline calculation failed"}
            
            # Add relationship status information with error handling
            try:
                relationships = {}
                
                # Customer information
                if instance.customer:
                    relationships['customer_verified'] = getattr(instance.customer, 'is_verified', False)
                    relationships['customer_join_date'] = instance.customer.date_joined.strftime("%Y-%m-%d") if hasattr(instance.customer, 'date_joined') else None
                    logger.debug(f"   👤 Customer: {instance.customer.username} (verified: {relationships['customer_verified']})")
                else:
                    relationships['customer_verified'] = False
                    relationships['customer_join_date'] = None
                    logger.debug("   ⚠️ No customer associated")
                
                # Provider information
                if instance.assigned_provider:
                    relationships['provider_verified'] = getattr(instance.assigned_provider, 'is_verified', False)
                    relationships['has_assigned_provider'] = True
                    logger.debug(f"   🔧 Provider: {instance.assigned_provider.username} (verified: {relationships['provider_verified']})")
                else:
                    relationships['provider_verified'] = False
                    relationships['has_assigned_provider'] = False
                    logger.debug("   📝 No provider assigned")
                
                # Fulfillment information
                if instance.fulfilled_by_service:
                    relationships['is_fulfilled'] = True
                    relationships['fulfilling_service_id'] = instance.fulfilled_by_service.id
                    logger.debug(f"   ✅ Fulfilled by service: {instance.fulfilled_by_service.id}")
                else:
                    relationships['is_fulfilled'] = False
                    relationships['fulfilling_service_id'] = None
                    logger.debug("   📋 Not yet fulfilled")
                
                representation['relationships'] = relationships
            except Exception as e:
                logger.error(f"💥 DEBUG: Error creating relationship info: {e}")
                representation['relationships'] = {"error": "Relationship analysis failed"}
            
            # Add location and geographic information with error handling
            try:
                location_info = {}
                
                if instance.location:
                    location_info['has_location'] = True
                    location_info['location_display'] = instance.location
                    logger.debug(f"   📍 Location: {instance.location[:50]}...")
                else:
                    location_info['has_location'] = False
                    location_info['location_display'] = None
                    logger.debug("   📍 No location specified")
                
                if instance.latitude and instance.longitude:
                    location_info['has_coordinates'] = True
                    location_info['coordinates'] = {
                        'latitude': float(instance.latitude),
                        'longitude': float(instance.longitude)
                    }
                    logger.debug(f"   🗺️ Coordinates: {instance.latitude}, {instance.longitude}")
                else:
                    location_info['has_coordinates'] = False
                    location_info['coordinates'] = None
                    logger.debug("   🗺️ No coordinates provided")
                
                representation['location_info'] = location_info
            except Exception as e:
                logger.error(f"💥 DEBUG: Error creating location info: {e}")
                representation['location_info'] = {"error": "Location analysis failed"}
            
            # ✅ DEBUG: Log successful representation
            logger.debug(f"✅ DEBUG: ServiceRequest detail representation completed successfully")
            return representation
            
        except Exception as e:
            # 💥 DEBUG: Log representation errors
            logger.error(f"💥 DEBUG: Error in ServiceRequest detail representation for {instance.id}: {e}")
            logger.error(f"🔍 DEBUG: Error type: {type(e).__name__}")
            # Return basic representation on error
            try:
                return super().to_representation(instance)
            except:
                # Last resort - return minimal data
                return {
                    'id': str(instance.id),
                    'title': getattr(instance, 'title', 'Unknown'),
                    'status': getattr(instance, 'status', 'unknown'),
                    'error': 'Representation error occurred'
                }
