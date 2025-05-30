"""
Custom throttling classes for API rate limiting.
These help protect critical endpoints from abuse and ensure fair usage.
"""
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """Rate limit for login attempts to prevent brute force attacks."""
    scope = 'login'


class RegisterRateThrottle(AnonRateThrottle):
    """Rate limit for registration to prevent spam accounts."""
    scope = 'register'


class BidSubmissionRateThrottle(UserRateThrottle):
    """Rate limit for bid submissions to ensure fair marketplace behavior."""
    scope = 'bid_submission'


class ReviewSubmissionRateThrottle(UserRateThrottle):
    """Rate limit for review submissions to prevent review bombing."""
    scope = 'review_submission'


class AIRequestRateThrottle(UserRateThrottle):
    """Rate limit for AI suggestion requests to manage resource usage."""
    scope = 'ai_suggestion'
