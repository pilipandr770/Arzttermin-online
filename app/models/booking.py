"""
Booking Model - Бронирование термина
"""
from app import db
from app.models import get_table_args
from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID
import uuid
import string
import random
import os


class Booking(db.Model):
    """
    Бронирование термина
    
    Связывает пациента со слотом через Stripe оплату
    """
    __tablename__ = 'bookings'
    __table_args__ = get_table_args()
    
    # Primary Key
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    timeslot_id = db.Column(UUID(as_uuid=True), db.ForeignKey('terminfinder.time_slots.id'), nullable=False, unique=True, index=True)
    patient_id = db.Column(UUID(as_uuid=True), db.ForeignKey('terminfinder.patients.id'), nullable=False, index=True)
    
    # Статус
    status = db.Column(db.String(20), default='confirmed', nullable=False, index=True)
    # Возможные значения: 'confirmed', 'cancelled', 'completed', 'no_show'
    
    # Payment информация
    payment_intent_id = db.Column(db.String(100), nullable=False, unique=True)
    amount_paid = db.Column(db.Numeric(10, 2), nullable=False)  # €10.00
    refund_amount = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    
    # Booking код для отмены
    booking_code = db.Column(db.String(8), unique=True, nullable=False, index=True)
    
    # Правила отмены
    cancellable_until = db.Column(db.DateTime, nullable=False)
    
    # Информация об отмене
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancelled_by = db.Column(db.String(20), nullable=True)  # 'patient' or 'practice'
    cancellation_reason = db.Column(db.Text, nullable=True)
    
    # Post-appointment информация
    attended = db.Column(db.Boolean, nullable=True)  # None до окончания термина
    rating = db.Column(db.Integer, nullable=True)  # 1-5 звезд
    review = db.Column(db.Text, nullable=True)
    
    # Reminders
    reminder_sent = db.Column(db.Boolean, default=False)
    reminder_sent_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    confirmed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    timeslot = db.relationship('TimeSlot', back_populates='booking')
    patient = db.relationship('Patient', back_populates='bookings')
    
    def __repr__(self):
        return f'<Booking {self.booking_code} - {self.status}>'
    
    @staticmethod
    def generate_booking_code():
        """Генерация уникального кода бронирования (8 символов)"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    def to_dict(self, include_details=False):
        """Сериализация для API"""
        data = {
            'id': str(self.id),
            'booking_code': self.booking_code,
            'status': self.status,
            'amount_paid': float(self.amount_paid),
            'refund_amount': float(self.refund_amount),
            'cancellable': self.can_be_cancelled(),
            'cancellable_until': self.cancellable_until.isoformat() if self.cancellable_until else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        
        if include_details:
            data['timeslot'] = self.timeslot.to_dict(include_doctor=True) if self.timeslot else None
            data['patient'] = {
                'email': self.patient.email
            } if self.patient else None
            
            if self.cancelled_at:
                data['cancellation'] = {
                    'cancelled_at': self.cancelled_at.isoformat(),
                    'cancelled_by': self.cancelled_by,
                    'reason': self.cancellation_reason
                }
            
            if self.rating:
                data['feedback'] = {
                    'rating': self.rating,
                    'review': self.review
                }
        
        return data
    
    def can_be_cancelled(self):
        """
        Проверка возможности отмены
        
        Returns:
            bool: можно ли отменить бронь
        """
        if self.status != 'confirmed':
            return False
        
        return datetime.utcnow() < self.cancellable_until
    
    def calculate_refund_amount(self):
        """
        Расчет суммы возврата при отмене
        
        Returns:
            Decimal: сумма возврата
        """
        if self.status != 'confirmed':
            return 0
        
        time_until_appointment = self.timeslot.start_time - datetime.utcnow()
        hours_until = time_until_appointment.total_seconds() / 3600
        
        # Более 24 часов - полный возврат
        if hours_until >= 24:
            return self.amount_paid
        
        # 1-24 часа - 50% возврат
        elif hours_until >= 1:
            return self.amount_paid * 0.5
        
        # Менее часа - без возврата
        else:
            return 0
    
    def get_cancellation_policy_text(self):
        """
        Текст политики отмены для пациента
        
        Returns:
            str: описание политики
        """
        time_until = self.timeslot.start_time - datetime.utcnow()
        hours_until = time_until.total_seconds() / 3600
        
        if hours_until >= 24:
            return "Vollständige Rückerstattung (10,00€)"
        elif hours_until >= 1:
            return "50% Rückerstattung (5,00€)"
        else:
            return "Keine Rückerstattung möglich"
    
    def mark_attended(self, attended=True):
        """Отметить посещение/неявку"""
        self.attended = attended
        
        if attended:
            self.status = 'completed'
            self.patient.attended_appointments += 1
        else:
            self.status = 'no_show'
            self.patient.no_show_count += 1
        
        db.session.commit()
    
    def needs_reminder(self):
        """
        Проверка, нужно ли отправить напоминание
        
        Returns:
            bool: нужно ли напоминание
        """
        if self.status != 'confirmed' or self.reminder_sent:
            return False
        
        # Напоминание за 24 часа
        time_until = self.timeslot.start_time - datetime.utcnow()
        hours_until = time_until.total_seconds() / 3600
        
        # Окно для отправки: 24h ± 15 минут
        return 23.75 <= hours_until <= 24.25
