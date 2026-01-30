"""
Google Calendar Service - Интеграция с Google Calendar API
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os
import uuid
import requests

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app import db
from app.services.calendar_integration_service import CalendarService
from app.models.booking import Booking
from app.models.calendar_integration import CalendarIntegration


class GoogleCalendarService(CalendarService):
    """
    Сервис для работы с Google Calendar API
    
    Использует OAuth 2.0 для авторизации и Google Calendar API v3
    """
    
    def __init__(self, integration: CalendarIntegration):
        super().__init__(integration)
        self.service = None
        self.credentials = None
    
    def authenticate(self) -> bool:
        """
        Аутентификация через OAuth 2.0
        
        Returns:
            bool: True если аутентификация успешна
        """
        try:
            # Создать credentials из сохраненных токенов
            self.credentials = Credentials(
                token=self.decrypt(self.integration.oauth_access_token),
                refresh_token=self.decrypt(self.integration.oauth_refresh_token),
                token_uri='https://oauth2.googleapis.com/token',
                client_id=os.getenv('GOOGLE_CLIENT_ID'),
                client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
                scopes=['https://www.googleapis.com/auth/calendar.events']
            )
            
            # Обновить токен если истек
            if self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
                
                # Сохранить обновленные токены
                self.integration.oauth_access_token = self.encrypt(self.credentials.token)
                if self.credentials.expiry:
                    self.integration.oauth_token_expires_at = self.credentials.expiry
                db.session.commit()
            
            # Создать сервис Google Calendar API
            self.service = build('calendar', 'v3', credentials=self.credentials)
            
            return True
            
        except Exception as e:
            print(f"Google Calendar authentication error: {e}")
            return False
    
    def create_event(self, booking: Booking) -> str:
        """
        Создать событие в Google Calendar
        
        Args:
            booking: Booking instance
        
        Returns:
            str: ID созданного события в Google Calendar
        """
        if not self.service:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        # Подготовить данные события
        event = {
            'summary': self.format_event_title(booking),
            'description': self.format_event_description(booking),
            'start': {
                'dateTime': booking.timeslot.start_time.isoformat(),
                'timeZone': self.integration.external_calendar_timezone,
            },
            'end': {
                'dateTime': booking.timeslot.end_time.isoformat(),
                'timeZone': self.integration.external_calendar_timezone,
            },
        }
        
        # Добавить цвет если настроено
        if self.integration.event_color_id:
            event['colorId'] = self.integration.event_color_id
        
        # Добавить напоминания
        if self.integration.event_reminders:
            event['reminders'] = {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 30},
                    {'method': 'email', 'minutes': 60},
                ],
            }
        else:
            event['reminders'] = {'useDefault': False}
        
        try:
            # Создать событие
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            return created_event['id']
            
        except HttpError as e:
            raise Exception(f"Failed to create Google Calendar event: {e}")
    
    def update_event(self, external_event_id: str, booking: Booking) -> bool:
        """
        Обновить существующее событие в Google Calendar
        
        Args:
            external_event_id: ID события в Google Calendar
            booking: Обновленное бронирование
        
        Returns:
            bool: True если обновление успешно
        """
        if not self.service:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        try:
            # Получить существующее событие
            existing_event = self.service.events().get(
                calendarId='primary',
                eventId=external_event_id
            ).execute()
            
            # Обновить поля
            existing_event['summary'] = self.format_event_title(booking)
            existing_event['description'] = self.format_event_description(booking)
            existing_event['start'] = {
                'dateTime': booking.timeslot.start_time.isoformat(),
                'timeZone': self.integration.external_calendar_timezone,
            }
            existing_event['end'] = {
                'dateTime': booking.timeslot.end_time.isoformat(),
                'timeZone': self.integration.external_calendar_timezone,
            }
            
            # Обновить событие
            self.service.events().update(
                calendarId='primary',
                eventId=external_event_id,
                body=existing_event
            ).execute()
            
            return True
            
        except HttpError as e:
            print(f"Failed to update Google Calendar event: {e}")
            return False
    
    def delete_event(self, external_event_id: str) -> bool:
        """
        Удалить событие из Google Calendar
        
        Args:
            external_event_id: ID события в Google Calendar
        
        Returns:
            bool: True если удаление успешно
        """
        if not self.service:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=external_event_id
            ).execute()
            
            return True
            
        except HttpError as e:
            print(f"Failed to delete Google Calendar event: {e}")
            return False
    
    def get_events(self, time_min: datetime, time_max: datetime) -> List[Dict]:
        """
        Получить события из Google Calendar за период
        
        Args:
            time_min: Начало периода
            time_max: Конец периода
        
        Returns:
            List[Dict]: Список событий в стандартизированном формате
        """
        if not self.service:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        try:
            # Запрос событий
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime',
                maxResults=2500  # Максимальное количество событий
            ).execute()
            
            events = events_result.get('items', [])
            
            # Преобразовать в стандартизированный формат
            standardized_events = []
            for event in events:
                # Пропустить события без времени (целодневные)
                if 'dateTime' not in event['start']:
                    continue
                
                standardized_event = {
                    'id': event['id'],
                    'title': event.get('summary', 'Busy'),
                    'description': event.get('description', ''),
                    'start': datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00')),
                    'end': datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00')),
                    'status': event.get('status', 'confirmed'),
                }
                
                standardized_events.append(standardized_event)
            
            return standardized_events
            
        except HttpError as e:
            raise Exception(f"Failed to fetch Google Calendar events: {e}")
    
    def setup_webhook(self, callback_url: str) -> bool:
        """
        Настроить webhook для получения уведомлений об изменениях
        
        Google Calendar Push Notifications позволяют получать real-time обновления
        
        Args:
            callback_url: URL для webhook callbacks
        
        Returns:
            bool: True если webhook успешно настроен
        """
        if not self.service:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        try:
            # Создать уникальный channel ID
            channel_id = str(uuid.uuid4())
            
            # Webhook истекает через 7 дней (максимум для Google)
            expiration = int((datetime.utcnow() + timedelta(days=7)).timestamp() * 1000)
            
            # Настроить watch request
            watch_request = {
                'id': channel_id,
                'type': 'web_hook',
                'address': callback_url,
                'expiration': expiration
            }
            
            # Создать webhook
            response = self.service.events().watch(
                calendarId='primary',
                body=watch_request
            ).execute()
            
            # Сохранить информацию о webhook
            self.integration.external_webhook_id = response['id']
            self.integration.external_resource_id = response['resourceId']
            self.integration.webhook_expires_at = datetime.fromtimestamp(expiration / 1000)
            db.session.commit()
            
            return True
            
        except HttpError as e:
            print(f"Failed to setup Google Calendar webhook: {e}")
            return False
    
    def stop_webhook(self) -> bool:
        """
        Остановить webhook
        
        Returns:
            bool: True если webhook успешно остановлен
        """
        if not self.service:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        if not self.integration.external_webhook_id or not self.integration.external_resource_id:
            return True  # Webhook не был настроен
        
        try:
            self.service.channels().stop(
                body={
                    'id': self.integration.external_webhook_id,
                    'resourceId': self.integration.external_resource_id
                }
            ).execute()
            
            # Очистить информацию о webhook
            self.integration.external_webhook_id = None
            self.integration.external_resource_id = None
            self.integration.webhook_expires_at = None
            db.session.commit()
            
            return True
            
        except HttpError as e:
            print(f"Failed to stop Google Calendar webhook: {e}")
            return False
    
    def renew_webhook(self, callback_url: str) -> bool:
        """
        Обновить webhook (нужно делать каждые 7 дней)
        
        Args:
            callback_url: URL для webhook callbacks
        
        Returns:
            bool: True если webhook успешно обновлен
        """
        # Остановить старый webhook
        self.stop_webhook()
        
        # Создать новый webhook
        return self.setup_webhook(callback_url)
    
    @staticmethod
    def get_authorization_url(state: str) -> str:
        """
        Получить URL для OAuth авторизации
        
        Args:
            state: Случайная строка для защиты от CSRF
        
        Returns:
            str: Authorization URL
        """
        from google_auth_oauthlib.flow import Flow
        
        # Создать flow для OAuth
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                    "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [os.getenv('GOOGLE_REDIRECT_URI')]
                }
            },
            scopes=['https://www.googleapis.com/auth/calendar.events']
        )
        
        flow.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
        
        authorization_url, _ = flow.authorization_url(
            access_type='offline',  # Получить refresh token
            include_granted_scopes='true',
            state=state,
            prompt='consent'  # Всегда показывать consent screen для получения refresh token
        )
        
        return authorization_url
    
    @staticmethod
    def exchange_code_for_tokens(code: str) -> Dict:
        """
        Обменять authorization code на access и refresh токены
        
        Args:
            code: Authorization code из OAuth callback
        
        Returns:
            Dict: Словарь с токенами и expiry
        """
        import requests
        
        # Использовать прямой запрос к Google OAuth API вместо Flow
        # чтобы избежать строгой проверки scope
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            'code': code,
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'redirect_uri': os.getenv('GOOGLE_REDIRECT_URI'),
            'grant_type': 'authorization_code'
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        
        # Вычислить expiry
        expires_in = token_data.get('expires_in', 3600)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        return {
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),
            'expires_at': expires_at,
            'scopes': token_data.get('scope', '').split()
        }
