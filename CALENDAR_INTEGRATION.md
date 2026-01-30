# Интеграция Внешних Календарей в TerminFinder

## Обзор

Для успешной интеграции в действующие праксисы необходимо обеспечить синхронизацию с популярными календарными системами. Это позволит врачам продолжать использовать привычные инструменты, в то время как TerminFinder автоматически управляет доступностью слотов.

## Основная Концепция

### Двунаправленная Синхронизация

1. **TerminFinder → Внешний Календарь**: 
   - Автоматическое создание событий во внешнем календаре при подтверждении бронирования
   - Обновление событий при изменении или отмене

2. **Внешний Календарь → TerminFinder**:
   - Синхронизация занятых слотов (блокировка в TerminFinder)
   - Периодический опрос (polling) или webhook для получения изменений
   - Автоматическое обновление доступности

### Поддерживаемые Платформы

#### 1. **Google Calendar** (Приоритет 1) 🟢
- **Протокол**: Google Calendar API v3 + OAuth 2.0
- **Преимущества**:
  - Наиболее популярная система
  - Мощный API с отличной документацией
  - Webhooks (Push notifications) для real-time обновлений
  - Бесплатное использование для большинства случаев
- **Квоты**: 1,000,000 запросов/день (бесплатно)

#### 2. **Apple Calendar / iCloud** (Приоритет 2) 🟡
- **Протокол**: CalDAV (RFC 4791)
- **Преимущества**:
  - Стандартный открытый протокол
  - Популярен среди врачей с Apple устройствами
  - Хорошая совместимость
- **Ограничения**:
  - Требует app-specific password для iCloud
  - Менее удобная авторизация

#### 3. **Microsoft Outlook / Office 365** (Приоритет 2) 🟡
- **Протокол**: Microsoft Graph API + OAuth 2.0
- **Преимущества**:
  - Широко используется в корпоративной среде
  - Современный REST API
  - Webhooks для real-time обновлений
- **Квоты**: 10,000 запросов/10 минут на приложение

#### 4. **Универсальный CalDAV** (Приоритет 3) 🔵
- **Протокол**: CalDAV (RFC 4791)
- **Преимущества**:
  - Поддержка любых CalDAV серверов (Nextcloud, Fastmail, etc.)
  - Стандартизированный протокол
- **Применение**: Для специфических случаев и самостоятельных серверов

---

## Архитектура Системы

### Модель Данных

```python
# Новая таблица: calendar_integrations
class CalendarIntegration(db.Model):
    id = UUID (primary key)
    doctor_id = UUID (foreign key → doctors)
    
    # Тип интеграции
    provider = String  # 'google', 'apple', 'outlook', 'caldav'
    
    # Авторизация
    oauth_access_token = String (encrypted)
    oauth_refresh_token = String (encrypted)
    oauth_token_expires_at = DateTime
    
    # Для CalDAV
    caldav_url = String
    caldav_username = String
    caldav_password = String (encrypted)
    caldav_calendar_id = String
    
    # Настройки синхронизации
    sync_enabled = Boolean (default: True)
    sync_direction = String  # 'both', 'to_external', 'from_external'
    last_sync_at = DateTime
    sync_status = String  # 'active', 'error', 'disconnected'
    sync_error_message = Text
    
    # Настройки создания событий
    event_title_template = String  # e.g., "Termin mit {patient_name}"
    event_description_template = Text
    event_color = String  # для цветовой маркировки
    
    # Webhook/Notifications
    external_webhook_id = String  # для Google/Outlook webhooks
    external_resource_id = String
    
    created_at = DateTime
    updated_at = DateTime
```

### Дополнения в Doctor Model

```python
class Doctor(db.Model):
    # ... существующие поля ...
    
    # Настройки календарной интеграции
    calendar_integration_enabled = Boolean (default: False)
    calendar_sync_conflicts = String  # 'block_slot', 'show_warning', 'ignore'
    
    # Relationships
    calendar_integrations = relationship('CalendarIntegration', back_populates='doctor')
```

---

## Логика Синхронизации

