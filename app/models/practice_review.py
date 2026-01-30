"""
PracticeReview Model - Отзывы о праксисе
"""
from app import db
from app.models import get_table_args
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid


class PracticeReview(db.Model):
    """
    Отзыв пациента о праксисе
    
    Позволяет пациентам оставлять оценки и комментарии после визита
    """
    __tablename__ = 'practice_reviews'
    __table_args__ = get_table_args()
    
    # Primary Key
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    practice_id = db.Column(UUID(as_uuid=True), db.ForeignKey('terminfinder.practices.id'), nullable=False, index=True)
    patient_id = db.Column(UUID(as_uuid=True), db.ForeignKey('terminfinder.patients.id'), nullable=False, index=True)
    doctor_id = db.Column(UUID(as_uuid=True), db.ForeignKey('terminfinder.doctors.id'), nullable=True, index=True)  # Опционально - отзыв о конкретном враче
    booking_id = db.Column(UUID(as_uuid=True), db.ForeignKey('terminfinder.bookings.id'), nullable=True)  # Связь с бронированием
    
    # Оценки (1-5 stars)
    rating_overall = db.Column(db.Integer, nullable=False)  # Общая оценка (обязательная)
    rating_treatment = db.Column(db.Integer, nullable=True)  # Качество лечения
    rating_staff = db.Column(db.Integer, nullable=True)  # Персонал
    rating_facilities = db.Column(db.Integer, nullable=True)  # Оснащение/чистота
    rating_waiting_time = db.Column(db.Integer, nullable=True)  # Время ожидания
    
    # Отзыв
    title = db.Column(db.String(200), nullable=True)  # Заголовок отзыва
    comment = db.Column(db.Text, nullable=True)  # Комментарий
    
    # Мета информация
    visit_date = db.Column(db.Date, nullable=True)  # Дата визита
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Статус и модерация
    is_verified = db.Column(db.Boolean, default=False, nullable=False)  # Подтвержденный визит (через booking)
    is_published = db.Column(db.Boolean, default=False, nullable=False)  # Одобрен модератором
    is_flagged = db.Column(db.Boolean, default=False, nullable=False)  # Помечен как неподобающий
    flagged_reason = db.Column(db.String(500), nullable=True)  # Причина флага
    
    # Реакция практиса
    practice_response = db.Column(db.Text, nullable=True)  # Ответ от праксиса
    practice_response_at = db.Column(db.DateTime, nullable=True)  # Когда был дан ответ
    practice_response_by = db.Column(UUID(as_uuid=True), nullable=True)  # ID врача, который ответил
    
    # Полезность отзыва (для сортировки)
    helpful_count = db.Column(db.Integer, default=0, nullable=False)  # Сколько пользователей нашли полезным
    not_helpful_count = db.Column(db.Integer, default=0, nullable=False)  # Сколько нашли бесполезным
    
    # Relationships
    practice = db.relationship('Practice', backref=db.backref('reviews', lazy='dynamic'))
    patient = db.relationship('Patient', backref=db.backref('reviews', lazy='dynamic'))
    doctor = db.relationship('Doctor', backref=db.backref('reviews', lazy='dynamic'))
    
    def __repr__(self):
        return f'<PracticeReview {self.id} for Practice {self.practice_id}>'
    
    def to_dict(self, include_patient=False):
        """Сериализация для API"""
        data = {
            'id': str(self.id),
            'practice_id': str(self.practice_id),
            'ratings': {
                'overall': self.rating_overall,
                'treatment': self.rating_treatment,
                'staff': self.rating_staff,
                'facilities': self.rating_facilities,
                'waiting_time': self.rating_waiting_time,
                'average': self.average_rating
            },
            'title': self.title,
            'comment': self.comment,
            'visit_date': self.visit_date.isoformat() if self.visit_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_verified': self.is_verified,
            'helpful_count': self.helpful_count,
            'not_helpful_count': self.not_helpful_count,
        }
        
        # Ответ от праксиса
        if self.practice_response:
            data['practice_response'] = {
                'text': self.practice_response,
                'created_at': self.practice_response_at.isoformat() if self.practice_response_at else None
            }
        
        # Информация о пациенте (анонимизированная)
        if include_patient and self.patient:
            data['patient'] = {
                'name': f"{self.patient.first_name[0]}. {self.patient.last_name[:2]}***",  # Первая буква имени
                'initials': f"{self.patient.first_name[0]}.{self.patient.last_name[0]}."
            }
        
        return data
    
    @property
    def average_rating(self):
        """Средняя оценка по всем категориям"""
        ratings = [
            r for r in [
                self.rating_overall,
                self.rating_treatment,
                self.rating_staff,
                self.rating_facilities,
                self.rating_waiting_time
            ] if r is not None
        ]
        return round(sum(ratings) / len(ratings), 1) if ratings else self.rating_overall
    
    @property
    def helpfulness_score(self):
        """Показатель полезности (для сортировки)"""
        total = self.helpful_count + self.not_helpful_count
        if total == 0:
            return 0
        return (self.helpful_count - self.not_helpful_count) / total
    
    @staticmethod
    def calculate_practice_rating(practice_id):
        """Пересчитать средний рейтинг праксиса"""
        from sqlalchemy import func
        
        # Получаем средний рейтинг только опубликованных отзывов
        result = db.session.query(
            func.avg(PracticeReview.rating_overall),
            func.count(PracticeReview.id)
        ).filter(
            PracticeReview.practice_id == practice_id,
            PracticeReview.is_published == True
        ).first()
        
        avg_rating = float(result[0]) if result[0] else 0.0
        count = result[1] if result[1] else 0
        
        # Обновляем праксис
        from app.models.practice import Practice
        practice = Practice.query.get(practice_id)
        if practice:
            practice.rating_avg = round(avg_rating, 1)
            practice.rating_count = count
            db.session.commit()
        
        return avg_rating, count
