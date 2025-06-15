"""
Custom throttling classes for API rate limiting.
These help protect critical endpoints from abuse and ensure fair usage.
"""
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class BidSubmissionRateThrottle(UserRateThrottle):
    """Rate limit for bid submissions to ensure fair marketplace behavior."""
    scope = 'bid_submission'


class ReviewSubmissionRateThrottle(UserRateThrottle):
    """Rate limit for review submissions to prevent review bombing."""
    scope = 'review_submission'


class AIRequestRateThrottle(UserRateThrottle):
    """Rate limit for AI suggestion requests to manage resource usage."""
    scope = 'ai_suggestion'


class ServiceCategoryRateThrottle(UserRateThrottle):
    """Rate limit for service category creation/modification to prevent spam."""
    scope = 'service_category'


class ServiceSubCategoryRateThrottle(UserRateThrottle):
    """Rate limit for service subcategory creation/modification to prevent spam."""
    scope = 'service_subcategory'


class ServiceCreationRateThrottle(UserRateThrottle):
    """Rate limit for service creation to prevent spam services."""
    scope = 'service_creation'


class ServiceRequestRateThrottle(UserRateThrottle):
    """Rate limit for service request creation to prevent spam requests."""
    scope = 'service_request'
