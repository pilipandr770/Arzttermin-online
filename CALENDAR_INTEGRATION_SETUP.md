# Настройка Интеграций Календарей - Setup Guide

## Быстрый Старт

Эта интеграция полностью реализована и готова к использованию. Следуйте этим шагам для настройки.

---

## 1. Установка Зависимостей

```bash
pip install -r requirements.txt
```

Это установит:
- `google-auth`, `google-auth-oauthlib`, `google-api-python-client` (Google Calendar)
- `caldav`, `icalendar` (Apple Calendar / CalDAV)
- `msal` (Microsoft Outlook/Office 365)
- `cryptography` (для шифрования токенов)

---

## 2. Применение Миграции Базы Данных

```bash
# Создать миграцию
python -m flask db migrate -m "Add calendar integrations support"

# Применить миграцию
python -m flask db upgrade
```

Это создаст таблицу `terminfinder.calendar_integrations`.

---

## 3. Настройка Environment Variables

Добавьте в `.env` файл:

```bash
# Ключ для шифрования токенов календарей
# Сгенерировать: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
CALENDAR_ENCRYPTION_KEY=your-generated-fernet-key-here

# Google Calendar OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://your-domain.com/api/doctor/calendar-integrations/callback/google

# Microsoft Outlook/Office 365 OAuth
MICROSOFT_CLIENT_ID=your-microsoft-app-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
MICROSOFT_REDIRECT_URI=https://your-domain.com/api/doctor/calendar-integrations/callback/outlook
```

---

## 4. Настройка Google Calendar API

### Шаг 1: Создать проект в Google Cloud Console

1. Перейдите на https://console.cloud.google.com/
2. Создайте новый проект или выберите существующий
3. Перейдите в "APIs & Services" > "Library"
4. Найдите и включите "Google Calendar API"

### Шаг 2: Создать OAuth 2.0 Credentials

1. Перейдите в "APIs & Services" > "Credentials"
2. Нажмите "Create Credentials" > "OAuth client ID"
3. Выберите "Web application"
4. Добавьте Authorized redirect URI:
   ```
   https://your-domain.com/api/doctor/calendar-integrations/callback/google
   http://localhost:5000/api/doctor/calendar-integrations/callback/google (для разработки)
   ```
5. Сохраните Client ID и Client Secret в `.env`

### Шаг 3: Настроить OAuth Consent Screen

1. "APIs & Services" > "OAuth consent screen"
2. Выберите "External" (для публичного использования)
3. Заполните необходимую информацию
4. Добавьте scope: `https://www.googleapis.com/auth/calendar.events`

### Квоты Google Calendar API

- **Бесплатно**: 1,000,000 запросов/день
- **Достаточно** для большинства медицинских практик

---

## 5. Настройка Microsoft Outlook/Office 365

### Шаг 1: Зарегистрировать приложение в Azure

1. Перейдите на https://portal.azure.com/
2. Перейдите в "Azure Active Directory" > "App registrations"
3. Нажмите "New registration"
4. Заполните:
   - Name: "TerminFinder Calendar Integration"
   - Supported account types: "Accounts in any organizational directory and personal Microsoft accounts"
   - Redirect URI: `https://your-domain.com/api/doctor/calendar-integrations/callback/outlook`

### Шаг 2: Настроить API Permissions

1. В вашем приложении перейдите в "API permissions"
2. Нажмите "Add a permission" > "Microsoft Graph"
3. Выберите "Delegated permissions"
4. Добавьте: `Calendars.ReadWrite`
5. Нажмите "Grant admin consent" (если у вас есть права)

### Шаг 3: Создать Client Secret

1. Перейдите в "Certificates & secrets"
2. Нажмите "New client secret"
3. Сохраните значение secret в `.env`

### Квоты Microsoft Graph API

- **Бесплатно**: 10,000 запросов/10 минут на приложение
- **Достаточно** для медицинских практик

---

## 6. Apple Calendar / iCloud - НЕ ТРЕБУЕТ НАСТРОЙКИ

Apple Calendar использует стандартный CalDAV протокол.

