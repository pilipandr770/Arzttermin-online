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
    
    # === NEW: Extended profile fields ===
    # Media content
    gallery_photos = db.Column(db.Text, nullable=True)  # JSON: [{url, title, order}, ...]
    video_url = db.Column(db.String(500), nullable=True)  # YouTube/Vimeo link
    virtual_tour_url = db.Column(db.String(500), nullable=True)  # 360° tour link
    
    # Services and specializations
    services = db.Column(db.Text, nullable=True)  # JSON: [{name, description, duration, price_from, category}, ...]
    
    # Team members
    team_members = db.Column(db.Text, nullable=True)  # JSON: [{doctor_id, role, photo_url, bio_short}, ...]
    
    # Equipment and technologies
    equipment = db.Column(db.Text, nullable=True)  # JSON: [{name, description, icon}, ...]
    
    # Insurance companies
    accepted_insurances = db.Column(db.Text, nullable=True)  # JSON: [{name, type: 'public/private', logo_url}, ...]
    
    # Features/Amenities
    features = db.Column(db.Text, nullable=True)  # JSON: ['wheelchair_accessible', 'parking', 'wifi', ...]
    
    # Certifications
    certifications = db.Column(db.Text, nullable=True)  # JSON: [{name, issuer, year, logo_url}, ...]
    
    # FAQ
    faq = db.Column(db.Text, nullable=True)  # JSON: [{question, answer, category, order}, ...]
    
    # Reviews and ratings statistics
    rating_avg = db.Column(db.Float, default=0.0)
    rating_count = db.Column(db.Integer, default=0)
    
    # Additional contact information
    parking_info = db.Column(db.Text, nullable=True)  # Parking information
    public_transport = db.Column(db.Text, nullable=True)  # JSON: [{type: 'bus/train/tram', line, stop, distance}, ...]
    emergency_phone = db.Column(db.String(20), nullable=True)
    whatsapp_number = db.Column(db.String(20), nullable=True)
    telegram_username = db.Column(db.String(100), nullable=True)
    
    # SEO and meta information
    meta_title = db.Column(db.String(200), nullable=True)
    meta_description = db.Column(db.Text, nullable=True)
    slug = db.Column(db.String(200), unique=True, nullable=True, index=True)  # URL-friendly name
    
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
    
    # === NEW: Helper methods for JSON fields ===
    
    @property
    def gallery_photos_list(self):
        """Get gallery photos as list"""
        if self.gallery_photos and isinstance(self.gallery_photos, str):
            try:
                return json.loads(self.gallery_photos)
            except:
                return []
        return self.gallery_photos or []
    
    @gallery_photos_list.setter
    def gallery_photos_list(self, value):
        if isinstance(value, list):
            self.gallery_photos = json.dumps(value)
    
    @property
    def services_list(self):
        """Get services as list"""
        if self.services and isinstance(self.services, str):
            try:
                return json.loads(self.services)
            except:
                return []
        return self.services or []
    
    @services_list.setter
    def services_list(self, value):
        if isinstance(value, list):
            self.services = json.dumps(value)
    
    @property
    def team_members_list(self):
        """Get team members as list"""
        if self.team_members and isinstance(self.team_members, str):
            try:
                return json.loads(self.team_members)
            except:
                return []
        return self.team_members or []
    
    @team_members_list.setter
    def team_members_list(self, value):
        if isinstance(value, list):
            self.team_members = json.dumps(value)
    
    @property
    def equipment_list(self):
        """Get equipment as list"""
        if self.equipment and isinstance(self.equipment, str):
            try:
                return json.loads(self.equipment)
            except:
                return []
        return self.equipment or []
    
    @equipment_list.setter
    def equipment_list(self, value):
        if isinstance(value, list):
            self.equipment = json.dumps(value)
    
    @property
    def accepted_insurances_list(self):
        """Get accepted insurances as list"""
        if self.accepted_insurances and isinstance(self.accepted_insurances, str):
            try:
                return json.loads(self.accepted_insurances)
            except:
                return []
        return self.accepted_insurances or []
    
    @accepted_insurances_list.setter
    def accepted_insurances_list(self, value):
        if isinstance(value, list):
            self.accepted_insurances = json.dumps(value)
    
    @property
    def features_list(self):
        """Get features as list"""
        if self.features and isinstance(self.features, str):
            try:
                return json.loads(self.features)
            except:
                return []
        return self.features or []
    
    @features_list.setter
    def features_list(self, value):
        if isinstance(value, list):
            self.features = json.dumps(value)
    
    @property
    def certifications_list(self):
        """Get certifications as list"""
        if self.certifications and isinstance(self.certifications, str):
            try:
                return json.loads(self.certifications)
            except:
                return []
        return self.certifications or []
    
    @certifications_list.setter
    def certifications_list(self, value):
        if isinstance(value, list):
            self.certifications = json.dumps(value)
    
    @property
    def faq_list(self):
        """Get FAQ as list"""
        if self.faq and isinstance(self.faq, str):
            try:
                return json.loads(self.faq)
            except:
                return []
        return self.faq or []
    
    @faq_list.setter
    def faq_list(self, value):
        if isinstance(value, list):
            self.faq = json.dumps(value)
    
    @property
    def public_transport_list(self):
        """Get public transport as list"""
        if self.public_transport and isinstance(self.public_transport, str):
            try:
                return json.loads(self.public_transport)
            except:
                return []
        return self.public_transport or []
    
    @public_transport_list.setter
    def public_transport_list(self, value):
        if isinstance(value, list):
            self.public_transport = json.dumps(value)
    
    @property
    def social_media_dict(self):
        """Get social media as dict"""
        if self.social_media and isinstance(self.social_media, str):
            try:
                return json.loads(self.social_media)
            except:
                return {}
        return self.social_media or {}
    
    @social_media_dict.setter
    def social_media_dict(self, value):
        if isinstance(value, dict):
            self.social_media = json.dumps(value)
    
    def get_profile_completeness(self):
        """Calculate profile completeness percentage"""
        score = 0
        max_score = 11
        
        if self.gallery_photos_list and len(self.gallery_photos_list) >= 3:
            score += 1
        if self.description:
            score += 1
        if self.services_list and len(self.services_list) >= 5:
            score += 1
        if self.opening_hours_dict:
            score += 1
        if self.accepted_insurances_list:
            score += 1
        if self.features_list:
            score += 1
        if self.faq_list and len(self.faq_list) >= 3:
            score += 1
        if self.parking_info:
            score += 1
        if self.public_transport_list:
            score += 1
        if self.video_url:
            score += 1
        if self.virtual_tour_url:
            score += 1
        
        return int((score / max_score) * 100)
    
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
