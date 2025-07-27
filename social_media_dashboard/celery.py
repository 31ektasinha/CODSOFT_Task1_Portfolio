import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'social_media_dashboard.settings')

app = Celery('social_media_dashboard')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    'process-scheduled-posts': {
        'task': 'social_media.tasks.process_scheduled_posts',
        'schedule': 60.0,  # Run every minute
    },
    'sync-all-users-data': {
        'task': 'social_media.tasks.sync_all_users_data',
        'schedule': 3600.0,  # Run every hour
    },
    'update-social-media-metrics': {
        'task': 'social_media.tasks.update_social_media_metrics',
        'schedule': 86400.0,  # Run daily
    },
    'cleanup-old-activity-logs': {
        'task': 'social_media.tasks.cleanup_old_activity_logs',
        'schedule': 86400.0,  # Run daily
    },
    'retry-failed-scheduled-posts': {
        'task': 'social_media.tasks.retry_failed_scheduled_posts',
        'schedule': 1800.0,  # Run every 30 minutes
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')