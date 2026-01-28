"""
Calendar и TimeSlot Models - Календарь и временные слоты
"""
from app import db
from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import os
import json


class Calendar(db.Model):
    """
    Календарь врача
    
    Определяет рабочие часы и правила создания слотов
    """
    __tablename__ = 'calendars'
    # Schema только для PostgreSQL
    if 'postgresql' in os.getenv('DATABASE_URL', ''):
        __table_args__ = {'schema': os.getenv('DB_SCHEMA', 'public')}
    
    # Primary Key
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    doctor_id = db.Column(UUID(as_uuid=True), db.ForeignKey('doctors.id'), nullable=False, unique=True, index=True)
    
    # Рабочие часы (JSON структура)
    working_hours = db.Column(db.Text, nullable=False)
    # Структура working_hours:
    # {
    #     "monday": [["09:00", "13:00"], ["14:00", "18:00"]],
    #     "tuesday": [["09:00", "13:00"], ["14:00", "18:00"]],
    #     "wednesday": [],  # выходной
    #     "thursday": [["09:00", "13:00"], ["14:00", "18:00"]],
    #     "friday": [["09:00", "13:00"], ["14:00", "18:00"]],
    #     "saturday": [["09:00", "13:00"]],
    #     "sunday": []  # выходной
    # }
    
    # Настройки слотов
    slot_duration = db.Column(db.Integer, default=30, nullable=False)  # минут
    buffer_time = db.Column(db.Integer, default=5, nullable=False)  # минут между слотами
    
    # Настройки бронирования
    max_advance_booking_days = db.Column(db.Integer, default=90)  # макс за сколько дней можно бронировать
    min_advance_booking_hours = db.Column(db.Integer, default=2)  # мин за сколько часов можно бронировать
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Методы для работы с working_hours как JSON
    @property
    def working_hours_dict(self):
        """Получить рабочие часы как словарь"""
        if isinstance(self.working_hours, str):
            return json.loads(self.working_hours)
        return self.working_hours
    
    @working_hours_dict.setter
    def working_hours_dict(self, value):
        """Установить рабочие часы как словарь"""
        if isinstance(value, dict):
            self.working_hours = json.dumps(value)
        else:
            self.working_hours = value
    
    # Relationships
    doctor = db.relationship('Doctor', back_populates='calendar')
    time_slots = db.relationship('TimeSlot', back_populates='calendar', cascade='all, delete-orphan')
    time_slots = db.relationship('TimeSlot', back_populates='calendar', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Calendar for Doctor {self.doctor_id}>'
    
    def to_dict(self):
        """Сериализация для API"""
        return {
            'id': str(self.id),
            'doctor_id': str(self.doctor_id),
            'working_hours': self.working_hours,
            'slot_duration': self.slot_duration,
            'buffer_time': self.buffer_time,
            'booking_settings': {
                'max_advance_days': self.max_advance_booking_days,
                'min_advance_hours': self.min_advance_booking_hours
            }
        }
    
    def generate_slots(self, date_from, date_to):
        """
        Генерация слотов на период
        
        Args:
            date_from: datetime.date - начало периода
            date_to: datetime.date - конец периода
        
        Returns:
            list of TimeSlot objects (не сохраняет в БД, только создает)
        """
        slots = []
        current_date = date_from
        
        # Парсим working_hours из JSON
        try:
            working_hours = json.loads(self.working_hours) if isinstance(self.working_hours, str) else self.working_hours
        except:
            working_hours = {}
        
        while current_date <= date_to:
            # Определяем день недели
            weekday = current_date.strftime('%A').lower()
            
            # Получаем рабочие часы для этого дня
            day_config = working_hours.get(weekday, {})
            if not day_config or 'start' not in day_config or 'end' not in day_config:
                current_date += timedelta(days=1)
                continue
            
            start_time_str = day_config['start']
            end_time_str = day_config['end']
            
            # Парсим время
            start_hour, start_minute = map(int, start_time_str.split(':'))
            end_hour, end_minute = map(int, end_time_str.split(':'))
            
            current_time = datetime.combine(
                current_date,
                datetime.min.time().replace(hour=start_hour, minute=start_minute)
            )
            end_time = datetime.combine(
                current_date,
                datetime.min.time().replace(hour=end_hour, minute=end_minute)
            )
            
            # Генерируем слоты
            while current_time + timedelta(minutes=self.slot_duration) <= end_time:
                slot = TimeSlot(
                    calendar_id=self.id,
                    start_time=current_time,
                    end_time=current_time + timedelta(minutes=self.slot_duration),
                    status='available'
                )
                slots.append(slot)
                
                # Следующий слот с учетом buffer time
                current_time += timedelta(minutes=self.slot_duration + self.buffer_time)
            
            current_date += timedelta(days=1)
        
        return slots


class TimeSlot(db.Model):
    """
    Временной слот для бронирования
    
    Каждый слот может быть: free, booked, blocked
    """
    __tablename__ = 'time_slots'
    
    # Primary Key
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    calendar_id = db.Column(UUID(as_uuid=True), db.ForeignKey('calendars.id'), nullable=False, index=True)
    
    # Время
    start_time = db.Column(db.DateTime, nullable=False, index=True)
    end_time = db.Column(db.DateTime, nullable=False)
    
    # Статус
    status = db.Column(db.String(20), default='available', nullable=False, index=True)
    # Возможные значения: 'available', 'booked', 'blocked'
    
    # Если заблокирован вручную (обед, meeting и т.д.)
    block_reason = db.Column(db.String(200), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    calendar = db.relationship('Calendar', back_populates='time_slots')
    booking = db.relationship('Booking', back_populates='timeslot', uselist=False)
    
    # Индекс для быстрого поиска свободных слотов
    __table_args__ = (
        db.Index('idx_slot_calendar_time_status', 'calendar_id', 'start_time', 'status'),
    )
    
    def __repr__(self):
        return f'<TimeSlot {self.start_time} - {self.status}>'
    
    def to_dict(self, include_doctor=False):
        """Сериализация для API"""
        data = {
            'id': str(self.id),
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'duration_minutes': int((self.end_time - self.start_time).total_seconds() / 60) if self.end_time and self.start_time else None,
        }
        
        if include_doctor and self.calendar and self.calendar.doctor:
            data['doctor'] = self.calendar.doctor.to_dict(include_practice=True)
        
        return data
    
    def is_available(self):
        """Проверка доступности слота"""
        return self.status == 'available' and self.start_time > datetime.utcnow()
    
    def can_be_cancelled(self, hours_before=1):
        """Проверка возможности отмены"""
        if not self.booking:
            return False
        
        time_until_appointment = (self.start_time - datetime.utcnow()).total_seconds() / 3600
        return time_until_appointment >= hours_before