### 1. Подключение Календаря

```
1. Пользователь нажимает "Connect Google Calendar"
2. Redirect на OAuth consent screen
3. После авторизации → callback с authorization code
4. Обмен code на access_token + refresh_token
5. Сохранение токенов в БД (зашифрованно)
6. Создание webhook (если поддерживается)
7. Первичная полная синхронизация
```

### 2. Создание Бронирования (TerminFinder → External)

```python
# Когда пациент бронирует слот в TerminFinder:
1. Создать Booking в БД
2. Обновить TimeSlot status = 'booked'
3. Для каждой активной интеграции врача:
   a. Создать событие во внешнем календаре:
      - Title: "Termin mit Max Müller"
      - Time: start_time → end_time слота
      - Description: контактная информация
   b. Сохранить external_event_id в таблице bookings
4. Отправить подтверждение пациенту
```

### 3. Синхронизация из Внешнего Календаря (External → TerminFinder)

#### Вариант A: Polling (для CalDAV и fallback)

```python
# Celery task: sync_external_calendars
# Запускается каждые 5-15 минут

def sync_doctor_calendar(doctor_id):
    integration = CalendarIntegration.query.filter_by(
        doctor_id=doctor_id, 
        sync_enabled=True
    ).first()
    
    if not integration:
        return
    
    # Получить события из внешнего календаря за период
    external_events = fetch_external_events(
        integration, 
        date_from=today, 
        date_to=today + 90 days
    )
    
    # Для каждого события:
    for event in external_events:
        # Если событие не из TerminFinder (нет external_event_id):
        if not is_terminfinder_event(event):
            # Найти пересекающиеся TimeSlots
            overlapping_slots = find_overlapping_slots(
                doctor.calendar_id,
                event.start_time,
                event.end_time
            )
            
            # Заблокировать слоты
            for slot in overlapping_slots:
                if slot.status == 'available':
                    slot.status = 'blocked'
                    slot.block_reason = f'External: {event.title}'
    
    integration.last_sync_at = datetime.utcnow()
    db.session.commit()
```

#### Вариант B: Webhooks (для Google/Outlook)

```python
# Google Calendar Push Notification
@app.route('/webhooks/calendar/google', methods=['POST'])
def google_calendar_webhook():
    # Получаем notification
    channel_id = request.headers.get('X-Goog-Channel-ID')
    resource_state = request.headers.get('X-Goog-Resource-State')
    
    # Найти интеграцию по channel_id
    integration = CalendarIntegration.query.filter_by(
        external_webhook_id=channel_id
    ).first()
    
    if resource_state == 'sync':
        return '', 200  # Initial sync notification
    
    if resource_state in ['exists', 'not_exists']:
        # Что-то изменилось - запустить синхронизацию
        sync_doctor_calendar.delay(integration.doctor_id)
    
    return '', 200
```

### 4. Разрешение Конфликтов

```python
# Стратегии при обнаружении конфликта:
if doctor.calendar_sync_conflicts == 'block_slot':
    # Автоматически блокировать слоты в TerminFinder
    slot.status = 'blocked'
    
elif doctor.calendar_sync_conflicts == 'show_warning':
    # Показать слот как доступный, но с предупреждением
    slot.status = 'available'
    slot.warning = 'Возможен конфликт с внешним календарем'
    
elif doctor.calendar_sync_conflicts == 'ignore':
    # Игнорировать внешние события
    pass
```

---

## Реализация API Клиентов

### Google Calendar Service

