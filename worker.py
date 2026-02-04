"""
RQ Worker Startup Script
=========================

Run this script to start RQ workers for processing background tasks.

Usage:
    python worker.py

This will start workers for all queues:
- high: High priority tasks (notifications)
- default: Medium priority tasks (calendar sync)
- low: Low priority tasks (alerts, cleanup)
"""

import os
import sys
from redis import Redis
from rq import Worker, Queue, Connection

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

# Import app to ensure all models and services are loaded
from app import create_app

app = create_app()

# Redis connection
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis_conn = Redis.from_url(redis_url)

# Define queues to listen to
listen = ['high', 'default', 'low']

if __name__ == '__main__':
    with app.app_context():
        with Connection(redis_conn):
            worker = Worker(list(map(Queue, listen)))
            print(f"Starting RQ worker listening to queues: {listen}")
            print(f"Redis URL: {redis_url}")
            worker.work()
