"""
Performance monitoring middleware for the Prbal backend.
Tracks API response times and sends metrics to monitoring systems.
"""
import time
import logging
import json
from django.conf import settings

# Configure logger
logger = logging.getLogger('api.performance')

class PerformanceMonitoringMiddleware:
    """
    Middleware to track API response times and log performance metrics.
    Can be extended to send metrics to StatsD, Prometheus, or other monitoring systems.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Skip non-API requests to avoid unnecessary overhead
        if not request.path.startswith('/api/'):
            return self.get_response(request)
            
        # Start timer
        start_time = time.time()
        
        # Process request
        response = self.get_response(request)
        
        # End timer
        duration_ms = (time.time() - start_time) * 1000
        
        # Gather metrics
        path = request.path
        method = request.method
        status_code = response.status_code
        user_id = request.user.id if request.user.is_authenticated else None
        
        # Log performance data
        perf_data = {
            'path': path,
            'method': method,
            'status_code': status_code,
            'duration_ms': round(duration_ms, 2),
            'user_id': user_id,
        }
        
        # Add response size if available
        if hasattr(response, 'content'):
            perf_data['response_size'] = len(response.content)
            
        # Log to structured logger
        logger.info('API Request', extra=perf_data)
        
        # Add timing header to response
        response['X-Response-Time'] = f"{duration_ms:.2f}ms"
        
        # In development, add timing to response for easier debugging
        if settings.DEBUG and 'application/json' in response.get('Content-Type', ''):
            try:
                content = json.loads(response.content.decode('utf-8'))
                if isinstance(content, dict):
                    content['_debug'] = {'response_time_ms': round(duration_ms, 2)}
                    response.content = json.dumps(content).encode('utf-8')
            except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                pass
                
        return response
