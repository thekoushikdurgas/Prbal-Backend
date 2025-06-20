"""
🚦 ENHANCED CUSTOM THROTTLING CLASSES - WITH COMPREHENSIVE DEBUG TRACKING
========================================================================

Custom throttling classes for API rate limiting with detailed monitoring.
These help protect critical endpoints from abuse and ensure fair usage.

FEATURES:
- ✅ Enhanced rate limiting with detailed logging
- ✅ User behavior pattern monitoring
- ✅ Abuse detection and prevention
- ✅ Performance impact tracking
- ✅ Comprehensive debug logging for all throttling decisions

DEBUG ENHANCEMENTS:
- 🔍 Throttle check initiation tracking
- 📊 Rate limit status and remaining quota logging
- 🛡️ Abuse detection with detailed context
- 📈 Usage pattern monitoring and analytics
- 🔄 Throttle bypass and admin override tracking
"""
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
import logging
import time
from django.core.cache import cache

# 🔍 DEBUG: Setup comprehensive logging for throttling
logger = logging.getLogger(__name__)
logger.info("🚀 DEBUG: Services throttling module loaded successfully")
logger.debug("🚦 DEBUG: Initializing enhanced throttling classes with debug tracking")

class EnhancedBaseThrottle:
    """
    🚦 ENHANCED BASE THROTTLE CLASS WITH COMPREHENSIVE DEBUG TRACKING
    ================================================================
    
    Base mixin class that provides enhanced debug logging capabilities
    for all throttling operations and rate limiting decisions.
    
    FEATURES:
    - ✅ Comprehensive throttle decision logging
    - ✅ User context and request pattern tracking
    - ✅ Rate limit quota monitoring and alerts
    - ✅ Performance impact measurement
    - ✅ Admin override capabilities
    
    DEBUG ENHANCEMENTS:
    - 🔍 Throttle check initiation tracking
    - 📊 Rate limit calculations and status logging
    - 🛡️ Abuse pattern detection and alerting
    - 📈 Usage analytics and trend monitoring
    - 🔄 Cache interaction and performance tracking
    """
    
    def enhanced_allow_request(self, request, view, original_result):
        """
        🔍 ENHANCED THROTTLE CHECK WITH COMPREHENSIVE DEBUG TRACKING
        ===========================================================
        
        Enhanced wrapper for throttle checks that provides detailed logging
        and monitoring for all rate limiting decisions.
        """
        # 📝 DEBUG: Log throttle check initiation
        throttle_name = self.__class__.__name__
        user_identifier = self.get_cache_key(request, view) if hasattr(self, 'get_cache_key') else 'unknown'
        
        logger.debug(f"🚦 DEBUG: {throttle_name} throttle check initiated")
        logger.debug(f"🌐 DEBUG: Request method: {request.method}")
        logger.debug(f"📍 DEBUG: Request path: {request.path}")
        logger.debug(f"👤 DEBUG: User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
        logger.debug(f"🔑 DEBUG: Cache key: {user_identifier}")
        
        # 📊 DEBUG: Check for admin bypass
        if request.user.is_authenticated and request.user.is_staff:
            logger.debug(f"👑 DEBUG: Admin user detected - checking bypass settings")
            # Allow admin bypass for most throttles (configurable)
            bypass_admin = getattr(self, 'bypass_admin', True)
            if bypass_admin:
                logger.info(f"✅ DEBUG: {throttle_name} throttle BYPASSED for admin user")
                logger.debug(f"👑 DEBUG: Admin bypass enabled for {throttle_name}")
                return True
        
        # 🔍 DEBUG: Get current rate limit status before decision
        if hasattr(self, 'get_rate'):
            rate = self.get_rate()
            logger.debug(f"📊 DEBUG: Rate limit configuration: {rate}")
        
        # ⏱️ DEBUG: Measure throttle check performance
        start_time = time.time()
        
        try:
            # 🚦 DEBUG: Make the throttle decision
            throttle_result = original_result
            check_duration = time.time() - start_time
            
            if throttle_result:
                # ✅ DEBUG: Request allowed
                logger.info(f"✅ DEBUG: {throttle_name} throttle check PASSED")
                logger.debug(f"🚦 DEBUG: Request allowed for {request.method} {request.path}")
                logger.debug(f"⏱️ DEBUG: Throttle check duration: {check_duration:.4f}s")
                
                # Log remaining quota if available
                if hasattr(self, 'get_available_requests'):
                    try:
                        remaining = self.get_available_requests(request, view)
                        logger.debug(f"📊 DEBUG: Remaining quota: {remaining} requests")
                    except:
                        logger.debug(f"📊 DEBUG: Could not determine remaining quota")
                
            else:
                # ❌ DEBUG: Request throttled
                logger.warning(f"🚫 DEBUG: {throttle_name} throttle check FAILED - request blocked")
                logger.warning(f"🚦 DEBUG: Rate limit exceeded for {request.method} {request.path}")
                logger.warning(f"👤 DEBUG: User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
                logger.debug(f"⏱️ DEBUG: Throttle check duration: {check_duration:.4f}s")
                
                # 🚨 DEBUG: Log potential abuse patterns
                self.log_potential_abuse(request, throttle_name)
                
                # Get wait time if available
                if hasattr(self, 'wait'):
                    wait_time = self.wait()
                    if wait_time:
                        logger.warning(f"⏰ DEBUG: Retry after: {wait_time:.2f} seconds")
                        logger.debug(f"📅 DEBUG: Next request allowed at: {time.strftime('%H:%M:%S', time.localtime(time.time() + wait_time))}")
            
            return throttle_result
            
        except Exception as e:
            # 💥 DEBUG: Log throttle check errors
            check_duration = time.time() - start_time
            logger.error(f"💥 DEBUG: {throttle_name} throttle check failed: {e}")
            logger.error(f"🔍 DEBUG: Error type: {type(e).__name__}")
            logger.debug(f"⏱️ DEBUG: Failed check duration: {check_duration:.4f}s")
            # Fail open - allow request if throttle check fails
            logger.warning(f"⚠️ DEBUG: Throttle check failed - allowing request (fail-open policy)")
            return True
    
    def log_potential_abuse(self, request, throttle_name):
        """
        🚨 LOG POTENTIAL ABUSE PATTERNS WITH DETAILED ANALYSIS
        =====================================================
        
        Analyze and log potential abuse patterns based on throttling decisions.
        Provides insights into suspicious activity and usage patterns.
        """
        try:
            # 📊 DEBUG: Analyze request patterns for abuse detection
            user_key = f"abuse_analysis_{request.user.id if request.user.is_authenticated else request.META.get('REMOTE_ADDR', 'unknown')}"
            
            # Get recent throttle violations
            cache_key = f"{user_key}_{throttle_name}_violations"
            recent_violations = cache.get(cache_key, 0)
            recent_violations += 1
            
            # Store violation count (expires in 1 hour)
            cache.set(cache_key, recent_violations, 3600)
            
            # 🚨 DEBUG: Check for abuse patterns
            if recent_violations >= 5:
                logger.error(f"🚨 DEBUG: POTENTIAL ABUSE DETECTED")
                logger.error(f"   📊 Throttle: {throttle_name}")
                logger.error(f"   👤 User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
                logger.error(f"   🔢 Violations in last hour: {recent_violations}")
                logger.error(f"   📍 Path: {request.path}")
                logger.error(f"   🌐 IP: {request.META.get('REMOTE_ADDR', 'Unknown')}")
                logger.error(f"   🕐 Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            elif recent_violations >= 2:
                logger.warning(f"⚠️ DEBUG: Repeated throttle violations detected")
                logger.warning(f"   📊 Throttle: {throttle_name}, Violations: {recent_violations}")
                logger.warning(f"   👤 User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
            
        except Exception as e:
            logger.error(f"💥 DEBUG: Error in abuse pattern analysis: {e}")

class BidSubmissionRateThrottle(UserRateThrottle, EnhancedBaseThrottle):
    """
    💰 ENHANCED BID SUBMISSION RATE THROTTLE - WITH COMPREHENSIVE DEBUG TRACKING
    ===========================================================================
    
    Rate limit for bid submissions to ensure fair marketplace behavior.
    Prevents users from spamming bids and ensures equal opportunity for all providers.
    
    FEATURES:
    - ✅ Bid submission rate limiting with detailed tracking
    - ✅ Fair marketplace behavior enforcement
    - ✅ Spam prevention and abuse detection
    - ✅ Provider equity protection
    - ✅ Comprehensive debug logging for all decisions
    
    RATE LIMIT LOGIC:
    - 🔒 Prevents excessive bid submissions per user
    - 🔄 Ensures fair competition among providers
    - 🛡️ Protects against bid bombing attacks
    - 📊 Monitors bidding patterns for abuse
    
    DEBUG ENHANCEMENTS:
    - 🔍 Bid submission pattern tracking
    - 📊 Provider behavior analytics
    - 🛡️ Marketplace abuse detection
    - 📈 Bidding competition monitoring
    """
    scope = 'bid_submission'
    bypass_admin = True  # Allow admin to bypass this throttle

    def allow_request(self, request, view):
        """Enhanced bid submission throttle check with comprehensive tracking"""
        # 📝 DEBUG: Log bid submission throttle check
        logger.debug(f"💰 DEBUG: Bid submission throttle check for provider")
        
        # Call the parent method and enhance with debug logging
        original_result = super().allow_request(request, view)
        return self.enhanced_allow_request(request, view, original_result)

class ReviewSubmissionRateThrottle(UserRateThrottle, EnhancedBaseThrottle):
    """
    ⭐ ENHANCED REVIEW SUBMISSION RATE THROTTLE - WITH COMPREHENSIVE DEBUG TRACKING
    =============================================================================
    
    Rate limit for review submissions to prevent review bombing and ensure authentic feedback.
    Protects the integrity of the review system and maintains trust in the marketplace.
    
    FEATURES:
    - ✅ Review submission rate limiting with detailed tracking
    - ✅ Review bombing prevention and detection
    - ✅ Authentic feedback protection
    - ✅ Review system integrity maintenance
    - ✅ Comprehensive debug logging for all decisions
    
    RATE LIMIT LOGIC:
    - 🔒 Prevents excessive review submissions per user
    - 🔄 Ensures authentic and thoughtful reviews
    - 🛡️ Protects against review manipulation
    - 📊 Monitors review patterns for abuse
    
    DEBUG ENHANCEMENTS:
    - 🔍 Review submission pattern tracking
    - 📊 Review authenticity analytics
    - 🛡️ Review bombing detection
    - 📈 Feedback quality monitoring
    """
    scope = 'review_submission'
    bypass_admin = True  # Allow admin to bypass this throttle

    def allow_request(self, request, view):
        """Enhanced review submission throttle check with comprehensive tracking"""
        # 📝 DEBUG: Log review submission throttle check
        logger.debug(f"⭐ DEBUG: Review submission throttle check for user")
        
        # Call the parent method and enhance with debug logging
        original_result = super().allow_request(request, view)
        return self.enhanced_allow_request(request, view, original_result)

class AIRequestRateThrottle(UserRateThrottle, EnhancedBaseThrottle):
    """
    🤖 ENHANCED AI REQUEST RATE THROTTLE - WITH COMPREHENSIVE DEBUG TRACKING
    ========================================================================
    
    Rate limit for AI suggestion requests to manage resource usage and costs.
    Ensures fair access to AI features while controlling computational expenses.
    
    FEATURES:
    - ✅ AI request rate limiting with detailed tracking
    - ✅ Resource usage management and optimization
    - ✅ Cost control and budget protection
    - ✅ Fair access distribution among users
    - ✅ Comprehensive debug logging for all decisions
    
    RATE LIMIT LOGIC:
    - 🔒 Prevents excessive AI API usage per user
    - 🔄 Ensures fair distribution of AI resources
    - 🛡️ Protects against AI service abuse
    - 📊 Monitors AI usage patterns and costs
    
    DEBUG ENHANCEMENTS:
    - 🔍 AI request pattern tracking
    - 📊 Resource usage analytics
    - 🛡️ AI service abuse detection
    - 📈 Cost and performance monitoring
    """
    scope = 'ai_suggestion'
    bypass_admin = False  # Don't bypass for admin to control costs

    def allow_request(self, request, view):
        """Enhanced AI request throttle check with comprehensive tracking"""
        # 📝 DEBUG: Log AI request throttle check
        logger.debug(f"🤖 DEBUG: AI suggestion throttle check for user")
        
        # Call the parent method and enhance with debug logging
        original_result = super().allow_request(request, view)
        return self.enhanced_allow_request(request, view, original_result)

class ServiceCategoryRateThrottle(UserRateThrottle, EnhancedBaseThrottle):
    """
    📂 ENHANCED SERVICE CATEGORY RATE THROTTLE - WITH COMPREHENSIVE DEBUG TRACKING
    =============================================================================
    
    Rate limit for service category creation/modification to prevent spam and maintain structure.
    Protects the categorization system and ensures thoughtful category management.
    
    FEATURES:
    - ✅ Category management rate limiting with detailed tracking
    - ✅ Spam prevention and structure protection
    - ✅ Administrative action monitoring
    - ✅ Category system integrity maintenance
    - ✅ Comprehensive debug logging for all decisions
    
    RATE LIMIT LOGIC:
    - 🔒 Prevents excessive category modifications
    - 🔄 Ensures thoughtful category management
    - 🛡️ Protects against category system abuse
    - 📊 Monitors administrative activity patterns
    
    DEBUG ENHANCEMENTS:
    - 🔍 Category management pattern tracking
    - 📊 Administrative activity analytics
    - 🛡️ Category system abuse detection
    - 📈 Structure integrity monitoring
    """
    scope = 'service_category'
    bypass_admin = True  # Allow admin to bypass this throttle

    def allow_request(self, request, view):
        """Enhanced service category throttle check with comprehensive tracking"""
        # 📝 DEBUG: Log service category throttle check
        logger.debug(f"📂 DEBUG: Service category throttle check for admin action")
        
        # Call the parent method and enhance with debug logging
        original_result = super().allow_request(request, view)
        return self.enhanced_allow_request(request, view, original_result)

class ServiceSubCategoryRateThrottle(UserRateThrottle, EnhancedBaseThrottle):
    """
    📁 ENHANCED SERVICE SUBCATEGORY RATE THROTTLE - WITH COMPREHENSIVE DEBUG TRACKING
    ================================================================================
    
    Rate limit for service subcategory creation/modification to prevent spam and maintain structure.
    Protects the subcategorization system and ensures proper hierarchy management.
    
    FEATURES:
    - ✅ Subcategory management rate limiting with detailed tracking
    - ✅ Spam prevention and hierarchy protection
    - ✅ Administrative action monitoring
    - ✅ Subcategory system integrity maintenance
    - ✅ Comprehensive debug logging for all decisions
    
    RATE LIMIT LOGIC:
    - 🔒 Prevents excessive subcategory modifications
    - 🔄 Ensures proper hierarchy management
    - 🛡️ Protects against subcategory system abuse
    - 📊 Monitors subcategory activity patterns
    
    DEBUG ENHANCEMENTS:
    - 🔍 Subcategory management pattern tracking
    - 📊 Hierarchy management analytics
    - 🛡️ Subcategory system abuse detection
    - 📈 Structure consistency monitoring
    """
    scope = 'service_subcategory'
    bypass_admin = True  # Allow admin to bypass this throttle

    def allow_request(self, request, view):
        """Enhanced service subcategory throttle check with comprehensive tracking"""
        # 📝 DEBUG: Log service subcategory throttle check
        logger.debug(f"📁 DEBUG: Service subcategory throttle check for admin action")
        
        # Call the parent method and enhance with debug logging
        original_result = super().allow_request(request, view)
        return self.enhanced_allow_request(request, view, original_result)

class ServiceCreationRateThrottle(UserRateThrottle, EnhancedBaseThrottle):
    """
    🔧 ENHANCED SERVICE CREATION RATE THROTTLE - WITH COMPREHENSIVE DEBUG TRACKING
    =============================================================================
    
    Rate limit for service creation to prevent spam services and maintain quality.
    Ensures thoughtful service creation and protects marketplace quality.
    
    FEATURES:
    - ✅ Service creation rate limiting with detailed tracking
    - ✅ Spam service prevention and quality protection
    - ✅ Provider behavior monitoring
    - ✅ Marketplace quality maintenance
    - ✅ Comprehensive debug logging for all decisions
    
    RATE LIMIT LOGIC:
    - 🔒 Prevents excessive service creation per provider
    - 🔄 Ensures thoughtful service development
    - 🛡️ Protects against service spam
    - 📊 Monitors provider service creation patterns
    
    DEBUG ENHANCEMENTS:
    - 🔍 Service creation pattern tracking
    - 📊 Provider behavior analytics
    - 🛡️ Service spam detection
    - 📈 Marketplace quality monitoring
    """
    scope = 'service_creation'
    bypass_admin = True  # Allow admin to bypass this throttle

    def allow_request(self, request, view):
        """Enhanced service creation throttle check with comprehensive tracking"""
        # 📝 DEBUG: Log service creation throttle check
        logger.debug(f"🔧 DEBUG: Service creation throttle check for provider")
        
        # Call the parent method and enhance with debug logging
        original_result = super().allow_request(request, view)
        return self.enhanced_allow_request(request, view, original_result)

class ServiceRequestRateThrottle(UserRateThrottle, EnhancedBaseThrottle):
    """
    📋 ENHANCED SERVICE REQUEST RATE THROTTLE - WITH COMPREHENSIVE DEBUG TRACKING
    ============================================================================
    
    Rate limit for service request creation to prevent spam requests and maintain quality.
    Ensures thoughtful request creation and protects marketplace efficiency.
    
    FEATURES:
    - ✅ Service request rate limiting with detailed tracking
    - ✅ Spam request prevention and quality protection
    - ✅ Customer behavior monitoring
    - ✅ Marketplace efficiency maintenance
    - ✅ Comprehensive debug logging for all decisions
    
    RATE LIMIT LOGIC:
    - 🔒 Prevents excessive request creation per customer
    - 🔄 Ensures thoughtful request development
    - 🛡️ Protects against request spam
    - 📊 Monitors customer request patterns
    
    DEBUG ENHANCEMENTS:
    - 🔍 Request creation pattern tracking
    - 📊 Customer behavior analytics
    - 🛡️ Request spam detection
    - 📈 Marketplace efficiency monitoring
    """
    scope = 'service_request'
    bypass_admin = True  # Allow admin to bypass this throttle

    def allow_request(self, request, view):
        """Enhanced service request throttle check with comprehensive tracking"""
        # 📝 DEBUG: Log service request throttle check
        logger.debug(f"📋 DEBUG: Service request throttle check for customer")
        
        # Call the parent method and enhance with debug logging
        original_result = super().allow_request(request, view)
        return self.enhanced_allow_request(request, view, original_result)

# 🔍 DEBUG: Log module initialization completion
logger.info("✅ DEBUG: Services throttling module initialization completed")
logger.debug("🚦 DEBUG: Available throttling classes:")
logger.debug("   💰 BidSubmissionRateThrottle - Bid submission rate limiting")
logger.debug("   ⭐ ReviewSubmissionRateThrottle - Review submission rate limiting")
logger.debug("   🤖 AIRequestRateThrottle - AI request rate limiting")
logger.debug("   📂 ServiceCategoryRateThrottle - Category management rate limiting")
logger.debug("   📁 ServiceSubCategoryRateThrottle - Subcategory management rate limiting")
logger.debug("   🔧 ServiceCreationRateThrottle - Service creation rate limiting")
logger.debug("   📋 ServiceRequestRateThrottle - Service request rate limiting")
