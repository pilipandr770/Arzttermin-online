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
    password_hash = db.Column(db.String(255), nullable=False)
    
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
    
    # === NEW: Extended profile fields ===
    # Professional information
    title = db.Column(db.String(50), nullable=True)  # Dr. med., Prof. Dr., Dipl.-Med.
    qualifications = db.Column(db.Text, nullable=True)  # JSON: [{degree, institution, year, country}, ...]
    
    # Career and experience
    experience_years = db.Column(db.Integer, nullable=True)  # Years of practice
    previous_positions = db.Column(db.Text, nullable=True)  # JSON: [{title, institution, location, period_from, period_to}, ...]
    
    # Specializations and focus
    treatment_focus = db.Column(db.Text, nullable=True)  # JSON: [{area, description, icon}, ...]
    subspecialities = db.Column(db.Text, nullable=True)  # JSON: [subspeciality codes]
    
    # Professional memberships
    professional_memberships = db.Column(db.Text, nullable=True)  # JSON: [{organization, role, since_year}, ...]
    
    # Publications and research
    publications = db.Column(db.Text, nullable=True)  # JSON: [{title, journal, year, link}, ...]
    
    # Consultation types availability
    consultation_types = db.Column(db.Text, nullable=True)  # JSON: ['in_person', 'video', 'phone', 'chat']
    video_consultation_url = db.Column(db.String(500), nullable=True)  # Video consultation link
    
    # Personal info for profile page
    hobbies = db.Column(db.Text, nullable=True)  # Hobbies/interests
    motto = db.Column(db.String(500), nullable=True)  # Professional motto
    
    # Contact preferences
    preferred_contact_method = db.Column(db.String(20), nullable=True)  # email/phone/whatsapp
    
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
    
    # === NEW: Helper methods for JSON fields ===
    
    @property
    def qualifications_list(self):
        """Get qualifications as list"""
        if self.qualifications and isinstance(self.qualifications, str):
            try:
                return json.loads(self.qualifications)
            except:
                return []
        return self.qualifications or []
    
    @qualifications_list.setter
    def qualifications_list(self, value):
        if isinstance(value, list):
            self.qualifications = json.dumps(value)
    
    @property
    def previous_positions_list(self):
        """Get previous positions as list"""
        if self.previous_positions and isinstance(self.previous_positions, str):
            try:
                return json.loads(self.previous_positions)
            except:
                return []
        return self.previous_positions or []
    
    @previous_positions_list.setter
    def previous_positions_list(self, value):
        if isinstance(value, list):
            self.previous_positions = json.dumps(value)
    
    @property
    def treatment_focus_list(self):
        """Get treatment focus as list"""
        if self.treatment_focus and isinstance(self.treatment_focus, str):
            try:
                return json.loads(self.treatment_focus)
            except:
                return []
        return self.treatment_focus or []
    
    @treatment_focus_list.setter
    def treatment_focus_list(self, value):
        if isinstance(value, list):
            self.treatment_focus = json.dumps(value)
    
    @property
    def subspecialities_list(self):
        """Get subspecialities as list"""
        if self.subspecialities and isinstance(self.subspecialities, str):
            try:
                return json.loads(self.subspecialities)
            except:
                return []
        return self.subspecialities or []
    
    @subspecialities_list.setter
    def subspecialities_list(self, value):
        if isinstance(value, list):
            self.subspecialities = json.dumps(value)
    
    @property
    def professional_memberships_list(self):
        """Get professional memberships as list"""
        if self.professional_memberships and isinstance(self.professional_memberships, str):
            try:
                return json.loads(self.professional_memberships)
            except:
                return []
        return self.professional_memberships or []
    
    @professional_memberships_list.setter
    def professional_memberships_list(self, value):
        if isinstance(value, list):
            self.professional_memberships = json.dumps(value)
    
    @property
    def publications_list(self):
        """Get publications as list"""
        if self.publications and isinstance(self.publications, str):
            try:
                return json.loads(self.publications)
            except:
                return []
        return self.publications or []
    
    @publications_list.setter
    def publications_list(self, value):
        if isinstance(value, list):
            self.publications = json.dumps(value)
    
    @property
    def consultation_types_list(self):
        """Get consultation types as list"""
        if self.consultation_types and isinstance(self.consultation_types, str):
            try:
                return json.loads(self.consultation_types)
            except:
                return []
        return self.consultation_types or []
    
    @consultation_types_list.setter
    def consultation_types_list(self, value):
        if isinstance(value, list):
            self.consultation_types = json.dumps(value)
    
    def get_profile_completeness(self):
        """Calculate profile completeness percentage"""
        score = 0
        max_score = 10
        
        if self.photo_url:
            score += 2  # Professional photo is important
        if self.bio and len(self.bio) > 100:
            score += 1
        if self.qualifications_list:
            score += 1
        if self.experience_years:
            score += 1
        if self.treatment_focus_list:
            score += 1
        if self.professional_memberships_list:
            score += 1
        if self.languages_list and len(self.languages_list) >= 2:
            score += 1
        if self.title:
            score += 1
        if self.motto:
            score += 1
        
        return int((score / max_score) * 100)
    
    @property
    def full_name_with_title(self):
        """Full name with professional title"""
        if self.title:
            return f"{self.title} {self.first_name} {self.last_name}".strip()
        return self.name
    
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
        from app.constants.specialities import SPECIALITIES
        
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
        from app.constants.specialities import SPECIALITIES
        
        if self.speciality == 'other' and self.speciality_custom:
            return self.speciality_custom
        
        return SPECIALITIES.get(self.speciality, {}).get('de', self.speciality)

    # Relationships
    practice = db.relationship('Practice', back_populates='doctors')
    calendar = db.relationship('Calendar', back_populates='doctor', uselist=False, cascade='all, delete-orphan')
    calendar_integrations = db.relationship('CalendarIntegration', back_populates='doctor', cascade='all, delete-orphan')
