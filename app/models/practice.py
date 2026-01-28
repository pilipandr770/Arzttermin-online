"""
Practice Model - Медицинская практика (Praxis)
"""
from app import db
from app.models import get_table_args
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import os
import json


class Practice(db.Model):
    """
    Медицинская практика (Praxis)
    
    Это основная сущность для B2B стороны.
    Каждая практика имеет владельца, врачей, календари и т.д.
    """
    __tablename__ = 'practices'
    __table_args__ = get_table_args()
    
    # Primary Key
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Основная информация
    name = db.Column(db.String(200), nullable=False)
    vat_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    handelsregister_nr = db.Column(db.String(50), nullable=True)
    
    # Контакты
    owner_email = db.Column(db.String(120), nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    
    # Адрес (хранится как JSON для гибкости)
    address = db.Column(db.Text, nullable=False)
    # Структура address:
    # {
    #     'street': 'Maximilianstraße 10',
    #     'plz': '80539',
    #     'city': 'München',
    #     'bundesland': 'Bayern',
    #     'country': 'Deutschland'
    # }
    
    # Геолокация (для поиска по расстоянию)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
    # Дополнительная информация для пациентов
    website = db.Column(db.String(500), nullable=True)
    google_business_url = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)  # Описание практики
    opening_hours = db.Column(db.Text, nullable=True)  # JSON с часами работы
    # Структура opening_hours:
    # {
    #     'monday': {'open': '08:00', 'close': '18:00'},
    #     'tuesday': {'open': '08:00', 'close': '18:00'},
    #     ...
    # }
    social_media = db.Column(db.Text, nullable=True)  # JSON с социальными сетями
    # Структура social_media:
    # {
    #     'facebook': 'https://facebook.com/...',
    #     'instagram': 'https://instagram.com/...',
    #     'linkedin': 'https://linkedin.com/...'
    # }
    photos = db.Column(db.Text, nullable=True)  # JSON массив URL фотографий
    
    # Статус верификации
    verified = db.Column(db.Boolean, default=False, nullable=False)
    verified_at = db.Column(db.DateTime, nullable=True)
    
    # Методы для работы с address как JSON
    @property
    def address_dict(self):
        """Получить адрес как словарь"""
        if not self.address:
            return {}
        if isinstance(self.address, str):
            try:
                return json.loads(self.address)
            except (json.JSONDecodeError, ValueError):
                # Если адрес - просто текст, возвращаем пустой словарь
                return {'raw': self.address}
        return self.address if isinstance(self.address, dict) else {}
    
    @address_dict.setter
    def address_dict(self, value):
        """Установить адрес как словарь"""
        if isinstance(value, dict):
            self.address = json.dumps(value)
        else:
            self.address = value
    
    # Статистика (для аналитики)
    total_appointments = db.Column(db.Integer, default=0)
    average_rating = db.Column(db.Float, default=0.0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    doctors = db.relationship('Doctor', back_populates='practice', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Practice {self.name}>'
    
    def to_dict(self):
        """Сериализация для API"""
        return {
            'id': str(self.id),
            'name': self.name,
            'vat_number': self.vat_number,
            'phone': self.phone,
            'address': self.address,
            'location': {
                'latitude': self.latitude,
                'longitude': self.longitude
            } if self.latitude and self.longitude else None,
            'verified': self.verified,
            'stats': {
                'total_appointments': self.total_appointments,
                'average_rating': round(self.average_rating, 2)
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    @property
    def full_address_string(self):
        """Полный адрес одной строкой"""
        addr = self.address_dict
        return f"{addr['street']}, {addr['plz']} {addr['city']}"
    
    @property
    def opening_hours_dict(self):
        """Получить часы работы как словарь"""
        if self.opening_hours and isinstance(self.opening_hours, str):
            return json.loads(self.opening_hours)
        return self.opening_hours or {}
    
    @opening_hours_dict.setter
    def opening_hours_dict(self, value):
        """Установить часы работы как словарь"""
        if isinstance(value, dict):
            self.opening_hours = json.dumps(value)
        else:
            self.opening_hours = value
    
    @property
    def social_media_dict(self):
        """Получить социальные сети как словарь"""
        if self.social_media and isinstance(self.social_media, str):
            return json.loads(self.social_media)
        return self.social_media or {}
    
    @social_media_dict.setter
    def social_media_dict(self, value):
        """Установить социальные сети как словарь"""
        if isinstance(value, dict):
            self.social_media = json.dumps(value)
        else:
            self.social_media = value
    
    @property
    def photos_list(self):
        """Получить фотографии как список"""
        if self.photos and isinstance(self.photos, str):
            return json.loads(self.photos)
        return self.photos or []
    
    @photos_list.setter
    def photos_list(self, value):
        """Установить фотографии как список"""
        if isinstance(value, list):
            self.photos = json.dumps(value)
        else:
            self.photos = value
    
    # Relationships
    doctors = db.relationship('Doctor', back_populates='practice', cascade='all, delete-orphan')
