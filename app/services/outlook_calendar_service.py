"""
Outlook Calendar Service - Интеграция с Microsoft Outlook/Office 365
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os
import requests
import msal

from app import db
from app.services.calendar_integration_service import CalendarService
from app.models.booking import Booking
from app.models.calendar_integration import CalendarIntegration


class OutlookCalendarService(CalendarService):
    """
    Сервис для работы с Microsoft Outlook/Office 365 через Microsoft Graph API
    
    Использует OAuth 2.0 и MSAL (Microsoft Authentication Library)
    """
    
    GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'
    AUTHORITY = 'https://login.microsoftonline.com/common'
    SCOPES = ['Calendars.ReadWrite']
    
    def __init__(self, integration: CalendarIntegration):
        super().__init__(integration)
        self.access_token = None
    
    def authenticate(self) -> bool:
        """
        Аутентификация через OAuth 2.0 с MSAL
        
        Returns:
            bool: True если аутентификация успешна
        """
        try:
            # Создать MSAL приложение
            app = msal.ConfidentialClientApplication(
                os.getenv('MICROSOFT_CLIENT_ID'),
                authority=self.AUTHORITY,
                client_credential=os.getenv('MICROSOFT_CLIENT_SECRET')
            )
            
            # Попытаться обновить токен через refresh token
            result = app.acquire_token_by_refresh_token(
                self.decrypt(self.integration.oauth_refresh_token),
                scopes=self.SCOPES
            )
            
            if 'access_token' in result:
                self.access_token = result['access_token']
                
                # Сохранить обновленные токены
                self.integration.oauth_access_token = self.encrypt(result['access_token'])
                if 'refresh_token' in result:
                    self.integration.oauth_refresh_token = self.encrypt(result['refresh_token'])
                if 'expires_in' in result:
                    self.integration.oauth_token_expires_at = datetime.utcnow() + timedelta(seconds=result['expires_in'])
                
                db.session.commit()
                
                return True
            else:
                raise Exception(f"Token refresh failed: {result.get('error_description', 'Unknown error')}")
            
        except Exception as e:
            print(f"Outlook Calendar authentication error: {e}")
            return False
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        Выполнить HTTP запрос к Microsoft Graph API
        
        Args:
            method: HTTP метод (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (без базового URL)
            data: JSON данные для отправки
        
        Returns:
            Dict: Ответ API
        """
        if not self.access_token:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'Prefer': 'outlook.timezone="Europe/Berlin"'
        }
        
        url = f"{self.GRAPH_API_ENDPOINT}{endpoint}"
        
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        
        # DELETE возвращает 204 без тела
        if response.status_code == 204:
            return {}
        
        return response.json()
    
    def create_event(self, booking: Booking) -> str:
        """
        Создать событие в Outlook Calendar
        
        Args:
            booking: Booking instance
        
        Returns:
            str: ID созданного события
        """
        if not self.access_token:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        # Подготовить данные события
        event_data = {
            'subject': self.format_event_title(booking),
            'body': {
                'contentType': 'text',
                'content': self.format_event_description(booking)
            },
            'start': {
                'dateTime': booking.timeslot.start_time.isoformat(),
                'timeZone': self.integration.external_calendar_timezone
            },
            'end': {
                'dateTime': booking.timeslot.end_time.isoformat(),
                'timeZone': self.integration.external_calendar_timezone
            },
            'isReminderOn': self.integration.event_reminders,
        }
        
        if self.integration.event_reminders:
            event_data['reminderMinutesBeforeStart'] = 30
        
        try:
            response = self._make_request('POST', '/me/events', event_data)
            return response['id']
            
        except requests.HTTPError as e:
            raise Exception(f"Failed to create Outlook Calendar event: {e}")
    
    def update_event(self, external_event_id: str, booking: Booking) -> bool:
        """
        Обновить существующее событие в Outlook Calendar
        
        Args:
            external_event_id: ID события в Outlook
            booking: Обновленное бронирование
        
        Returns:
            bool: True если обновление успешно
        """
        if not self.access_token:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        # Подготовить данные для обновления
        event_data = {
            'subject': self.format_event_title(booking),
            'body': {
                'contentType': 'text',
                'content': self.format_event_description(booking)
            },
            'start': {
                'dateTime': booking.timeslot.start_time.isoformat(),
                'timeZone': self.integration.external_calendar_timezone
            },
            'end': {
                'dateTime': booking.timeslot.end_time.isoformat(),
                'timeZone': self.integration.external_calendar_timezone
            }
        }
        
        try:
            self._make_request('PATCH', f'/me/events/{external_event_id}', event_data)
            return True
            
        except requests.HTTPError as e:
            print(f"Failed to update Outlook Calendar event: {e}")
            return False
    
    def delete_event(self, external_event_id: str) -> bool:
        """
        Удалить событие из Outlook Calendar
        
        Args:
            external_event_id: ID события в Outlook
        
        Returns:
            bool: True если удаление успешно
        """
        if not self.access_token:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        try:
            self._make_request('DELETE', f'/me/events/{external_event_id}')
            return True
            
        except requests.HTTPError as e:
            print(f"Failed to delete Outlook Calendar event: {e}")
            return False
    
    def get_events(self, time_min: datetime, time_max: datetime) -> List[Dict]:
        """
        Получить события из Outlook Calendar за период
        
        Args:
            time_min: Начало периода
            time_max: Конец периода
        
        Returns:
            List[Dict]: Список событий в стандартизированном формате
        """
        if not self.access_token:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        try:
            # Использовать calendarView для получения событий за период
            params = {
                'startDateTime': time_min.isoformat(),
                'endDateTime': time_max.isoformat(),
                '$select': 'id,subject,body,start,end,isAllDay',
                '$top': 999
            }
            
            # Построить query string
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            endpoint = f'/me/calendarView?{query_string}'
            
            response = self._make_request('GET', endpoint)
            events = response.get('value', [])
            
            # Преобразовать в стандартизированный формат
            standardized_events = []
            
            for event in events:
                # Пропустить целодневные события
                if event.get('isAllDay', False):
                    continue
                
                start_str = event['start']['dateTime']
                end_str = event['end']['dateTime']
                
                # Microsoft Graph возвращает время в формате ISO без 'Z'
                start_dt = datetime.fromisoformat(start_str)
                end_dt = datetime.fromisoformat(end_str)
                
                standardized_event = {
                    'id': event['id'],
                    'title': event.get('subject', 'Busy'),
                    'description': event.get('body', {}).get('content', ''),
                    'start': start_dt,
                    'end': end_dt,
                    'status': 'confirmed',
                }
                
                standardized_events.append(standardized_event)
            
            return standardized_events
            
        except requests.HTTPError as e:
            raise Exception(f"Failed to fetch Outlook Calendar events: {e}")
    
    def setup_webhook(self, callback_url: str) -> bool:
        """
        Настроить webhook для получения уведомлений об изменениях
        
        Microsoft Graph Webhooks (Subscriptions)
        
        Args:
            callback_url: URL для webhook callbacks
        
        Returns:
            bool: True если webhook успешно настроен
        """
        if not self.access_token:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        try:
            # Webhook истекает через 4230 минут (примерно 3 дня) для Outlook
            expiration = datetime.utcnow() + timedelta(days=3)
            
            subscription_data = {
                'changeType': 'created,updated,deleted',
                'notificationUrl': callback_url,
                'resource': '/me/events',
                'expirationDateTime': expiration.isoformat() + 'Z',
                'clientState': 'terminfinder-secret-state'  # Для валидации
            }
            
            response = self._make_request('POST', '/subscriptions', subscription_data)
            
            # Сохранить информацию о webhook
            self.integration.external_webhook_id = response['id']
            self.integration.webhook_expires_at = datetime.fromisoformat(response['expirationDateTime'].replace('Z', '+00:00'))
            db.session.commit()
            
            return True
            
        except requests.HTTPError as e:
            print(f"Failed to setup Outlook Calendar webhook: {e}")
            return False
    
    def renew_webhook(self) -> bool:
        """
        Продлить срок действия webhook
        
        Returns:
            bool: True если webhook успешно продлен
        """
        if not self.access_token or not self.integration.external_webhook_id:
            return False
        
        try:
            # Продлить на 3 дня
            new_expiration = datetime.utcnow() + timedelta(days=3)
            
            update_data = {
                'expirationDateTime': new_expiration.isoformat() + 'Z'
            }
            
            response = self._make_request(
                'PATCH',
                f'/subscriptions/{self.integration.external_webhook_id}',
                update_data
            )
            
            self.integration.webhook_expires_at = datetime.fromisoformat(response['expirationDateTime'].replace('Z', '+00:00'))
            db.session.commit()
            
            return True
            
        except requests.HTTPError as e:
            print(f"Failed to renew Outlook Calendar webhook: {e}")
            return False
    
    @staticmethod
    def get_authorization_url(state: str) -> str:
        """
        Получить URL для OAuth авторизации
        
        Args:
            state: Случайная строка для защиты от CSRF
        
        Returns:
            str: Authorization URL
        """
        app = msal.ConfidentialClientApplication(
            os.getenv('MICROSOFT_CLIENT_ID'),
            authority=OutlookCalendarService.AUTHORITY,
            client_credential=os.getenv('MICROSOFT_CLIENT_SECRET')
        )
        
        auth_url = app.get_authorization_request_url(
            scopes=OutlookCalendarService.SCOPES,
            state=state,
            redirect_uri=os.getenv('MICROSOFT_REDIRECT_URI')
        )
        
        return auth_url
    
    @staticmethod
    def exchange_code_for_tokens(code: str) -> Dict:
        """
        Обменять authorization code на access и refresh токены
        
        Args:
            code: Authorization code из OAuth callback
        
        Returns:
            Dict: Словарь с токенами и expiry
        """
        app = msal.ConfidentialClientApplication(
            os.getenv('MICROSOFT_CLIENT_ID'),
            authority=OutlookCalendarService.AUTHORITY,
            client_credential=os.getenv('MICROSOFT_CLIENT_SECRET')
        )
        
        result = app.acquire_token_by_authorization_code(
            code,
            scopes=OutlookCalendarService.SCOPES,
            redirect_uri=os.getenv('MICROSOFT_REDIRECT_URI')
        )
        
        if 'error' in result:
            raise Exception(f"Token exchange failed: {result.get('error_description', 'Unknown error')}")
        
        return {
            'access_token': result['access_token'],
            'refresh_token': result.get('refresh_token'),
            'expires_at': datetime.utcnow() + timedelta(seconds=result.get('expires_in', 3600)),
            'scopes': result.get('scope', '').split()
        }
