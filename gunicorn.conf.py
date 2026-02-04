# Gunicorn configuration for TerminFinder
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:" + str(os.getenv('PORT', 8000))
backlog = 2048

# Worker processes - optimized for Render's free tier
workers = 2  # Fixed number for free tier
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 120  # Increased for OpenAI API calls (chatbot can take 30-60s)
keepalive = 5  # Increased keepalive for long connections

# Logging
loglevel = os.getenv('LOG_LEVEL', 'info')
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'terminfinder'

# Server mechanics
preload_app = True
pidfile = None  # Not needed on Render
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None

# Application
pythonpath = "/opt/render/project/src"

# Development vs Production
if os.getenv('FLASK_ENV') == 'development':
    reload = True
    workers = 1
    loglevel = 'debug'
else:
    reload = False