"""
Background Workers for TerminFinder
====================================

This module contains RQ workers for handling blocking I/O operations asynchronously.

Workers:
- notification_tasks: Email and SMS notifications
- calendar_tasks: Calendar synchronization with Google/Outlook/Apple
- chatbot_tasks: AI chatbot message processing

Usage:
    from app.workers import notification_tasks
    from rq import Queue
    from redis import Redis
    
    redis_conn = Redis.from_url('redis://localhost:6379')
    queue = Queue('default', connection=redis_conn)
    
    # Enqueue task
    job = queue.enqueue(notification_tasks.send_booking_confirmation, patient_id=123)
"""

from redis import Redis
from rq import Queue
import os
import ssl

# Redis connection with SSL support for Upstash
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Initialize Redis connection
redis_conn = None
default_queue = None
high_priority_queue = None
low_priority_queue = None

try:
    # SSL configuration for rediss:// URLs (Upstash)
    if redis_url.startswith('rediss://'):
        redis_conn = Redis.from_url(
            redis_url,
            ssl_cert_reqs=None,  # Disable certificate verification for Upstash
            decode_responses=False
        )
    else:
        # Local Redis (without SSL)
        redis_conn = Redis.from_url(
            redis_url,
            decode_responses=False,
            socket_connect_timeout=5
        )
    
    # Test connection
    redis_conn.ping()
    
    # Queues
    default_queue = Queue('default', connection=redis_conn)
    high_priority_queue = Queue('high', connection=redis_conn)
    low_priority_queue = Queue('low', connection=redis_conn)
    
    print(f"✅ Redis connected: {redis_url.split('@')[0] if '@' in redis_url else redis_url}")
    
except Exception as e:
    print(f"⚠️ Redis connection failed: {e}")
    print(f"⚠️ Background workers disabled. Tasks will run synchronously.")
    redis_conn = None
    default_queue = None
    high_priority_queue = None
    low_priority_queue = None

__all__ = ['redis_conn', 'default_queue', 'high_priority_queue', 'low_priority_queue']
