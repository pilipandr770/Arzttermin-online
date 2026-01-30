"""
Calendar Integration Service - Базовая логика интеграции с внешними календарями
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os
from cryptography.fernet import Fernet
from app import db
from app.models.calendar_integration import CalendarIntegration
from app.models.booking import Booking
from app.models.calendar import TimeSlot


class CalendarService(ABC):
    """
    Абстрактный базовый класс для всех календарных интеграций
    
    Определяет единый интерфейс для работы с различными календарными системами
    """
    
    def __init__(self, integration: CalendarIntegration):
        """
        Args:
            integration: CalendarIntegration model instance
        """
        self.integration = integration
        self.cipher = self._get_cipher()
    
    def _get_cipher(self):
        """Получить cipher для шифрования/дешифрования"""
        key = os.getenv('CALENDAR_ENCRYPTION_KEY')
        if not key:
            raise ValueError('CALENDAR_ENCRYPTION_KEY not set in environment')
        return Fernet(key.encode())
    
    def encrypt(self, value: str) -> str:
        """Зашифровать значение"""
        if not value:
            return None
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt(self, value: str) -> str:
        """Расшифровать значение"""
        if not value:
            return None
        return self.cipher.decrypt(value.encode()).decode()
    
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Аутентификация в календарной системе
        
        Returns:
            bool: True если аутентификация успешна
        """
        pass
    
    @abstractmethod
    def create_event(self, booking: Booking) -> str:
        """
        Создать событие в внешнем календаре на основе бронирования
        
        Args:
            booking: Booking instance
        
        Returns:
            str: ID созданного события во внешней системе
        """
        pass
    
    @abstractmethod
    def update_event(self, external_event_id: str, booking: Booking) -> bool:
        """
        Обновить существующее событие
        
        Args:
            external_event_id: ID события во внешней системе
            booking: Обновленное бронирование
        
        Returns:
            bool: True если обновление успешно
        """
        pass
    
    @abstractmethod
    def delete_event(self, external_event_id: str) -> bool:
        """
        Удалить событие из внешнего календаря
        
        Args:
            external_event_id: ID события во внешней системе
        
        Returns:
            bool: True если удаление успешно
        """
        pass
    
    @abstractmethod
    def get_events(self, time_min: datetime, time_max: datetime) -> List[Dict]:
        """
        Получить события из внешнего календаря за период
        
        Args:
            time_min: Начало периода
            time_max: Конец периода
        
        Returns:
            List[Dict]: Список событий в стандартизированном формате
        """
        pass
    
    def sync_from_external(self):
        """
        Синхронизация из внешнего календаря в TerminFinder
        
        Блокирует слоты, которые заняты во внешнем календаре
        """
        try:
            # Аутентификация
            if not self.authenticate():
                raise Exception("Authentication failed")
            
            # Получить события на ближайшие 90 дней
            now = datetime.utcnow()
            time_max = now + timedelta(days=90)
            
            external_events = self.get_events(now, time_max)
            
            # Фильтруем события, созданные TerminFinder
            external_only_events = [
                event for event in external_events
                if not self._is_terminfinder_event(event)
            ]
            
            # Для каждого внешнего события блокируем пересекающиеся слоты
            blocked_count = 0
            for event in external_only_events:
                blocked = self._block_overlapping_slots(event)
                blocked_count += blocked
            
            # Обновить статус интеграции
            self.integration.last_sync_at = datetime.utcnow()
            self.integration.sync_status = 'active'
            self.integration.reset_error_count()
            db.session.commit()
            
            return {
                'success': True,
                'external_events_count': len(external_only_events),
                'slots_blocked': blocked_count
            }
            
        except Exception as e:
            self.integration.sync_status = 'error'
            self.integration.sync_error_message = str(e)
            self.integration.increment_error_count()
            db.session.commit()
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def sync_to_external(self, booking: Booking) -> Optional[str]:
        """
        Создать событие во внешнем календаре для бронирования
        
        Args:
            booking: Booking instance
        
        Returns:
            str: ID созданного события или None при ошибке
        """
        try:
            if not self.authenticate():
                raise Exception("Authentication failed")
            
            external_event_id = self.create_event(booking)
            
            return external_event_id
            
        except Exception as e:
            print(f"Error syncing to external calendar: {e}")
            return None
    
    def _is_terminfinder_event(self, event: Dict) -> bool:
        """
        Проверить создано ли событие TerminFinder
        
        Проверяет по описанию или дополнительным полям
        """
        # Можно добавить специальный маркер в description
        description = event.get('description', '')
        return 'TerminFinder' in description or '[TF]' in description
    
    def _block_overlapping_slots(self, event: Dict) -> int:
        """
        Заблокировать слоты, которые пересекаются с событием
        
        Args:
            event: Событие из внешнего календаря
        
        Returns:
            int: Количество заблокированных слотов
        """
        if not self.integration.auto_block_conflicts:
            return 0
        
        event_start = event['start']
        event_end = event['end']
        event_title = event.get('title', 'External Event')
        
        # Найти календарь врача
        doctor = self.integration.doctor
        if not doctor.calendar:
            return 0
        
        # Найти все слоты, которые пересекаются с событием
        overlapping_slots = TimeSlot.query.filter(
            TimeSlot.calendar_id == doctor.calendar.id,
            TimeSlot.start_time < event_end,
            TimeSlot.end_time > event_start,
            TimeSlot.status == 'available'
        ).all()
        
        blocked_count = 0
        for slot in overlapping_slots:
            slot.status = 'blocked'
            slot.blocked_reason = f'External: {event_title}' if self.integration.import_event_titles else 'External Calendar'
            blocked_count += 1
        
        if blocked_count > 0:
            db.session.commit()
        
        return blocked_count
    
    def format_event_title(self, booking: Booking) -> str:
        """
        Форматировать название события по шаблону
        
        Args:
            booking: Booking instance
        
        Returns:
            str: Отформатированное название
        """
        template = self.integration.event_title_template
        
        return template.format(
            patient_name=booking.patient.name if booking.patient else 'Patient',
            doctor_name=self.integration.doctor.name,
            speciality=self.integration.doctor.display_speciality
        )
    
    def format_event_description(self, booking: Booking) -> str:
        """
        Форматировать описание события по шаблону
        
        Args:
            booking: Booking instance
        
        Returns:
            str: Отформатированное описание
        """
        template = self.integration.event_description_template
        
        description = template.format(
            patient_name=booking.patient.name if booking.patient else 'N/A',
            patient_phone=booking.patient.phone if booking.patient else 'N/A',
            patient_email=booking.patient.email if booking.patient else 'N/A',
            booking_id=str(booking.id)
        )
        
        # Добавить маркер TerminFinder
        description += '\n\n[TF] Created by TerminFinder'
        
        return description


