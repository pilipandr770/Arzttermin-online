"""
CalendarIntegration Model - Интеграция с внешними календарями
"""
from app import db
from app.models import get_table_args
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid


class CalendarIntegration(db.Model):
    """
    Интеграция календаря врача с внешними системами
    
    Поддерживает: Google Calendar, Apple/iCloud Calendar, Outlook/Office 365, CalDAV
    """
    __tablename__ = 'calendar_integrations'
    __table_args__ = get_table_args()
    
    # Primary Key
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    doctor_id = db.Column(UUID(as_uuid=True), db.ForeignKey('terminfinder.doctors.id'), nullable=False, index=True)
    
    # Тип провайдера
    provider = db.Column(db.String(20), nullable=False)
    # Допустимые значения: 'google', 'apple', 'outlook', 'caldav'
    
    # OAuth 2.0 Credentials (для Google, Outlook)
    oauth_access_token = db.Column(db.Text, nullable=True)  # Зашифрованный токен
    oauth_refresh_token = db.Column(db.Text, nullable=True)  # Зашифрованный токен
    oauth_token_expires_at = db.Column(db.DateTime, nullable=True)
    oauth_scope = db.Column(db.String(500), nullable=True)  # Запрошенные разрешения
    
    # CalDAV Credentials (для Apple, самостоятельных серверов)
    caldav_url = db.Column(db.String(500), nullable=True)
    caldav_username = db.Column(db.String(200), nullable=True)
    caldav_password = db.Column(db.Text, nullable=True)  # Зашифрованный пароль
    caldav_calendar_id = db.Column(db.String(200), nullable=True)  # ID конкретного календаря
    
    # Настройки синхронизации
    sync_enabled = db.Column(db.Boolean, default=True, nullable=False)
    sync_direction = db.Column(db.String(20), default='both', nullable=False)
    # Допустимые значения:
    # - 'both': двунаправленная синхронизация
    # - 'to_external': только создавать события во внешнем календаре
    # - 'from_external': только блокировать слоты на основе внешнего календаря
    
    # Статус синхронизации
    last_sync_at = db.Column(db.DateTime, nullable=True)
    next_sync_at = db.Column(db.DateTime, nullable=True)
    sync_status = db.Column(db.String(20), default='active', nullable=False)
    # Допустимые значения: 'active', 'error', 'disconnected', 'paused'
    sync_error_message = db.Column(db.Text, nullable=True)
    sync_error_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Webhook Configuration (для Google, Outlook)
    external_webhook_id = db.Column(db.String(200), nullable=True)  # Channel ID
    external_resource_id = db.Column(db.String(200), nullable=True)  # Resource ID
    webhook_expires_at = db.Column(db.DateTime, nullable=True)
    
    # Настройки создания событий во внешнем календаре
    event_title_template = db.Column(db.String(200), default='Termin mit {patient_name}', nullable=False)
    event_description_template = db.Column(db.Text, default='Patient: {patient_name}\nTelefon: {patient_phone}', nullable=False)
    event_color_id = db.Column(db.String(10), nullable=True)  # Google Calendar color ID
    event_reminders = db.Column(db.Boolean, default=True, nullable=False)  # Включить напоминания
    
    # Настройки блокировки слотов из внешнего календаря
    import_free_busy = db.Column(db.Boolean, default=True, nullable=False)  # Импортировать занятые слоты
    import_event_titles = db.Column(db.Boolean, default=False, nullable=False)  # Импортировать названия событий (приватность)
    auto_block_conflicts = db.Column(db.Boolean, default=True, nullable=False)  # Автоматически блокировать конфликтующие слоты
    
    # Дополнительные метаданные
    external_calendar_name = db.Column(db.String(200), nullable=True)  # Название календаря во внешней системе
    external_calendar_timezone = db.Column(db.String(50), default='Europe/Berlin', nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    connected_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    disconnected_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    doctor = db.relationship('Doctor', back_populates='calendar_integrations')
    
    def __repr__(self):
        return f'<CalendarIntegration {self.provider} for Doctor {self.doctor_id}>'
    
    def to_dict(self, include_sensitive=False):
        """
        Сериализация для API
        
        Args:
            include_sensitive: включить ли чувствительные данные (токены)
        """
        data = {
            'id': str(self.id),
            'doctor_id': str(self.doctor_id),
            'provider': self.provider,
            'sync_enabled': self.sync_enabled,
            'sync_direction': self.sync_direction,
            'sync_status': self.sync_status,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'next_sync_at': self.next_sync_at.isoformat() if self.next_sync_at else None,
            'sync_error_message': self.sync_error_message if self.sync_status == 'error' else None,
            'settings': {
                'event_title_template': self.event_title_template,
                'event_description_template': self.event_description_template,
                'event_reminders': self.event_reminders,
                'import_free_busy': self.import_free_busy,
                'import_event_titles': self.import_event_titles,
                'auto_block_conflicts': self.auto_block_conflicts
            },
            'external_calendar_name': self.external_calendar_name,
            'external_calendar_timezone': self.external_calendar_timezone,
            'created_at': self.created_at.isoformat(),
            'connected_at': self.connected_at.isoformat(),
            'disconnected_at': self.disconnected_at.isoformat() if self.disconnected_at else None
        }
        
        # Включаем чувствительную информацию только если явно запрошено (для внутреннего использования)
        if include_sensitive:
            data['credentials'] = {
                'has_access_token': bool(self.oauth_access_token),
                'has_refresh_token': bool(self.oauth_refresh_token),
                'token_expires_at': self.oauth_token_expires_at.isoformat() if self.oauth_token_expires_at else None,
                'has_caldav_credentials': bool(self.caldav_url and self.caldav_username and self.caldav_password)
            }
        
        return data
    
    def is_token_expired(self):
        """Проверить истек ли OAuth токен"""
        if not self.oauth_token_expires_at:
            return False
        return datetime.utcnow() >= self.oauth_token_expires_at
    
    def is_webhook_expired(self):
        """Проверить истек ли webhook"""
        if not self.webhook_expires_at:
            return True
        return datetime.utcnow() >= self.webhook_expires_at
    
    def increment_error_count(self):
        """Увеличить счетчик ошибок синхронизации"""
        self.sync_error_count += 1
        
        # После 5 ошибок подряд - приостановить синхронизацию
        if self.sync_error_count >= 5:
            self.sync_status = 'paused'
            self.sync_enabled = False
    
    def reset_error_count(self):
        """Сбросить счетчик ошибок после успешной синхронизации"""
        self.sync_error_count = 0
        self.sync_error_message = None
        if self.sync_status == 'paused':
            self.sync_status = 'active'
