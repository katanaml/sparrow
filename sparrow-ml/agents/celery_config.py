"""
Celery configuration for Sparrow Agents
"""
from celery import Celery
import os

# Redis connection URL from environment or default
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Initialize Celery app
celery_app = Celery(
    'sparrow_agents',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['tasks']  # Import tasks module
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    result_expires=3600,  # Results expire after 1 hour
    task_track_started=True,  # Track when tasks start
    task_time_limit=3600,  # Hard time limit (1 hour)
    task_soft_time_limit=3300,  # Soft time limit (55 minutes)
    worker_prefetch_multiplier=1,  # Fetch one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
)

# Optional: Configure task routes
celery_app.conf.task_routes = {
    'tasks.process_data_agent': {'queue': 'data_queue'},
    'tasks.process_file_agent': {'queue': 'file_queue'},
}