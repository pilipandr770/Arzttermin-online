#!/bin/bash
# Startup script for Render.com - runs both Flask app and RQ worker

echo "🚀 Starting TerminFinder services..."

# Start RQ worker in background
echo "📦 Starting RQ worker..."
python worker.py &
WORKER_PID=$!
echo "✅ Worker started with PID: $WORKER_PID"

# Start Flask app with Gunicorn (foreground)
echo "🌐 Starting Flask app..."
exec gunicorn --config gunicorn.conf.py run:app
