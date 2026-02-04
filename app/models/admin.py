"""
Admin Model - Администратор платформы
"""
from app import db
from app.models import get_table_args
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid
import bcrypt


class Admin(db.Model):
    """
    Администратор платформы TerminFinder
    
    Полный доступ к управлению пользователями, верификации, платежами
    """
    __tablename__ = 'admins'
    __table_args__ = get_table_args()
    
    # Primary Key
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Основная информация
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Роли и права доступа
    role = db.Column(db.String(50), nullable=False, default='admin')
    # Roles: 'super_admin', 'admin', 'moderator'
    
    permissions = db.Column(db.ARRAY(db.String), nullable=True, default=[])
    # Array: ['manage_users', 'manage_payments', 'manage_verifications', 'view_analytics']
    
    # Статус
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Безопасность
    last_login = db.Column(db.DateTime, nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime, nullable=True)
    
    # Двухфакторная аутентификация
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """Хешировать и сохранить пароль"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Проверить пароль"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    @property
    def permissions_list(self):
        """Получить список прав доступа"""
        return self.permissions if self.permissions else []
    
    @permissions_list.setter
    def permissions_list(self, value):
        """Установить список прав доступа"""
        self.permissions = value
    
    def has_permission(self, permission):
        """Проверить наличие конкретного права"""
        if self.role == 'super_admin':
            return True
        return permission in self.permissions_list
    
    def to_dict(self):
        """Сериализация для API"""
        return {
            'id': str(self.id),
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'permissions': self.permissions_list,
            'is_active': self.is_active,
            'two_factor_enabled': self.two_factor_enabled,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Admin {self.username} ({self.role})>'