```python
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

class GoogleCalendarService:
    def __init__(self, integration: CalendarIntegration):
        self.integration = integration
        self.service = None
    
    def authenticate(self):
        creds = Credentials(
            token=decrypt(self.integration.oauth_access_token),
            refresh_token=decrypt(self.integration.oauth_refresh_token),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=os.getenv('GOOGLE_CLIENT_ID'),
            client_secret=os.getenv('GOOGLE_CLIENT_SECRET')
        )
        
        # Обновить токен если истек
        if creds.expired:
            creds.refresh(Request())
            self.integration.oauth_access_token = encrypt(creds.token)
            self.integration.oauth_token_expires_at = creds.expiry
            db.session.commit()
        
        self.service = build('calendar', 'v3', credentials=creds)
    
    def create_event(self, booking: Booking):
        event = {
            'summary': f'Termin mit {booking.patient.name}',
            'description': f'Patient: {booking.patient.phone}',
            'start': {
                'dateTime': booking.timeslot.start_time.isoformat(),
                'timeZone': 'Europe/Berlin',
            },
            'end': {
                'dateTime': booking.timeslot.end_time.isoformat(),
                'timeZone': 'Europe/Berlin',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 30},
                ],
            },
        }
        
        created_event = self.service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        
        return created_event['id']
    
    def get_events(self, time_min, time_max):
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=time_min.isoformat() + 'Z',
            timeMax=time_max.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return events_result.get('items', [])
    
    def setup_webhook(self, callback_url):
        # Watch calendar for changes
        watch_request = {
            'id': str(uuid.uuid4()),
            'type': 'web_hook',
            'address': callback_url,
            'expiration': int((datetime.utcnow() + timedelta(days=7)).timestamp() * 1000)
        }
        
        response = self.service.events().watch(
            calendarId='primary',
            body=watch_request
        ).execute()
        
        self.integration.external_webhook_id = response['id']
        self.integration.external_resource_id = response['resourceId']
        db.session.commit()
```

### Apple Calendar (CalDAV) Service

```python
import caldav

class AppleCalendarService:
    def __init__(self, integration: CalendarIntegration):
        self.integration = integration
        self.client = None
        self.calendar = None
    
    def authenticate(self):
        # iCloud CalDAV endpoint
        url = 'https://caldav.icloud.com'
        
        self.client = caldav.DAVClient(
            url=url,
            username=self.integration.caldav_username,
            password=decrypt(self.integration.caldav_password)
        )
        
        principal = self.client.principal()
        calendars = principal.calendars()
        
        # Использовать primary календарь или указанный
        if self.integration.caldav_calendar_id:
            self.calendar = [c for c in calendars 
                           if c.id == self.integration.caldav_calendar_id][0]
        else:
            self.calendar = calendars[0]
    
    def create_event(self, booking: Booking):
        # Создать iCalendar событие
        ical = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//TerminFinder//DE
BEGIN:VEVENT
UID:{uuid.uuid4()}@terminfinder.de
DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{booking.timeslot.start_time.strftime('%Y%m%dT%H%M%S')}
DTEND:{booking.timeslot.end_time.strftime('%Y%m%dT%H%M%S')}
SUMMARY:Termin mit {booking.patient.name}
DESCRIPTION:Patient: {booking.patient.phone}
END:VEVENT
END:VCALENDAR"""
        
        event = self.calendar.add_event(ical)
        return event.url
    
    def get_events(self, time_min, time_max):
        events = self.calendar.date_search(
            start=time_min,
            end=time_max
        )
        return events
```

### Microsoft Outlook Service

```python
import msal
import requests

class OutlookCalendarService:
    def __init__(self, integration: CalendarIntegration):
        self.integration = integration
        self.access_token = None
    
    def authenticate(self):
        # MSAL для token refresh
        app = msal.ConfidentialClientApplication(
            os.getenv('MICROSOFT_CLIENT_ID'),
            authority='https://login.microsoftonline.com/common',
            client_credential=os.getenv('MICROSOFT_CLIENT_SECRET')
        )
        
        result = app.acquire_token_by_refresh_token(
            decrypt(self.integration.oauth_refresh_token),
            scopes=['Calendars.ReadWrite']
        )
        
        self.access_token = result['access_token']
        self.integration.oauth_access_token = encrypt(result['access_token'])
        db.session.commit()
    
    def create_event(self, booking: Booking):
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        event_data = {
            'subject': f'Termin mit {booking.patient.name}',
            'body': {
                'contentType': 'text',
                'content': f'Patient: {booking.patient.phone}'
            },
            'start': {
                'dateTime': booking.timeslot.start_time.isoformat(),
                'timeZone': 'Europe/Berlin'
            },
            'end': {
                'dateTime': booking.timeslot.end_time.isoformat(),
                'timeZone': 'Europe/Berlin'
            }
        }
        
        response = requests.post(
            'https://graph.microsoft.com/v1.0/me/events',
            headers=headers,
            json=event_data
        )
        
        return response.json()['id']
    
    def get_events(self, time_min, time_max):
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        params = {
            'startDateTime': time_min.isoformat(),
            'endDateTime': time_max.isoformat()
        }
        
        response = requests.get(
            'https://graph.microsoft.com/v1.0/me/calendarView',
            headers=headers,
            params=params
        )
        
        return response.json().get('value', [])
```

