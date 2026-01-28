"""
PatientAlert Model - Уведомления пациентов о свободных слотах
"""
from app import db
from app.models import get_table_args
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid
import os


class PatientAlert(db.Model):
    """
    "Будильник" для пациента - уведомление о свободных слотах
    
    Пациент может подписаться на уведомления для определенных критериев поиска
    """
    __tablename__ = 'patient_alerts'
    __table_args__ = get_table_args()
    
    # Primary Key
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    patient_id = db.Column(UUID(as_uuid=True), db.ForeignKey('terminfinder.patients.id'), nullable=False, index=True)
    
    # Критерии поиска (JSON для гибкости)
    search_criteria = db.Column(db.JSON, nullable=False)
    # Структура search_criteria:
    # {
    #     'city': 'München',
    #     'speciality': 'Hausarzt',
    #     'max_distance_km': 10,
    #     'preferred_times': ['morning', 'afternoon'],
    #     'max_price': 50.00
    # }
    
    # Настройки уведомлений
    email_notifications = db.Column(db.Boolean, default=True)
    sms_notifications = db.Column(db.Boolean, default=False)  # для будущего
    
    # Статус
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Статистика
    notifications_sent = db.Column(db.Integer, default=0)
    last_notification_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', back_populates='alerts')
    
    def __repr__(self):
        return f'<PatientAlert {self.id} for {self.patient.email}>'