**Требования от пользователя:**
- Apple ID
- App-specific password (генерируется на https://appleid.apple.com/)

**Инструкция для врачей:**
1. Перейти на https://appleid.apple.com/
2. Security > App-Specific Passwords
3. Сгенерировать пароль для "TerminFinder"
4. Использовать этот пароль при подключении

---

## 7. Генерация Encryption Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Скопируйте вывод в `.env` как `CALENDAR_ENCRYPTION_KEY`.

**ВАЖНО**: Этот ключ шифрует OAuth токены и пароли в базе данных. 
**Не теряйте его** - без него невозможно расшифровать сохраненные токены!

---

## 8. Тестирование

### Локальная разработка

1. Запустите приложение:
   ```bash
   python run.py
   ```

2. Откройте в браузере:
   ```
   http://localhost:5000/doctor/calendar-integrations
   ```

3. Для тестирования OAuth используйте ngrok или аналогичный сервис:
   ```bash
   ngrok http 5000
   ```
   
   Обновите redirect URIs в Google Cloud Console и Azure на ngrok URL.

### Тестирование Google Calendar

1. Нажмите "Mit Google verbinden"
2. Пройдите OAuth flow
3. После успешного подключения попробуйте "Jetzt synchronisieren"

### Тестирование Apple Calendar

1. Создайте app-specific password на https://appleid.apple.com/
2. Нажмите "Mit iCloud verbinden"
3. Введите Apple ID и app-specific password
4. CalDAV URL: `https://caldav.icloud.com`

### Тестирование Outlook

1. Нажмите "Mit Outlook verbinden"
2. Войдите с Microsoft аккаунтом
3. Дайте разрешения
4. После успешного подключения попробуйте синхронизацию

---

## 9. Production Deployment

### Важные моменты:

1. **HTTPS обязателен** для OAuth callbacks
2. **Настройте webhook endpoints** для real-time синхронизации:
   - Google: `/webhooks/calendar/google`
   - Outlook: `/webhooks/calendar/outlook`
3. **Настройте Celery** для периодической синхронизации
4. **Backup encryption key** надежно

### Celery Tasks для Background Sync

Добавьте в `tasks.py`:

```python
from celery import Celery
from celery.schedules import crontab
from app.models.calendar_integration import CalendarIntegration
from app.services.calendar_integration_service import get_calendar_service

celery = Celery('tasks')

@celery.task
def sync_all_calendar_integrations():
    """Синхронизация всех активных интеграций"""
    integrations = CalendarIntegration.query.filter_by(
        sync_enabled=True,
        sync_status='active'
    ).all()
    
    for integration in integrations:
        try:
            service = get_calendar_service(integration)
            service.sync_from_external()
        except Exception as e:
            print(f"Sync error for {integration.id}: {e}")

# Запускать каждые 10 минут
celery.conf.beat_schedule = {
    'sync-calendars': {
        'task': 'tasks.sync_all_calendar_integrations',
        'schedule': crontab(minute='*/10'),
    },
}
```

Запуск Celery:

```bash
# Worker
celery -A tasks worker --loglevel=info

# Beat (scheduler)
celery -A tasks beat --loglevel=info
```

---

## 10. Мониторинг и Обслуживание

### Google Webhooks обновление

Google webhooks истекают через 7 дней. Настройте Celery task для обновления:

```python
@celery.task
def renew_google_webhooks():
    """Google webhooks истекают через 7 дней - обновляем"""
    integrations = CalendarIntegration.query.filter_by(
        provider='google',
        sync_enabled=True
    ).all()
    
    for integration in integrations:
        try:
            service = GoogleCalendarService(integration)
            callback_url = f"{os.getenv('BASE_URL')}/webhooks/calendar/google"
            service.renew_webhook(callback_url)
        except Exception as e:
            print(f"Webhook renewal error: {e}")

# Запускать ежедневно
celery.conf.beat_schedule['renew-google-webhooks'] = {
    'task': 'tasks.renew_google_webhooks',
    'schedule': crontab(hour=0, minute=0),
}
```

### Outlook Webhooks обновление

Outlook webhooks истекают через 3 дня:

```python
@celery.task
def renew_outlook_webhooks():
    """Outlook webhooks истекают через 3 дня - обновляем"""
    integrations = CalendarIntegration.query.filter_by(
        provider='outlook',
        sync_enabled=True
    ).all()
    
    for integration in integrations:
        try:
            service = OutlookCalendarService(integration)
            service.renew_webhook()
        except Exception as e:
            print(f"Webhook renewal error: {e}")

celery.conf.beat_schedule['renew-outlook-webhooks'] = {
    'task': 'tasks.renew_outlook_webhooks',
    'schedule': crontab(hour='*/12'),  # Каждые 12 часов
}
```

---

## 11. Troubleshooting

### Проблема: OAuth callback не работает

**Решение:**
- Проверьте redirect URI в Google Cloud Console / Azure
- Убедитесь что используется HTTPS в production
- Проверьте что blueprint зарегистрирован в app/__init__.py

### Проблема: Токены не расшифровываются

**Решение:**
- Проверьте что `CALENDAR_ENCRYPTION_KEY` установлен в .env
- Убедитесь что ключ не изменился после сохранения токенов
- Если ключ потерян - попросите врачей переподключить календари

### Проблема: CalDAV не подключается (Apple)

**Решение:**
- Убедитесь что используется app-specific password, а не основной пароль Apple ID
- Проверьте правильность URL: `https://caldav.icloud.com`
- Проверьте двухфакторную аутентификацию на Apple ID

### Проблема: Синхронизация не работает

**Решение:**
- Проверьте логи Celery
- Убедитесь что Celery worker и beat запущены
- Проверьте что `sync_enabled=True` для интеграции
- Проверьте квоты API (Google, Microsoft)

---

## 12. Security Best Practices

1. **Всегда используйте HTTPS** для OAuth callbacks
2. **Backup encryption key** в безопасном месте
3. **Rotate client secrets** периодически
4. **Мониторинг API usage** для выявления аномалий
5. **Rate limiting** для API endpoints
6. **Логирование** всех операций с календарями

---

## 13. Что дальше?

### Возможные улучшения:

1. **Автоматическое создание событий** при бронировании (уже реализовано в коде)
2. **Уведомления** врачам о конфликтах календарей
3. **Статистика синхронизации** в dashboard
4. **Поддержка нескольких календарей** (работа + личный)
5. **Выборочная синхронизация** по типам событий
6. **SMS/Email уведомления** при изменениях
7. **Bidirectional sync улучшения** - обновление в TerminFinder при изменении во внешнем календаре

---

## Поддержка

Для вопросов и помощи смотрите полную документацию в [CALENDAR_INTEGRATION.md](CALENDAR_INTEGRATION.md).

**Готово к использованию! 🚀**
