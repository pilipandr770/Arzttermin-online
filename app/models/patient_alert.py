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
    doctor_id = db.Column(UUID(as_uuid=True), db.ForeignKey('terminfinder.doctors.id'), nullable=True, index=True)
    
    # Критерии поиска
    speciality = db.Column(db.String(50), nullable=True)  # Если не указан конкретный врач
    city = db.Column(db.String(100), nullable=True)
    date_from = db.Column(db.Date, nullable=True)  # Желаемый период
    date_to = db.Column(db.Date, nullable=True)
    
    # Настройки уведомлений
    email_notifications = db.Column(db.Boolean, default=True)
    sms_notifications = db.Column(db.Boolean, default=False)  # для будущего
    
    # Статус
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Статистика
    notifications_sent = db.Column(db.Integer, default=0)
    last_notification_at = db.Column(db.DateTime, nullable=True)
    last_slot_notified_id = db.Column(UUID(as_uuid=True), nullable=True)  # Чтобы не отправлять дубли
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', back_populates='alerts')
    doctor = db.relationship('Doctor', foreign_keys=[doctor_id])
    
    def to_dict(self):
        """Сериализация для API"""
        from app.constants import SPECIALITIES
        
        doctor_info = None
        if self.doctor:
            doctor_info = {
                'id': str(self.doctor.id),
                'name': f"{self.doctor.first_name} {self.doctor.last_name}",
                'speciality': self.doctor.speciality
            }
        
        return {
            'id': str(self.id),
            'doctor': doctor_info,
            'speciality': self.speciality,
            'speciality_display': SPECIALITIES.get(self.speciality, {}).get('de', self.speciality) if self.speciality else None,
            'city': self.city,
            'date_from': self.date_from.strftime('%Y-%m-%d') if self.date_from else None,
            'date_to': self.date_to.strftime('%Y-%m-%d') if self.date_to else None,
            'is_active': self.is_active,
            'notifications_sent': self.notifications_sent,
            'last_notification_at': self.last_notification_at.isoformat() if self.last_notification_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<PatientAlert {self.id} for patient {self.patient_id}>'