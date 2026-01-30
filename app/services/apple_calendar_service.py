"""
Apple Calendar Service - Интеграция с Apple Calendar через CalDAV
"""
from typing import List, Dict
from datetime import datetime
import caldav
from icalendar import Calendar as iCalendar, Event as iEvent

from app.services.calendar_integration_service import CalendarService
from app.models.booking import Booking
from app.models.calendar_integration import CalendarIntegration


class AppleCalendarService(CalendarService):
    """
    Сервис для работы с Apple Calendar (iCloud) через CalDAV протокол
    
    Также работает с любыми CalDAV серверами (Nextcloud, Fastmail, etc.)
    """
    
    def __init__(self, integration: CalendarIntegration):
        super().__init__(integration)
        self.client = None
        self.calendar = None
    
    def authenticate(self) -> bool:
        """
        Аутентификация через CalDAV
        
        Returns:
            bool: True если аутентификация успешна
        """
        try:
            # URL для iCloud CalDAV
            url = self.integration.caldav_url or 'https://caldav.icloud.com'
            
            # Получить пароль (попытаться расшифровать, если не получится - использовать как есть)
            try:
                password = self.decrypt(self.integration.caldav_password)
            except Exception:
                # Если расшифровка не удалась, значит это открытый текст (для тестирования)
                password = self.integration.caldav_password
            
            # Создать CalDAV клиент
            self.client = caldav.DAVClient(
                url=url,
                username=self.integration.caldav_username,
                password=password
            )
            
            # Получить principal (пользователя)
            principal = self.client.principal()
            
            # Получить календари
            calendars = principal.calendars()
            
            if not calendars:
                raise Exception("No calendars found")
            
            # Использовать указанный календарь или первый доступный
            if self.integration.caldav_calendar_id:
                self.calendar = next(
                    (c for c in calendars if str(c.id) == self.integration.caldav_calendar_id),
                    calendars[0]
                )
            else:
                self.calendar = calendars[0]
                # Сохранить ID первого календаря
                self.integration.caldav_calendar_id = str(self.calendar.id)
                self.integration.external_calendar_name = self.calendar.name
            
            return True
            
        except Exception as e:
            print(f"Apple Calendar authentication error: {e}")
            return False
    
    def create_event(self, booking: Booking) -> str:
        """
        Создать событие в Apple Calendar
        
        Args:
            booking: Booking instance
        
        Returns:
            str: UID созданного события
        """
        if not self.calendar:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        # Создать iCalendar событие
        cal = iCalendar()
        cal.add('prodid', '-//TerminFinder//DE')
        cal.add('version', '2.0')
        
        event = iEvent()
        event.add('uid', f'terminfinder-{booking.id}@terminfinder.de')
        event.add('dtstamp', datetime.utcnow())
        event.add('dtstart', booking.timeslot.start_time)
        event.add('dtend', booking.timeslot.end_time)
        event.add('summary', self.format_event_title(booking))
        event.add('description', self.format_event_description(booking))
        
        # Добавить напоминание если настроено
        if self.integration.event_reminders:
            from icalendar import Alarm
            alarm = Alarm()
            alarm.add('action', 'DISPLAY')
            alarm.add('trigger', timedelta(minutes=-30))
            alarm.add('description', 'Termin Erinnerung')
            event.add_component(alarm)
        
        cal.add_component(event)
        
        try:
            # Добавить событие в календарь
            created_event = self.calendar.add_event(cal.to_ical().decode('utf-8'))
            
            return str(event.get('uid'))
            
        except Exception as e:
            raise Exception(f"Failed to create Apple Calendar event: {e}")
    
    def update_event(self, external_event_id: str, booking: Booking) -> bool:
        """
        Обновить существующее событие в Apple Calendar
        
        Args:
            external_event_id: UID события
            booking: Обновленное бронирование
        
        Returns:
            bool: True если обновление успешно
        """
        if not self.calendar:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        try:
            # Найти событие по UID
            events = self.calendar.events()
            target_event = None
            
            for event in events:
                ical_data = event.icalendar_component
                if str(ical_data.get('uid')) == external_event_id:
                    target_event = event
                    break
            
            if not target_event:
                return False
            
            # Обновить событие
            ical_data = target_event.icalendar_component
            ical_data['summary'] = self.format_event_title(booking)
            ical_data['description'] = self.format_event_description(booking)
            ical_data['dtstart'] = booking.timeslot.start_time
            ical_data['dtend'] = booking.timeslot.end_time
            
            target_event.save()
            
            return True
            
        except Exception as e:
            print(f"Failed to update Apple Calendar event: {e}")
            return False
    
    def delete_event(self, external_event_id: str) -> bool:
        """
        Удалить событие из Apple Calendar
        
        Args:
            external_event_id: UID события
        
        Returns:
            bool: True если удаление успешно
        """
        if not self.calendar:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        try:
            # Найти событие по UID
            events = self.calendar.events()
            
            for event in events:
                ical_data = event.icalendar_component
                if str(ical_data.get('uid')) == external_event_id:
                    event.delete()
                    return True
            
            return False
            
        except Exception as e:
            print(f"Failed to delete Apple Calendar event: {e}")
            return False
    
    def get_events(self, time_min: datetime, time_max: datetime) -> List[Dict]:
        """
        Получить события из Apple Calendar за период
        
        Args:
            time_min: Начало периода
            time_max: Конец периода
        
        Returns:
            List[Dict]: Список событий в стандартизированном формате
        """
        if not self.calendar:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        try:
            # Запрос событий за период
            events = self.calendar.date_search(
                start=time_min,
                end=time_max,
                expand=True
            )
            
            # Преобразовать в стандартизированный формат
            standardized_events = []
            
            for event in events:
                try:
                    ical_data = event.icalendar_component
                    
                    # Получить время начала и окончания
                    dtstart = ical_data.get('dtstart')
                    dtend = ical_data.get('dtend')
                    
                    if not dtstart or not dtend:
                        continue
                    
                    # Преобразовать в datetime если это date
                    start_dt = dtstart.dt if hasattr(dtstart, 'dt') else dtstart
                    end_dt = dtend.dt if hasattr(dtend, 'dt') else dtend
                    
                    if not isinstance(start_dt, datetime):
                        # Пропустить целодневные события
                        continue
                    
                    standardized_event = {
                        'id': str(ical_data.get('uid', '')),
                        'title': str(ical_data.get('summary', 'Busy')),
                        'description': str(ical_data.get('description', '')),
                        'start': start_dt,
                        'end': end_dt,
                        'status': 'confirmed',
                    }
                    
                    standardized_events.append(standardized_event)
                    
                except Exception as e:
                    print(f"Error parsing CalDAV event: {e}")
                    continue
            
            return standardized_events
            
        except Exception as e:
            raise Exception(f"Failed to fetch Apple Calendar events: {e}")
    
    def list_calendars(self) -> List[Dict]:
        """
        Получить список доступных календарей
        
        Returns:
            List[Dict]: Список календарей с ID и названиями
        """
        if not self.client:
            if not self.authenticate():
                return []
        
        try:
            principal = self.client.principal()
            calendars = principal.calendars()
            
            return [
                {
                    'id': str(cal.id),
                    'name': cal.name,
                    'url': str(cal.url)
                }
                for cal in calendars
            ]
            
        except Exception as e:
            print(f"Failed to list calendars: {e}")
            return []
