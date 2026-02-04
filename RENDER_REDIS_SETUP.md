# 🚀 Render Deployment - Single Service with Worker

## Варіант 1: Upstash Redis (Безкоштовний) ⭐ РЕКОМЕНДОВАНО

### Крок 1: Створити Upstash Redis
1. Перейти на https://upstash.com/
2. **Sign up** (можна через GitHub)
3. **Create Database**
   - Name: `terminfinder`
   - Region: **EU-West-1** (Dublin, ближче до ваших користувачів)
   - Type: **Global** (або Regional)
4. **Copy** → **Redis URL** (виглядає як `redis://default:password@eu1-xxx.upstash.io:6379`)

### Крок 2: Додати змінну на Render
1. Відкрийте ваш service: https://dashboard.render.com/web/srv-xxx
2. **Environment** → **Add Environment Variable**
3. Додайте:
   ```
   Key: REDIS_URL
   Value: redis://default:YOUR_PASSWORD@eu1-xxx.upstash.io:6379
   ```

### Крок 3: Commit і Push

Я вже створив `start.sh` що запускає і Flask і Worker в одному контейнері:

```bash
git add .
git commit -m "feat: Add worker to web service"
git push
```

Render автоматично deploy новий код! ✅

---

## Варіант 2: Redis Cloud (від RedisLabs) 

### Безкоштовний tier (30MB):
1. https://redis.com/try-free/
2. Sign up → Create database
3. Copy **Public endpoint**
4. На Render додати:
   ```
   REDIS_URL = redis://default:password@redis-12345.c123.us-east-1-1.ec2.cloud.redislabs.com:12345
   ```

---

## Варіант 3: Render Redis (Платний - $7/місяць)

Якщо хочете все в одному місці:
1. Render Dashboard → **New** → **Redis**
2. Plan: Starter ($7/mo, 256MB)
3. Copy Internal Redis URL
4. Додати змінну `REDIS_URL`

---

## Що відбувається після deploy?

`start.sh` запускає:
1. **Worker** у фоні → обробляє email, calendar, chatbot tasks
2. **Gunicorn** на передньому плані → обслуговує HTTP запити

В логах Render ви побачите:
```
📦 Starting RQ worker...
✅ Worker started with PID: 123
🌐 Starting Flask app...
Starting RQ worker listening to queues: ['high', 'default', 'low']
[2026-02-04 10:00:00] [INFO] Starting gunicorn 21.2.0
```

---

## ✅ Що робити ЗАРАЗ:

1. **Створити Upstash Redis** (5 хвилин, безкоштовно)
2. **Скопіювати Redis URL**
3. **Додати змінну `REDIS_URL`** на Render
4. **Я зроблю commit і push** ← скажіть коли готові!

Який варіант обираєте? **Upstash** найшвидший для старту! 🚀
