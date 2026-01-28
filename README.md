# TerminFinder MVP

**AI-ассистент для записи на прием к врачам в Германии**

Умная система бронирования терминов с автоматическими уведомлениями, Stripe платежами и защитой от no-show.

---

## 🏗️ Архитектура

### Backend (Flask)
- **API**: RESTful API с JWT authentication
- **Database**: PostgreSQL с SQLAlchemy ORM
- **Payments**: Stripe для депозитов и возвратов
- **Tasks**: Celery + Redis для background jobs
- **Email**: Flask-Mail для уведомлений

### Основные сущности
1. **Practice** (Praxis) - Медицинская практика
2. **Doctor** (Arzt) - Врач
3. **Calendar** - Календарь с рабочими часами
4. **TimeSlot** - Временной слот для бронирования
5. **Patient** - Пациент (только email)
6. **PatientAlert** - "Будильник" для уведомлений о свободных слотах
7. **Booking** - Бронирование с оплатой

---

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt
```

### 2. Настройка PostgreSQL

```bash
# Установить PostgreSQL (если еще не установлен)
# Ubuntu/Debian:
sudo apt-get install postgresql postgresql-contrib

# Создать базу данных
sudo -u postgres psql
CREATE DATABASE terminfinder;
CREATE USER terminfinder_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE terminfinder TO terminfinder_user;
\q
```

### 3. Настройка Redis

```bash
# Установить Redis
sudo apt-get install redis-server

# Запустить Redis
redis-server
```

### 4. Конфигурация

```bash
# Скопировать example config
cp .env.example .env

# Отредактировать .env
nano .env
```

**Важно!** Замените в `.env`:
- `SECRET_KEY` - случайная строка
- `DATABASE_URL` - ваши credentials PostgreSQL
- `STRIPE_SECRET_KEY` - ваш Stripe test key
- `MAIL_USERNAME` и `MAIL_PASSWORD` - для email

### 5. Инициализация БД

```bash
# Создать таблицы
flask db upgrade

# Или если миграции еще нет:
flask init-db

# Заполнить тестовыми данными (опционально)
flask seed-db
```

### 6. Запуск приложения

```bash
# Запуск Flask (Development)
python run.py

# Или через flask CLI
flask run

# API доступен на: http://localhost:5000
```

### 7. Запуск Celery (для background tasks)

```bash
# В отдельном терминале
celery -A app.celery worker --loglevel=info

