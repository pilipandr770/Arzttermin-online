"""
Doctor Model - Врач
"""
from app import db
from app.models import get_table_args
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
import os
import json


class Doctor(db.Model):
    """
    Врач, работающий в практике
    
    У каждого врача свой календарь и расписание
    """
    __tablename__ = 'doctors'
    __table_args__ = get_table_args()
    
    # Primary Key
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    practice_id = db.Column(UUID(as_uuid=True), db.ForeignKey('terminfinder.practices.id'), nullable=True, index=True)
    
    # Основная информация
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    
    # Верификация
    tax_number = db.Column(db.String(50), nullable=True)  # Steuernummer
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_token = db.Column(db.String(100), nullable=True)
    
    # Специальность
    speciality = db.Column(db.String(50), nullable=False, index=True)
    # Если выбрано 'other', то заполняется custom поле
    speciality_custom = db.Column(db.String(100), nullable=True)
    speciality_approved = db.Column(db.Boolean, default=False)
    
    # Языки (массив кодов языков)
    languages = db.Column(db.Text, nullable=False, default='["de"]')
    # Пример: ['de', 'en', 'ru']
    
    # Дополнительная информация (опционально)
    photo_url = db.Column(db.String(500), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    
    # Настройки расписания
    slot_duration_minutes = db.Column(db.Integer, default=30, nullable=False)  # Длительность одного термина в минутах
    work_days = db.Column(db.Text, nullable=False, default='["monday","tuesday","wednesday","thursday","friday"]')  # Рабочие дни недели
    work_start_time = db.Column(db.Time, nullable=False, default='09:00:00')  # Время начала работы
    work_end_time = db.Column(db.Time, nullable=False, default='17:00:00')    # Время окончания работы
    
    # Статус
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Методы для работы с languages как JSON
    @property
    def languages_list(self):
        """Получить языки как список"""
        if isinstance(self.languages, str):
            return json.loads(self.languages)
        return self.languages
    
    @languages_list.setter
    def languages_list(self, value):
        """Установить языки как список"""
        if isinstance(value, list):
            self.languages = json.dumps(value)
        else:
            self.languages = value
    
    @property
    def work_days_list(self):
        """Получить рабочие дни как список"""
        if isinstance(self.work_days, str):
            return json.loads(self.work_days)
        return self.work_days
    
    @work_days_list.setter
    def work_days_list(self, value):
        """Установить рабочие дни как список"""
        if isinstance(value, list):
            self.work_days = json.dumps(value)
        else:
            self.work_days = value
    
    @property
    def name(self):
        """Полное имя врача"""
        return f"{self.first_name} {self.last_name}".strip()
    
    @name.setter
    def name(self, value):
        """Установить имя из полного имени"""
        if value:
            parts = value.split(' ', 1)
            self.first_name = parts[0]
            self.last_name = parts[1] if len(parts) > 1 else ''
        else:
            self.first_name = ''
            self.last_name = ''
    
    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Doctor {self.name}>'
    
    def to_dict(self, include_practice=False):
        """Сериализация для API"""
        from app.constants import SPECIALITIES
        
        speciality_info = SPECIALITIES.get(self.speciality, {})
        
        data = {
            'id': str(self.id),
            'name': self.name,
            'speciality': {
                'code': self.speciality,
                'name_de': speciality_info.get('de', self.speciality_custom),
                'name_en': speciality_info.get('en'),
                'icon': speciality_info.get('icon'),
                'custom': self.speciality_custom if self.speciality == 'other' else None
            },
            'languages': self.languages,
            'photo_url': self.photo_url,
            'bio': self.bio,
            'is_active': self.is_active,
            'schedule_settings': {
                'slot_duration_minutes': self.slot_duration_minutes,
                'work_days': self.work_days_list,
                'work_start_time': self.work_start_time.strftime('%H:%M') if self.work_start_time else '09:00',
                'work_end_time': self.work_end_time.strftime('%H:%M') if self.work_end_time else '17:00'
            }
        }
        
        if include_practice and self.practice:
            data['practice'] = self.practice.to_dict()
        
        return data
    
    @property
    def display_speciality(self):
        """Отображаемое название специальности"""
        from app.constants import SPECIALITIES
        
        if self.speciality == 'other' and self.speciality_custom:
            return self.speciality_custom
        
        return SPECIALITIES.get(self.speciality, {}).get('de', self.speciality)

    # Relationships
    practice = db.relationship('Practice', back_populates='doctors')
    calendar = db.relationship('Calendar', back_populates='doctor', uselist=False, cascade='all, delete-orphan')
