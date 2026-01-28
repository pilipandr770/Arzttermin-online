"""
Инициализация Flask приложения и расширений
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from celery import Celery
from config import config

# Инициализация расширений
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
jwt = JWTManager()
celery = Celery(__name__)


def create_app(config_name='default'):
    """
    Application factory pattern
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    jwt.init_app(app)
    CORS(app)
    
    # Импорт моделей для регистрации в SQLAlchemy
    from app import models
    
    # Настройка Celery
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Europe/Berlin',
        enable_utc=True,
    )
    
    # Регистрация blueprints
    from app.routes import bp as main_bp
    from app.routes import auth, practice, doctor, patient, booking, search
    from app.routes import auth as auth_module
    from app.routes.doctor import doctor_api
    from app.routes.patient import patient_api
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(auth_module.auth_web, name='auth_web')
    app.register_blueprint(practice.bp, url_prefix='/api/practice')
    app.register_blueprint(doctor_api, url_prefix='/api/doctors')
    app.register_blueprint(patient_api, url_prefix='/api/patient')
    app.register_blueprint(booking.bp, url_prefix='/api/bookings')
    app.register_blueprint(search.bp, url_prefix='/api/search')
    
    # Регистрация веб-интерфейсов (без /api префикса)
    app.register_blueprint(doctor.bp, name='doctor_web')
    app.register_blueprint(patient.bp, name='patient_web')
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200
    
    return app
