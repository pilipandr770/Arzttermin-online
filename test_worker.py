"""
Test RQ Worker Setup
====================

Tests basic RQ functionality without requiring full app context.
"""

from redis import Redis
from rq import Queue
import time
import os

# Test function
def test_task(message):
    """Simple test task"""
    print(f"Processing: {message}")
    time.sleep(2)  # Simulate work
    return f"Completed: {message}"


def main():
    # Connect to Redis
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    print(f"Connecting to Redis: {redis_url}")
    
    try:
        redis_conn = Redis.from_url(redis_url)
        redis_conn.ping()
        print("✅ Redis connection successful!")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("\n💡 Make sure Redis is running:")
        print("   Windows: Download from https://github.com/microsoftarchive/redis/releases")
        print("   Or use Docker: docker run -d -p 6379:6379 redis:latest")
        return
    
    # Create queue
    queue = Queue('test', connection=redis_conn)
    print(f"✅ Queue created: {queue.name}")
    
    # Enqueue test task
    print("\nEnqueuing test task...")
    job = queue.enqueue(test_task, "Hello from TerminFinder!")
    print(f"✅ Job enqueued: {job.id}")
    print(f"   Status: {job.get_status()}")
    
    # Check queue status
    print(f"\n📊 Queue status:")
    print(f"   Jobs in queue: {len(queue)}")
    print(f"   Job ID: {job.id}")
    
    print("\n" + "="*50)
    print("🚀 To process this job, run in another terminal:")
    print("   python worker.py")
    print("="*50)
    
    # Wait and check result (if worker is running)
    print("\nWaiting for worker to process job (10 seconds)...")
    for i in range(10):
        job.refresh()
        status = job.get_status()
        print(f"   {i+1}s - Status: {status}")
        
        if status == 'finished':
            print(f"\n✅ Job completed!")
            print(f"   Result: {job.result}")
            break
        elif status == 'failed':
            print(f"\n❌ Job failed!")
            print(f"   Error: {job.exc_info}")
            break
        
        time.sleep(1)
    else:
        print("\n⏳ Job still pending. Worker may not be running.")
        print("   Start worker with: python worker.py")


if __name__ == '__main__':
    main()