def get_calendar_service(integration: CalendarIntegration) -> CalendarService:
    """
    Factory function для создания соответствующего календарного сервиса
    
    Args:
        integration: CalendarIntegration instance
    
    Returns:
        CalendarService: Соответствующая имплементация
    """
    from app.services.google_calendar_service import GoogleCalendarService
    from app.services.apple_calendar_service import AppleCalendarService
    from app.services.outlook_calendar_service import OutlookCalendarService
    
    if integration.provider == 'google':
        return GoogleCalendarService(integration)
    elif integration.provider == 'apple':
        return AppleCalendarService(integration)
    elif integration.provider == 'outlook':
        return OutlookCalendarService(integration)
    elif integration.provider == 'caldav':
        return AppleCalendarService(integration)  # CalDAV используется для Apple и других
    else:
        raise ValueError(f"Unknown calendar provider: {integration.provider}")


def create_external_event_for_booking(booking: Booking):
    """
    Создать события во всех подключенных календарях врача
    
    Args:
        booking: Booking instance
    """
    doctor = booking.timeslot.calendar.doctor
    
    # Получить все активные интеграции
    integrations = CalendarIntegration.query.filter_by(
        doctor_id=doctor.id,
        sync_enabled=True,
        sync_status='active'
    ).filter(
        CalendarIntegration.sync_direction.in_(['both', 'to_external'])
    ).all()
    
    for integration in integrations:
        try:
            service = get_calendar_service(integration)
            external_id = service.sync_to_external(booking)
            
            # Сохранить external_id в booking (если нужно отслеживать)
            # booking.external_calendar_ids = {integration.provider: external_id}
            
        except Exception as e:
            print(f"Error creating event in {integration.provider}: {e}")
            # Не прерываем процесс, продолжаем с другими интеграциями


def update_external_event_for_booking(booking: Booking):
    """
    Обновить события во всех подключенных календарях
    
    Args:
        booking: Booking instance
    """
    doctor = booking.timeslot.calendar.doctor
    
    integrations = CalendarIntegration.query.filter_by(
        doctor_id=doctor.id,
        sync_enabled=True
    ).all()
    
    for integration in integrations:
        try:
            service = get_calendar_service(integration)
            # TODO: Получить external_event_id из booking
            # service.update_event(external_event_id, booking)
        except Exception as e:
            print(f"Error updating event in {integration.provider}: {e}")


def delete_external_event_for_booking(booking: Booking):
    """
    Удалить события из всех подключенных календарей
    
    Args:
        booking: Booking instance
    """
    doctor = booking.timeslot.calendar.doctor
    
    integrations = CalendarIntegration.query.filter_by(
        doctor_id=doctor.id,
        sync_enabled=True
    ).all()
    
    for integration in integrations:
        try:
            service = get_calendar_service(integration)
            # TODO: Получить external_event_id из booking
            # service.delete_event(external_event_id)
        except Exception as e:
            print(f"Error deleting event from {integration.provider}: {e}")
