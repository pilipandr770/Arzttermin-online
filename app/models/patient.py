"""
Patient и PatientAlert Models - Пациент и терминные "будильники"
"""
from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
import uuid
import os
import json


class Patient(db.Model):
    """
    Пациент (B2C пользователь)
    
    Минимальные персональные данные - только email
    """
    __tablename__ = 'patients'
    # Schema только для PostgreSQL
    if 'postgresql' in os.getenv('DATABASE_URL', ''):
        __table_args__ = {'schema': os.getenv('DB_SCHEMA', 'public')}
    
    # Primary Key
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Основная информация
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=True)  # опционально
    
    # Stripe
    stripe_customer_id = db.Column(db.String(100), nullable=True, unique=True)
    
    # Статистика (для репутации)
    total_bookings = db.Column(db.Integer, default=0)
    no_show_count = db.Column(db.Integer, default=0)
    late_cancellations = db.Column(db.Integer, default=0)  # отмены < 24 часов
    early_cancellations = db.Column(db.Integer, default=0)  # отмены > 24 часов
    attended_appointments = db.Column(db.Integer, default=0)
    
    # Preferences
    notification_email = db.Column(db.Boolean, default=True)
    notification_sms = db.Column(db.Boolean, default=False)  # для будущего
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    alerts = db.relationship('PatientAlert', back_populates='patient', cascade='all, delete-orphan')
    bookings = db.relationship('Booking', back_populates='patient', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Patient {self.phone}>'
    
    def to_dict(self):
        """Сериализация для API"""
        return {
            'id': str(self.id),
            'email': self.email,
            'email_verified': self.email_verified,
            'reputation_score': self.calculate_reputation(),
            'stats': {
                'total_bookings': self.total_bookings,
                'no_shows': self.no_show_count,
                'attended': self.attended_appointments,
            },
            'preferences': {
                'email_notifications': self.notification_email,
                'sms_notifications': self.notification_sms
            }
        }
    
    def calculate_reputation(self):
        """
        Расчет reputation score (0-100)
        
        Формула:
        - Начальный score: 50
        - No-show: -20 points
        - Late cancellation (<24h): -10 points
        - Early cancellation (>24h): -5 points
        - Attended: +5 points
        """
        if self.total_bookings == 0:
            return 50.0  # Новые пользователи - средний score
        
        score = 50.0
        score -= self.no_show_count * 20
        score -= self.late_cancellations * 10
        score -= self.early_cancellations * 5
        score += self.attended_appointments * 5
        
        return max(0, min(100, score))
    
    def can_book(self):
        """
        Проверка возможности бронирования
        
        Returns:
            tuple: (bool, str) - (можно ли бронировать, причина если нельзя)
        """
        # Проверка репутации
        if self.calculate_reputation() < 20:
            return False, "Reputation score too low"
        
        # Проверка email verification
        if not self.email_verified:
            return False, "Email not verified"
        
        return True, None


class PatientAlert(db.Model):
    """
    Терминный "будильник" пациента
    
    Пациент задает критерии, и система уведомляет при появлении подходящих слотов
    """
    __tablename__ = 'patient_alerts'
    
    # Primary Key
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    patient_id = db.Column(UUID(as_uuid=True), db.ForeignKey('patients.id'), nullable=False, index=True)
    
    # Критерии поиска
    city = db.Column(db.String(100), nullable=False, index=True)
    speciality = db.Column(db.String(50), nullable=False, index=True)
    languages = db.Column(db.Text, nullable=True)  # опционально, JSON array
    
    # Временные рамки
    date_range = db.Column(db.Text, nullable=False)  # JSON
    # Структура date_range:
    # {
    #     "from": "2025-02-01",
    #     "to": "2025-02-15"
    # }
    
    time_preferences = db.Column(db.Text, nullable=True)  # JSON array
    # Пример: ["morning", "afternoon"]
    
    # Статус
    status = db.Column(db.String(20), default='active', nullable=False, index=True)
    # Возможные значения: 'active', 'fulfilled', 'cancelled', 'expired'
    
    # Статистика уведомлений
    notifications_sent = db.Column(db.Integer, default=0)
    last_notified_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)  # автоматическая деактивация
    
    # Методы для работы с JSON полями
    @property
    def languages_list(self):
        """Получить языки как список"""
        if isinstance(self.languages, str):
            return json.loads(self.languages) if self.languages else []
        return self.languages or []
    
    @languages_list.setter
    def languages_list(self, value):
        """Установить языки как список"""
        if isinstance(value, list):
            self.languages = json.dumps(value)
        else:
            self.languages = value
    
    @property
    def time_preferences_list(self):
        """Получить предпочтения времени как список"""
        if isinstance(self.time_preferences, str):
            return json.loads(self.time_preferences) if self.time_preferences else []
        return self.time_preferences or []
    
    @time_preferences_list.setter
    def time_preferences_list(self, value):
        """Установить предпочтения времени как список"""
        if isinstance(value, list):
            self.time_preferences = json.dumps(value)
        else:
            self.time_preferences = value
    
    @property
    def date_range_dict(self):
        """Получить диапазон дат как словарь"""
        if isinstance(self.date_range, str):
            return json.loads(self.date_range)
        return self.date_range
    
    @date_range_dict.setter
    def date_range_dict(self, value):
        """Установить диапазон дат как словарь"""
        if isinstance(value, dict):
            self.date_range = json.dumps(value)
        else:
            self.date_range = value
    
    # Relationships
    patient = db.relationship('Patient', back_populates='alerts')
    
    # Индекс для быстрого поиска активных alerts
    if 'postgresql' in os.getenv('DATABASE_URL', ''):
        __table_args__ = (
            {'schema': os.getenv('DB_SCHEMA', 'public')},
            db.Index('idx_alert_active_city_speciality', 'status', 'city', 'speciality'),
        )
    else:
        __table_args__ = (
            db.Index('idx_alert_active_city_speciality', 'status', 'city', 'speciality'),
        )
    
    def __repr__(self):
        return f'<PatientAlert {self.city} - {self.speciality}>'
    
    def to_dict(self):
        """Сериализация для API"""
        return {
            'id': str(self.id),
            'criteria': {
                'city': self.city,
                'speciality': self.speciality,
                'languages': self.languages,
                'date_range': self.date_range,
                'time_preferences': self.time_preferences
            },
            'status': self.status,
            'notifications_sent': self.notifications_sent,
            'last_notified_at': self.last_notified_at.isoformat() if self.last_notified_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
    
    def is_active(self):
        """Проверка активности alert"""
        return (
            self.status == 'active' and
            self.expires_at > datetime.utcnow()
        )
    
    def should_notify(self, cooldown_minutes=60):
        """
        Проверка, нужно ли отправлять уведомление
        
        Args:
            cooldown_minutes: минимальный интервал между уведомлениями
        
        Returns:
            bool: можно ли отправлять уведомление
        """
        if not self.is_active():
            return False
        
        if self.last_notified_at is None:
            return True
        
        time_since_last = (datetime.utcnow() - self.last_notified_at).total_seconds() / 60
        return time_since_last >= cooldown_minutes
