"""
Patient и PatientAlert Models - Пациент и терминные "будильники"
"""
from app import db
from app.models import get_table_args
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
    __table_args__ = get_table_args()
    
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



