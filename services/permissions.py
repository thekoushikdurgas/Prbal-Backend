from rest_framework import permissions
import logging

# 🔍 DEBUG: Setup comprehensive logging for permissions
logger = logging.getLogger(__name__)
logger.info("🚀 DEBUG: Services permissions module loaded successfully")
logger.debug("🔐 DEBUG: Initializing custom permission classes with enhanced debug tracking")

# 🔍 DEBUG: Setup comprehensive logging for permissions
logger = logging.getLogger(__name__)
logger.info("🚀 DEBUG: Services permissions module loaded successfully")
logger.debug("🔐 DEBUG: Initializing custom permission classes with enhanced debug tracking")

class IsServiceProvider(permissions.BasePermission):
    """
    🔧 ENHANCED SERVICE PROVIDER PERMISSION - WITH COMPREHENSIVE DEBUG TRACKING
    ==========================================================================
    
    Custom permission to only allow service providers to create and modify services.
    Provides detailed logging for all permission checks and validation decisions.
    
    FEATURES:
    - ✅ Service provider authentication validation
    - ✅ User type verification and validation
    - ✅ Safe method allowance for read operations
    - ✅ Comprehensive debug logging for all decisions
    - ✅ Detailed error context for permission denials
    
    PERMISSION LOGIC:
    - 🔓 SAFE_METHODS (GET, HEAD, OPTIONS): Allowed for everyone
    - 🔒 WRITE_METHODS (POST, PUT, PATCH, DELETE): Provider only
    
    DEBUG ENHANCEMENTS:
    - 🔍 Permission check initiation tracking
    - 📊 User context and authentication status logging
    - 🛡️ Permission decision reasoning with detailed context
    - 📈 Access pattern monitoring and analytics
    - 🔄 Request method validation tracking
    """
    message = "Only service providers can create or modify services."

    def has_permission(self, request, view):
        """
        🔐 ENHANCED PERMISSION CHECK WITH COMPREHENSIVE DEBUG TRACKING
        =============================================================
        
        Check if the user has permission to perform the requested action.
        Provides detailed logging for all permission decisions.
        """
        # 📝 DEBUG: Log permission check initiation
        logger.debug(f"🔐 DEBUG: IsServiceProvider permission check initiated")
        logger.debug(f"🌐 DEBUG: Request method: {request.method}")
        logger.debug(f"📍 DEBUG: Request path: {request.path}")
        logger.debug(f"👤 DEBUG: User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
        logger.debug(f"🔑 DEBUG: Authenticated: {request.user.is_authenticated}")
        
        # 🔓 DEBUG: Check for safe methods (read operations)
        if request.method in permissions.SAFE_METHODS:
            logger.debug(f"🔓 DEBUG: Safe method detected: {request.method} - allowing access")
            logger.debug(f"📋 DEBUG: Safe methods: {list(permissions.SAFE_METHODS)}")
            logger.info(f"✅ DEBUG: IsServiceProvider permission GRANTED for safe method {request.method}")
            return True
        
        # 🔒 DEBUG: Check for write methods (requires provider authentication)
        logger.debug(f"🔒 DEBUG: Write method detected: {request.method} - checking provider credentials")
        
        # Check authentication first
        if not request.user.is_authenticated:
            logger.warning(f"🚫 DEBUG: IsServiceProvider permission DENIED - user not authenticated")
            logger.debug(f"📊 DEBUG: Permission denial reason: User authentication required for {request.method}")
            return False
        
        # Check user type
        user_type = getattr(request.user, 'user_type', None)
        logger.debug(f"🎭 DEBUG: User type check: '{user_type}'")
        
        if user_type == 'provider':
            logger.info(f"✅ DEBUG: IsServiceProvider permission GRANTED")
            logger.debug(f"🔧 DEBUG: Provider access granted for {request.method} to {request.path}")
            logger.debug(f"👤 DEBUG: Provider: {request.user.username} (ID: {request.user.id})")
            return True
        else:
            logger.warning(f"🚫 DEBUG: IsServiceProvider permission DENIED")
            logger.warning(f"❌ DEBUG: User type '{user_type}' is not 'provider'")
            logger.debug(f"📊 DEBUG: Required user type: 'provider', Actual: '{user_type}'")
            logger.debug(f"👤 DEBUG: User: {request.user.username} (ID: {request.user.id})")
            return False

class IsCustomer(permissions.BasePermission):
    """
    🛒 ENHANCED CUSTOMER PERMISSION - WITH COMPREHENSIVE DEBUG TRACKING
    ===================================================================
    
    Custom permission to only allow customers to create and modify service requests.
    Provides detailed logging for all permission checks and validation decisions.
    
    FEATURES:
    - ✅ Customer authentication validation
    - ✅ User type verification and validation
    - ✅ Safe method allowance for read operations
    - ✅ Comprehensive debug logging for all decisions
    - ✅ Detailed error context for permission denials
    
    PERMISSION LOGIC:
    - 🔓 SAFE_METHODS (GET, HEAD, OPTIONS): Allowed for everyone
    - 🔒 WRITE_METHODS (POST, PUT, PATCH, DELETE): Customer only
    
    DEBUG ENHANCEMENTS:
    - 🔍 Permission check initiation tracking
    - 📊 User context and authentication status logging
    - 🛡️ Permission decision reasoning with detailed context
    - 📈 Access pattern monitoring and analytics
    - 🔄 Request method validation tracking
    """
    message = "Only customers can create or modify service requests."

    def has_permission(self, request, view):
        """
        🔐 ENHANCED PERMISSION CHECK WITH COMPREHENSIVE DEBUG TRACKING
        =============================================================
        
        Check if the user has permission to perform the requested action.
        Provides detailed logging for all permission decisions.
        """
        # 📝 DEBUG: Log permission check initiation
        logger.debug(f"🔐 DEBUG: IsCustomer permission check initiated")
        logger.debug(f"🌐 DEBUG: Request method: {request.method}")
        logger.debug(f"📍 DEBUG: Request path: {request.path}")
        logger.debug(f"👤 DEBUG: User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
        logger.debug(f"🔑 DEBUG: Authenticated: {request.user.is_authenticated}")
        
        # 🔓 DEBUG: Check for safe methods (read operations)
        if request.method in permissions.SAFE_METHODS:
            logger.debug(f"🔓 DEBUG: Safe method detected: {request.method} - allowing access")
            logger.debug(f"📋 DEBUG: Safe methods: {list(permissions.SAFE_METHODS)}")
            logger.info(f"✅ DEBUG: IsCustomer permission GRANTED for safe method {request.method}")
            return True
        
        # 🔒 DEBUG: Check for write methods (requires customer authentication)
        logger.debug(f"🔒 DEBUG: Write method detected: {request.method} - checking customer credentials")
        
        # Check authentication first
        if not request.user.is_authenticated:
            logger.warning(f"🚫 DEBUG: IsCustomer permission DENIED - user not authenticated")
            logger.debug(f"📊 DEBUG: Permission denial reason: User authentication required for {request.method}")
            return False
        
        # Check user type
        user_type = getattr(request.user, 'user_type', None)
        logger.debug(f"🎭 DEBUG: User type check: '{user_type}'")
        
        if user_type == 'customer':
            logger.info(f"✅ DEBUG: IsCustomer permission GRANTED")
            logger.debug(f"🛒 DEBUG: Customer access granted for {request.method} to {request.path}")
            logger.debug(f"👤 DEBUG: Customer: {request.user.username} (ID: {request.user.id})")
            return True
        else:
            logger.warning(f"🚫 DEBUG: IsCustomer permission DENIED")
            logger.warning(f"❌ DEBUG: User type '{user_type}' is not 'customer'")
            logger.debug(f"📊 DEBUG: Required user type: 'customer', Actual: '{user_type}'")
            logger.debug(f"👤 DEBUG: User: {request.user.username} (ID: {request.user.id})")
            return False

class IsOwner(permissions.BasePermission):
    """
    👑 ENHANCED OWNER PERMISSION - WITH COMPREHENSIVE DEBUG TRACKING
    ================================================================
    
    Custom permission to only allow owners of an object to edit or delete it.
    Provides detailed logging for all permission checks and ownership validation.
    
    FEATURES:
    - ✅ Object ownership validation
    - ✅ Multiple ownership field support (provider, seller, customer)
    - ✅ Safe method allowance for read operations
    - ✅ Comprehensive debug logging for all decisions
    - ✅ Detailed error context for permission denials
    
    PERMISSION LOGIC:
    - 🔓 SAFE_METHODS (GET, HEAD, OPTIONS): Allowed for everyone
    - 🔒 WRITE_METHODS (POST, PUT, PATCH, DELETE): Owner only
    
    OWNERSHIP FIELDS SUPPORTED:
    - 🔧 provider: For services (Service model)
    - 🛒 customer: For service requests (ServiceRequest model)
    - 💰 seller: For products (Product model, if applicable)
    
    DEBUG ENHANCEMENTS:
    - 🔍 Permission check initiation tracking
    - 📊 Object context and ownership validation logging
    - 🛡️ Permission decision reasoning with detailed context
    - 📈 Access pattern monitoring and analytics
    - 🔄 Object field validation tracking
    """
    message = "You must be the owner of this object to perform this action."

    def has_object_permission(self, request, view, obj):
        """
        🔐 ENHANCED OBJECT PERMISSION CHECK WITH COMPREHENSIVE DEBUG TRACKING
        ====================================================================
        
        Check if the user has permission to perform the requested action on the specific object.
        Provides detailed logging for all ownership validation and permission decisions.
        """
        # 📝 DEBUG: Log object permission check initiation
        logger.debug(f"🔐 DEBUG: IsOwner object permission check initiated")
        logger.debug(f"🌐 DEBUG: Request method: {request.method}")
        logger.debug(f"📍 DEBUG: Request path: {request.path}")
        logger.debug(f"👤 DEBUG: User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
        logger.debug(f"📦 DEBUG: Object type: {obj.__class__.__name__}")
        logger.debug(f"🆔 DEBUG: Object ID: {getattr(obj, 'id', 'Unknown')}")
        
        # 🔓 DEBUG: Check for safe methods (read operations)
        if request.method in permissions.SAFE_METHODS:
            logger.debug(f"🔓 DEBUG: Safe method detected: {request.method} - allowing access")
            logger.debug(f"📋 DEBUG: Safe methods: {list(permissions.SAFE_METHODS)}")
            logger.info(f"✅ DEBUG: IsOwner permission GRANTED for safe method {request.method}")
            return True
        
        # 🔒 DEBUG: Check for write methods (requires ownership)
        logger.debug(f"🔒 DEBUG: Write method detected: {request.method} - checking object ownership")
        
        # Check authentication first
        if not request.user.is_authenticated:
            logger.warning(f"🚫 DEBUG: IsOwner permission DENIED - user not authenticated")
            logger.debug(f"📊 DEBUG: Permission denial reason: User authentication required for {request.method}")
            return False
        
        # 🔍 DEBUG: Check for various ownership fields
        ownership_fields = ['provider', 'customer', 'seller', 'owner', 'user']
        owner_found = False
        owner_field = None
        owner_user = None
        
        for field in ownership_fields:
            if hasattr(obj, field):
                owner_user = getattr(obj, field)
                owner_field = field
                logger.debug(f"🔍 DEBUG: Found ownership field '{field}' with value: {owner_user.username if owner_user else 'None'}")
                
                if owner_user == request.user:
                    owner_found = True
                    logger.info(f"✅ DEBUG: IsOwner permission GRANTED")
                    logger.debug(f"👑 DEBUG: Owner access granted for {request.method}")
                    logger.debug(f"📊 DEBUG: Ownership confirmed via field '{field}'")
                    logger.debug(f"👤 DEBUG: Owner: {request.user.username} (ID: {request.user.id})")
                    logger.debug(f"📦 DEBUG: Object: {obj.__class__.__name__} (ID: {getattr(obj, 'id', 'Unknown')})")
                    return True
                else:
                    logger.debug(f"❌ DEBUG: Ownership field '{field}' does not match current user")
                    logger.debug(f"   📊 Object owner: {owner_user.username if owner_user else 'None'}")
                    logger.debug(f"   👤 Current user: {request.user.username}")
        
        # 🚫 DEBUG: No ownership found or ownership doesn't match
        if not owner_found:
            if owner_field:
                logger.warning(f"🚫 DEBUG: IsOwner permission DENIED - ownership mismatch")
                logger.warning(f"❌ DEBUG: Object owned by '{owner_user.username if owner_user else 'None'}', requested by '{request.user.username}'")
                logger.debug(f"📊 DEBUG: Ownership field used: '{owner_field}'")
            else:
                logger.warning(f"🚫 DEBUG: IsOwner permission DENIED - no ownership field found")
                logger.warning(f"❌ DEBUG: Object type '{obj.__class__.__name__}' has no recognized ownership fields")
                logger.debug(f"📊 DEBUG: Checked fields: {ownership_fields}")
            
            logger.debug(f"👤 DEBUG: User: {request.user.username} (ID: {request.user.id})")
            logger.debug(f"📦 DEBUG: Object: {obj.__class__.__name__} (ID: {getattr(obj, 'id', 'Unknown')})")
            return False

class IsAdminOrOwner(permissions.BasePermission):
    """
    👑 ENHANCED ADMIN OR OWNER PERMISSION - WITH COMPREHENSIVE DEBUG TRACKING
    ========================================================================
    
    Custom permission that allows both admins and owners to modify objects.
    Provides detailed logging for all permission checks and validation decisions.
    
    FEATURES:
    - ✅ Admin override capability (staff users can access all objects)
    - ✅ Object ownership validation for non-admin users
    - ✅ Safe method allowance for read operations
    - ✅ Comprehensive debug logging for all decisions
    - ✅ Detailed error context for permission denials
    
    PERMISSION LOGIC:
    - 🔓 SAFE_METHODS (GET, HEAD, OPTIONS): Allowed for everyone
    - 🔒 WRITE_METHODS (POST, PUT, PATCH, DELETE): Admin or Owner only
    
    DEBUG ENHANCEMENTS:
    - 🔍 Permission check initiation tracking
    - 📊 Admin and ownership validation logging
    - 🛡️ Permission decision reasoning with detailed context
    - 📈 Access pattern monitoring and analytics
    - 🔄 Hierarchical permission checking
    """
    message = "You must be an admin or the owner of this object to perform this action."

    def has_object_permission(self, request, view, obj):
        """
        🔐 ENHANCED ADMIN OR OWNER PERMISSION CHECK WITH DEBUG TRACKING
        ==============================================================
        
        Check if the user is either an admin or the owner of the object.
        Provides detailed logging for all permission decisions.
        """
        # 📝 DEBUG: Log permission check initiation
        logger.debug(f"🔐 DEBUG: IsAdminOrOwner object permission check initiated")
        logger.debug(f"🌐 DEBUG: Request method: {request.method}")
        logger.debug(f"📍 DEBUG: Request path: {request.path}")
        logger.debug(f"👤 DEBUG: User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
        logger.debug(f"📦 DEBUG: Object type: {obj.__class__.__name__}")
        
        # 🔓 DEBUG: Check for safe methods (read operations)
        if request.method in permissions.SAFE_METHODS:
            logger.debug(f"🔓 DEBUG: Safe method detected: {request.method} - allowing access")
            logger.info(f"✅ DEBUG: IsAdminOrOwner permission GRANTED for safe method {request.method}")
            return True
        
        # Check authentication first
        if not request.user.is_authenticated:
            logger.warning(f"🚫 DEBUG: IsAdminOrOwner permission DENIED - user not authenticated")
            return False
        
        # 👑 DEBUG: Check for admin privileges first
        if request.user.is_staff:
            logger.info(f"✅ DEBUG: IsAdminOrOwner permission GRANTED - admin access")
            logger.debug(f"👑 DEBUG: Admin override activated for {request.method}")
            logger.debug(f"👤 DEBUG: Admin: {request.user.username} (ID: {request.user.id})")
            return True
        
        # 🔍 DEBUG: Check for ownership if not admin
        logger.debug(f"🔍 DEBUG: Not admin - checking ownership")
        ownership_fields = ['provider', 'customer', 'seller', 'owner', 'user']
        
        for field in ownership_fields:
            if hasattr(obj, field):
                owner_user = getattr(obj, field)
                logger.debug(f"🔍 DEBUG: Checking ownership field '{field}': {owner_user.username if owner_user else 'None'}")
                
                if owner_user == request.user:
                    logger.info(f"✅ DEBUG: IsAdminOrOwner permission GRANTED - owner access")
                    logger.debug(f"👑 DEBUG: Owner access granted via field '{field}'")
                    logger.debug(f"👤 DEBUG: Owner: {request.user.username} (ID: {request.user.id})")
                    return True
        
        # 🚫 DEBUG: Neither admin nor owner
        logger.warning(f"🚫 DEBUG: IsAdminOrOwner permission DENIED")
        logger.warning(f"❌ DEBUG: User is neither admin nor owner")
        logger.debug(f"👤 DEBUG: User: {request.user.username} (ID: {request.user.id})")
        logger.debug(f"📊 DEBUG: Admin status: {request.user.is_staff}")
        return False

# 🔍 DEBUG: Log module initialization completion
logger.info("✅ DEBUG: Services permissions module initialization completed")
logger.debug("🔐 DEBUG: Available permission classes:")
logger.debug("   🔧 IsServiceProvider - Provider-only write access")
logger.debug("   🛒 IsCustomer - Customer-only write access")
logger.debug("   👑 IsOwner - Owner-only write access")
logger.debug("   👑 IsAdminOrOwner - Admin or owner write access")
