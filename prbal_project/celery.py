"""
Celery configuration for Prbal backend.
Handles asynchronous task processing for operations like
payment processing, email notifications, and AI suggestions.
"""
import os
from celery import Celery
from celery.signals import task_failure
import logging

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prbal_project.settings')

app = Celery('prbal_project')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Configure Celery for production
app.conf.broker_transport_options = {
    'visibility_timeout': 3600,  # 1 hour
    'max_retries': 3,
}

# Task execution settings
app.conf.task_acks_late = True  # Ensure task is acknowledged only after execution
app.conf.worker_prefetch_multiplier = 1  # Fetch one task at a time
app.conf.task_time_limit = 1800  # 30 minutes max runtime
app.conf.task_soft_time_limit = 1500  # 25 minutes soft limit with graceful timeout

# Default queue settings
app.conf.task_default_queue = 'default'
app.conf.task_queues = {
    'default': {},
    'high_priority': {},
    'payments': {},
    'notifications': {},
    'ai_suggestions': {},
    'verification': {},
}

# Route tasks to specific queues based on their name
app.conf.task_routes = {
    'payments.*': {'queue': 'payments'},
    'notifications.*': {'queue': 'notifications'},
    'ai_suggestions.*': {'queue': 'ai_suggestions'},
    'verification.*': {'queue': 'verification'},
}

# Serialization
app.conf.accept_content = ['json']
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'

# Error handling
logger = logging.getLogger('celery')

@task_failure.connect
def handle_task_failure(task_id, exception, args, kwargs, traceback, einfo, **kw):
    """Handle and log task failures."""
    logger.error(
        f"Task failed: {task_id}, args: {args}, kwargs: {kwargs}, exception: {exception}",
        exc_info=(type(exception), exception, traceback)
    )
    
    # Optional: Integrate with Sentry for error tracking
    try:
        from sentry_sdk import capture_exception
        capture_exception(exception)
    except ImportError:
        pass


@app.task(bind=True)
def debug_task(self):
    """Test task to verify Celery is working."""
    print(f'Request: {self.request!r}')
    return "Celery is working!"