---

## API Endpoints

### Управление Интеграциями

```python
# GET /api/doctor/calendar-integrations
# Список всех интеграций текущего врача
{
    "integrations": [
        {
            "id": "uuid",
            "provider": "google",
            "sync_enabled": true,
            "last_sync_at": "2026-01-30T10:00:00Z",
            "sync_status": "active"
        }
    ]
}

# POST /api/doctor/calendar-integrations/connect
# Начать процесс подключения
{
    "provider": "google"  # or "apple", "outlook", "caldav"
}
# Response: redirect URL для OAuth

# GET /api/doctor/calendar-integrations/callback
# OAuth callback endpoint
# Обрабатывает код авторизации и сохраняет токены

# PUT /api/doctor/calendar-integrations/{id}
# Обновить настройки интеграции
{
    "sync_enabled": false,
    "sync_direction": "to_external"
}

# DELETE /api/doctor/calendar-integrations/{id}
# Отключить интеграцию

# POST /api/doctor/calendar-integrations/{id}/sync
# Принудительная синхронизация
```

---

## UI/UX

### Страница Настроек Интеграции

```
┌─────────────────────────────────────────────────────────┐
│ Calendar Integrations                                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ ┌──────────────────────────────────────────────────┐   │
│ │ 📅 Google Calendar                    Connected  │   │
│ │ Last sync: 5 minutes ago                         │   │
│ │ Status: ✅ Active                                │   │
│ │                                                   │   │
│ │ [Sync Now] [Settings] [Disconnect]               │   │
│ └──────────────────────────────────────────────────┘   │
│                                                          │
│ ┌──────────────────────────────────────────────────┐   │
│ │ 📆 Apple Calendar                 Not Connected  │   │
│ │                                                   │   │
│ │ [Connect with iCloud]                            │   │
│ └──────────────────────────────────────────────────┘   │
│                                                          │
│ ┌──────────────────────────────────────────────────┐   │
│ │ 📧 Outlook Calendar               Not Connected  │   │
│ │                                                   │   │
│ │ [Connect with Microsoft]                         │   │
│ └──────────────────────────────────────────────────┘   │
│                                                          │
│ Sync Settings:                                          │
│ ☑ Create events in external calendar for bookings      │
│ ☑ Block TerminFinder slots when busy in external cal   │
│ Conflict resolution: [Block slot ▼]                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Безопасность

### Шифрование Токенов

```python
from cryptography.fernet import Fernet
import os

# Ключ шифрования из env
ENCRYPTION_KEY = os.getenv('CALENDAR_ENCRYPTION_KEY')
cipher = Fernet(ENCRYPTION_KEY)

def encrypt(value: str) -> str:
    return cipher.encrypt(value.encode()).decode()

def decrypt(value: str) -> str:
    return cipher.decrypt(value.encode()).decode()
```

### OAuth Scopes

- **Google**: `https://www.googleapis.com/auth/calendar.events`
- **Microsoft**: `Calendars.ReadWrite`
- **Apple/CalDAV**: App-specific password

---

## Celery Tasks (Background Jobs)

