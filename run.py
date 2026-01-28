"""
TerminFinder MVP - Entry Point
Точка входа для запуска Flask приложения
"""
import os
import json
from app import create_app, db
from app.models import *  # noqa
from create_test_doctor_data import create_test_doctor_data

# Создаем приложение
env = os.getenv('FLASK_ENV', 'development')
app = create_app(env)


@app.shell_context_processor
def make_shell_context():
    """
    Добавляет db и models в Flask shell context
    Для использования: flask shell
    """
    return {
        'db': db,
        'Practice': Practice,
        'Doctor': Doctor,
        'Calendar': Calendar,
        'TimeSlot': TimeSlot,
        'Patient': Patient,
        'PatientAlert': PatientAlert,
        'Booking': Booking,
    }


@app.cli.command()
def init_db():
    """
    Инициализация базы данных с schema
    Usage: flask init-db
    """
    from app import db
    from sqlalchemy import text
    import os
    
    # Создаем schema если нужно
    schema = os.getenv('DB_SCHEMA', 'public')
    if schema != 'public':
        # Для PostgreSQL создаем schema
        with db.engine.connect() as conn:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS {schema}'))
            conn.commit()
    
    db.create_all()
    print(f'✅ Database initialized with schema: {schema}')


@app.cli.command()
def seed_db():
    """
    Заполнение базы тестовыми данными
    Usage: flask seed-db
    """
    from datetime import datetime, timedelta
    
    # Создать тестовую практику
    test_practice = Practice(
        name='Zahnarztpraxis Dr. Müller',
        vat_number='DE123456789',
        owner_email='owner@praxis-muller.de',
        phone='+49891234567',
        address=json.dumps({
            'street': 'Maximilianstraße 10',
            'plz': '80539',
            'city': 'München',
            'bundesland': 'Bayern',
            'country': 'Deutschland'
        }),
        latitude=48.1392,
        longitude=11.5803,
        verified=True,
        verified_at=datetime.utcnow()
    )
    
    db.session.add(test_practice)
    db.session.commit()
    
    # Создать тестового врача
    test_doctor = Doctor(
        practice_id=test_practice.id,
        first_name='Anna',
        last_name='Schmidt',
        email='doctor@test.com',
        speciality='general_practitioner',
        languages=['de', 'en', 'ru'],
        is_active=True,
        is_verified=True
    )
    test_doctor.set_password('password123')
    
    db.session.add(test_doctor)
    db.session.commit()
    
    # Создать календарь
    test_calendar = Calendar(
        doctor_id=test_doctor.id,
        working_hours=json.dumps({
            'monday': [['09:00', '13:00'], ['14:00', '18:00']],
            'tuesday': [['09:00', '13:00'], ['14:00', '18:00']],
            'wednesday': [['09:00', '13:00']],
            'thursday': [['09:00', '13:00'], ['14:00', '18:00']],
            'friday': [['09:00', '13:00'], ['14:00', '18:00']],
            'saturday': [],
            'sunday': []
        }),
        slot_duration=30,
        buffer_time=5
    )
    
    db.session.add(test_calendar)
    db.session.commit()
    
    # Генерировать слоты на 2 недели вперед
    today = datetime.utcnow().date()
    slots = test_calendar.generate_slots(
        date_from=today + timedelta(days=1),
        date_to=today + timedelta(days=14)
    )
    
    db.session.bulk_save_objects(slots)
    db.session.commit()
    
    print(f'✅ Test data created!')
    print(f'   Practice: {test_practice.name}')
    print(f'   Doctor: {test_doctor.name}')
    print(f'   Slots generated: {len(slots)}')


@app.cli.command('create-test-doctor')
def create_test_doctor():
    """Create test doctor with calendar and slots"""
    create_test_doctor_data()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