# Для периодических задач (reminders, cleanup)
celery -A app.celery beat --loglevel=info
```

---

## 📁 Структура проекта

```
terminfinder-mvp/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── constants.py          # Специальности, языки и т.д.
│   ├── models/               # SQLAlchemy модели
│   │   ├── practice.py       # Practice (Praxis)
│   │   ├── doctor.py         # Doctor
│   │   ├── calendar.py       # Calendar, TimeSlot
│   │   ├── patient.py        # Patient, PatientAlert
│   │   └── booking.py        # Booking
│   ├── routes/               # API endpoints
│   │   ├── auth.py           # Регистрация/логин
│   │   ├── practice.py       # Practice management
│   │   ├── doctor.py         # Doctor CRUD
│   │   ├── patient.py        # Patient operations
│   │   ├── booking.py        # Booking flow
│   │   └── search.py         # Поиск врачей
│   ├── services/             # Бизнес-логика
│   │   ├── stripe_service.py # Stripe integration
│   │   ├── email_service.py  # Email отправка
│   │   ├── vat_service.py    # VAT verification
│   │   └── rate_limiter.py   # Anti-spam
│   ├── utils/                # Helpers
│   ├── tasks.py              # Celery tasks
│   ├── templates/            # Email templates
│   └── static/               # Static files
├── migrations/               # Alembic migrations
├── config.py                 # Конфигурация
├── run.py                    # Entry point
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # This file
```

---

## 🔑 API Endpoints (основные)

### Authentication
```
POST /api/auth/register/patient     # Регистрация пациента
POST /api/auth/register/practice    # Регистрация практики
POST /api/auth/login                 # Логин
POST /api/auth/verify-email          # Подтверждение email
```

### Search
```
GET  /api/search/doctors             # Поиск врачей
GET  /api/search/available-slots     # Поиск свободных слотов
```

### Booking
```
POST /api/bookings/                  # Создать бронь
GET  /api/bookings/<code>            # Получить бронь
POST /api/bookings/<code>/cancel     # Отменить бронь
GET  /api/bookings/my-bookings       # Мои брони
```

### Practice Management
```
GET  /api/practice/dashboard         # Dashboard практики
POST /api/doctors/                   # Добавить врача
PUT  /api/doctors/<id>/calendar      # Обновить календарь
GET  /api/doctors/<id>/slots         # Слоты врача
```

### Patient
```
POST /api/patient/alerts             # Создать терминный alert
GET  /api/patient/alerts             # Мои alerts
```

---

## 🔧 Основные фичи MVP

### ✅ Реализовано в коде:

1. **Practice Registration**
   - VAT verification через EU VIES API
   - Email подтверждение
   - Multi-doctor support

2. **Doctor Management**
   - 20+ специальностей + custom
   - Multi-language support
   - Flexible календари

3. **Smart Slot Management**
   - Автогенерация слотов
   - Ручное блокирование (обед, meeting)
   - Race condition protection

4. **Booking Flow**
   - Stripe payment (€10 депозит)
   - Atomic booking (SELECT FOR UPDATE)
   - Automatic refund policy:
     - >24h: 100% refund
     - 1-24h: 50% refund
     - <1h: no refund

5. **Patient Alerts**
   - Search criteria (city, speciality, language)
   - Auto-notification на свободные слоты
   - Cooldown между уведомлениями

6. **Reputation System**
   - No-show tracking
   - Cancellation rate
   - Booking restrictions для bad actors

7. **Email Notifications**
   - Booking confirmation
   - 24h reminder
   - Cancellation confirmation
   - Practice-initiated cancellation

### 🚧 TODO для полного MVP:

- [ ] Frontend (React)
- [ ] Полная реализация всех routes
- [ ] Celery tasks (reminders, cleanup)
- [ ] Admin панель
- [ ] Unit tests
- [ ] Docker setup
- [ ] Deployment guide

---

## 💳 Stripe Integration

### Test Mode
Используй Stripe test keys для разработки:
```
Card: 4242 4242 4242 4242
Exp: любая будущая дата
CVC: любые 3 цифры
```

### Webhooks
Для локальной разработки используй Stripe CLI:
```bash
stripe listen --forward-to localhost:5000/api/webhooks/stripe
```

---

## 📧 Email Configuration

### Development (Console)
В development mode emails выводятся в консоль.

### Production
Рекомендуется использовать:
- **Mailgun** (хороший free tier)
- **SendGrid**
- **AWS SES**

Настрой в `.env`:
```
MAIL_SERVER=smtp.mailgun.org
MAIL_USERNAME=postmaster@your-domain.com
MAIL_PASSWORD=your-password
```

---

## 🔒 Security Best Practices

1. **Never commit .env** - уже в .gitignore
2. **Use strong SECRET_KEY** - генерируй через `python -c "import secrets; print(secrets.token_hex(32))"`
3. **HTTPS в production** - обязательно!
4. **Rate limiting** - реализовано через RateLimiter
5. **SQL Injection** - защита через SQLAlchemy ORM
6. **CSRF** - не нужно для API (используем JWT)

---

## 🐛 Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'app'"
**Solution**: Убедись что запускаешь из корневой папки проекта

### Problem: "Connection refused" при подключении к PostgreSQL
**Solution**: Проверь что PostgreSQL запущен: `sudo service postgresql status`

### Problem: Celery не запускается
**Solution**: Проверь что Redis запущен: `redis-cli ping` (должен вернуть "PONG")

### Problem: Stripe webhooks не работают локально
**Solution**: Используй Stripe CLI для forwarding

---

## 📚 Дополнительные ресурсы

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Stripe API](https://stripe.com/docs/api)
- [Celery Guide](https://docs.celeryproject.org/)

---

## 👨‍💻 Development

### Создание миграций
```bash
flask db migrate -m "Description of changes"
flask db upgrade
```

### Flask Shell
```bash
flask shell
>>> from app.models import Practice, Doctor
>>> Practice.query.all()
```

### Тестирование
```bash
pytest
```

---

## 📄 License

MIT License - см. LICENSE file

---

## 🤝 Contributing

Pull requests welcome! Для больших изменений сначала создай issue.

---

**Built with ❤️ for German healthcare**