```python
# tasks.py

@celery.task
def sync_all_calendar_integrations():
    """Синхронизация всех активных интеграций"""
    integrations = CalendarIntegration.query.filter_by(
        sync_enabled=True,
        sync_status='active'
    ).all()
    
    for integration in integrations:
        sync_calendar_integration.delay(integration.id)

@celery.task
def sync_calendar_integration(integration_id):
    """Синхронизация конкретной интеграции"""
    integration = CalendarIntegration.query.get(integration_id)
    
    try:
        service = get_calendar_service(integration)
        service.sync_from_external()
        
        integration.sync_status = 'active'
        integration.last_sync_at = datetime.utcnow()
    except Exception as e:
        integration.sync_status = 'error'
        integration.sync_error_message = str(e)
    
    db.session.commit()

@celery.task
def renew_google_webhooks():
    """Google webhooks истекают через 7 дней - обновляем"""
    integrations = CalendarIntegration.query.filter_by(
        provider='google',
        sync_enabled=True
    ).all()
    
    for integration in integrations:
        service = GoogleCalendarService(integration)
        service.renew_webhook()

# Celery Beat Schedule
celery.conf.beat_schedule = {
    'sync-calendars': {
        'task': 'tasks.sync_all_calendar_integrations',
        'schedule': crontab(minute='*/10'),  # Каждые 10 минут
    },
    'renew-google-webhooks': {
        'task': 'tasks.renew_google_webhooks',
        'schedule': crontab(hour=0, minute=0),  # Ежедневно в полночь
    },
}
```

---

## Конфигурация (.env)

```bash
# Google Calendar Integration
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret
GOOGLE_REDIRECT_URI=https://terminfinder.de/api/calendar/google/callback

# Microsoft/Outlook Integration
MICROSOFT_CLIENT_ID=your-app-id
MICROSOFT_CLIENT_SECRET=your-secret
MICROSOFT_REDIRECT_URI=https://terminfinder.de/api/calendar/outlook/callback

# Encryption for tokens
CALENDAR_ENCRYPTION_KEY=generate-with-fernet-key

# CalDAV (Apple iCloud)
# Настраивается per-user через UI
```

---

## Requirements

```txt
# Calendar Integrations
google-auth==2.26.2
google-auth-oauthlib==1.2.0
google-api-python-client==2.116.0
caldav==1.3.9
msal==1.26.0
icalendar==5.0.11

# Encryption
cryptography==41.0.7

# Background Tasks (если еще нет)
celery==5.3.4
redis==5.0.1
```

---

## Этапы Внедрения

### Phase 1: Google Calendar (2-3 дня) 🔥
1. ✅ Модели данных + миграция БД
2. ✅ OAuth flow для Google
3. ✅ Базовая синхронизация (создание событий)
4. ✅ UI для подключения
5. ✅ Тестирование

### Phase 2: Bidirectional Sync (2-3 дня)
1. ✅ Polling синхронизация из Google
2. ✅ Webhooks для real-time обновлений
3. ✅ Обработка конфликтов
4. ✅ Celery tasks

### Phase 3: Apple & Outlook (3-4 дня)
1. ✅ Apple/iCloud CalDAV integration
2. ✅ Microsoft Outlook/Office 365
3. ✅ Универсальный CalDAV
4. ✅ Расширенные настройки

### Phase 4: Polish & Production (1-2 дня)
1. ✅ Error handling & logging
2. ✅ Rate limiting & quotas
3. ✅ Monitoring & alerts
4. ✅ Documentation

---

## Преимущества для Практик

✅ **Простота внедрения**: Врачи продолжают использовать привычный календарь  
✅ **Автоматизация**: Синхронизация происходит автоматически  
✅ **Гибкость**: Выбор направления синхронизации  
✅ **Надежность**: Резервное polling если webhooks не работают  
✅ **Безопасность**: Шифрование токенов, OAuth 2.0  
✅ **Универсальность**: Поддержка всех популярных платформ

---

## Следующие Шаги

1. Создать модель `CalendarIntegration`
2. Реализовать Google Calendar integration (приоритет)
3. Добавить UI для управления интеграциями
4. Настроить Celery для background sync
5. Протестировать с реальными врачами

**Готовы начать реализацию?** 🚀
