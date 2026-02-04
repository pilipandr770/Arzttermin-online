# 🚀 Quick Start: Phase 1 Testing

## Step 1: Install Redis

### Option A: Docker (Recommended)
```powershell
# Pull and run Redis
docker run -d -p 6379:6379 --name terminfinder-redis redis:latest

# Check if running
docker ps
```

### Option B: Native Windows
1. Download Redis for Windows: https://github.com/tporadowski/redis/releases
2. Extract and run `redis-server.exe`

### Option C: WSL (Windows Subsystem for Linux)
```bash
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

---

## Step 2: Verify Redis Connection

```powershell
python test_worker.py
```

You should see:
```
✅ Redis connection successful!
✅ Queue created: test
✅ Job enqueued: job-id-here
```

---

## Step 3: Start RQ Worker

Open **NEW terminal** and run:
```powershell
python worker.py
```

Expected output:
```
Starting RQ worker listening to queues: ['high', 'default', 'low']
Redis URL: redis://localhost:6379/0
```

---

## Step 4: Test Full Integration

### 4.1 Start Flask App
In **third terminal**:
```powershell
python run.py
```

### 4.2 Create Test Booking (triggers email task)

Get JWT token first:
```powershell
# Login as patient
$response = Invoke-RestMethod -Uri "http://localhost:5000/api/patient/login" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"phone": "+380123456789", "password": "test123"}'

$token = $response.token
```

Create booking:
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/patient/book" `
  -Method POST `
  -Headers @{"Authorization" = "Bearer $token"} `
  -ContentType "application/json" `
  -Body '{"slot_id": "YOUR_SLOT_ID"}'
```

### 4.3 Check Worker Logs

Worker should show:
```
high: app.workers.notification_tasks.send_booking_confirmation_email('booking-uuid') (job-id)
Job OK (job-id)
Result is kept for 500 seconds
```

---

## Troubleshooting

### Redis connection refused
- ✅ Make sure Redis is running: `docker ps` or check `redis-server.exe` process
- ✅ Check port 6379 is not blocked by firewall
- ✅ Try: `telnet localhost 6379`

### Worker not processing jobs
- ✅ Check worker is running: Look for "Starting RQ worker..." message
- ✅ Verify queues: Worker listens to `high`, `default`, `low`
- ✅ Check Redis connection in worker logs

### Email tasks failing
- ✅ Check `MAIL_SERVER` and credentials in `.env`
- ✅ For testing, email failures are logged but don't crash worker
- ✅ Check worker logs for error details

---

## Production Deployment

See [PHASE1_ASYNC_WORKERS.md](PHASE1_ASYNC_WORKERS.md#production-deployment) for Render.com setup.

**Key points:**
1. Add Redis service on Render
2. Create separate Background Worker service
3. Set `REDIS_URL` environment variable
4. Scale workers based on queue length
