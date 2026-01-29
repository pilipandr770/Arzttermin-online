"""
Маршруты аутентификации
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from app.models import Patient, Doctor, Practice
from app import db
from app.constants import SPECIALITIES
import re
import uuid
from datetime import datetime

bp = Blueprint('auth', __name__)
auth_web = Blueprint('auth_web', __name__)


# Веб-маршруты для рендеринга страниц
@auth_web.route('/patient/login')
def patient_login():
    """Страница входа для пациентов"""
    return render_template('auth/patient_login.html')


@auth_web.route('/patient/register')
def patient_register():
    """Страница регистрации для пациентов"""
    return render_template('auth/patient_register.html')


@auth_web.route('/doctor/login')
def doctor_login():
    """Страница входа для врачей"""
    return render_template('auth/doctor_login.html')


@auth_web.route('/doctor/register')
def doctor_register():
    """Страница регистрации для врачей"""
    return render_template('auth/doctor_register.html', specialities=SPECIALITIES)


# API маршруты
@bp.route('/patient/login', methods=['POST'])
def api_patient_login():
    """API: Вход пациента"""
    data = request.get_json()
    phone = data.get('phone')
    
    if not phone:
        return jsonify({'error': 'Telefonnummer erforderlich'}), 400
    
    # Для разработки - убираем валидацию телефона
    
    # Создаем или находим пациента
    patient = Patient.query.filter_by(phone=phone).first()
    if not patient:
        patient = Patient(phone=phone)
        db.session.add(patient)
        db.session.commit()
    
    # Создаем токен
    access_token = create_access_token(identity=str(patient.id), additional_claims={'type': 'patient'})
    refresh_token = create_refresh_token(identity=str(patient.id), additional_claims={'type': 'patient'})
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'patient_id': str(patient.id)
    })


@bp.route('/patient/register', methods=['POST'])
def api_patient_register():
    """API: Регистрация пациента"""
    data = request.get_json()
    phone = data.get('phone', '')
    name = data.get('name', '')
    
    # Для разработки - убираем все проверки
    
    # Создаем пациента (даже если такой телефон уже есть)
    patient = Patient(phone=phone, name=name)
    db.session.add(patient)
    db.session.commit()
    
    # Для тестирования: считаем верифицированным
    patient.stripe_customer_id = f'test_customer_{patient.id}'
    db.session.commit()
    
    # Создаем токены
    access_token = create_access_token(identity=str(patient.id), additional_claims={'type': 'patient'})
    refresh_token = create_refresh_token(identity=str(patient.id), additional_claims={'type': 'patient'})
    
    return jsonify({
        'message': 'Patient erfolgreich registriert',
        'patient_id': str(patient.id),
        'access_token': access_token,
        'refresh_token': refresh_token
    })


@bp.route('/doctor/login', methods=['POST'])
def api_doctor_login():
    """API: Вход врача"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email und Passwort erforderlich'}), 400
    
    doctor = Doctor.query.filter_by(email=email).first()
    if not doctor or not doctor.check_password(password):
        return jsonify({'error': 'Ungültige Anmeldedaten'}), 401
    
    access_token = create_access_token(identity=str(doctor.id), additional_claims={'type': 'doctor'})
    refresh_token = create_refresh_token(identity=str(doctor.id), additional_claims={'type': 'doctor'})
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'doctor_id': str(doctor.id)
    })


@bp.route('/practice/register', methods=['POST'])
def api_practice_register():
    """API: Регистрация практики"""
    data = request.get_json()
    name = data.get('name', '')
    vat_number = data.get('vat_number', '')
    owner_email = data.get('owner_email', '')
    phone = data.get('phone', '')
    address = data.get('address', '')
    
    # Для разработки - убираем все проверки
    
    # Создаем практику
    practice = Practice(
        name=name,
        vat_number=vat_number,
        owner_email=owner_email,
        phone=phone,
        address=address,
        verified=True,  # Для разработки - автоматически верифицируем
        verified_at=datetime.utcnow()
    )
    
    db.session.add(practice)
    db.session.commit()
    
    return jsonify({
        'message': 'Praxis erfolgreich registriert',
        'practice_id': str(practice.id)
    })


@bp.route('/doctor/register', methods=['POST'])
def api_doctor_register():
    """API: Регистрация врача"""
    data = request.get_json()
    email = data.get('email', '')
    password = data.get('password', '')
    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')
    tax_number = data.get('tax_number', '')
    speciality = data.get('speciality', 'general_practitioner')
    practice_id_str = data.get('practice_id', '')
    
    # Для разработки - убираем все проверки, кроме основных полей
    if not email or not password or not first_name or not last_name:
        return jsonify({'error': 'Email, Passwort, Vorname und Nachname erforderlich'}), 400
    
    practice_id = None
    if practice_id_str:
        # Обработка practice_id если предоставлен
        try:
            practice_id = uuid.UUID(practice_id_str)
        except ValueError:
            return jsonify({'error': 'Invalid Practice ID'}), 400
        
        # Проверяем, существует ли практика
        practice = Practice.query.get(practice_id)
        if not practice:
            return jsonify({'error': 'Practice not found'}), 404
    
    # Создаем врача (даже если такой email уже есть)
    doctor = Doctor(
        email=email,
        first_name=first_name,
        last_name=last_name,
        tax_number=tax_number,
        speciality=speciality,
        practice_id=practice_id,
        is_verified=True  # Для разработки - автоматически верифицируем
    )
    doctor.set_password(password)
    
    db.session.add(doctor)
    db.session.commit()
    
    # Создаем календарь для врача
    from app.models import Calendar
    import json
    from datetime import datetime, timedelta
    from app.models import TimeSlot
    
    # Создаем календарь с базовыми настройками
    working_hours = {
        'monday': [['09:00', '17:00']],
        'tuesday': [['09:00', '17:00']],
        'wednesday': [['09:00', '17:00']],
        'thursday': [['09:00', '17:00']],
        'friday': [['09:00', '17:00']],
        'saturday': [],
        'sunday': []
    }
    
    calendar = Calendar(
        doctor_id=doctor.id,
        working_hours=json.dumps(working_hours),
        slot_duration=30,
        buffer_time=5,
        max_advance_booking_days=30,
        min_advance_booking_hours=24
    )
    db.session.add(calendar)
    db.session.commit()
    
    # Генерируем слоты на следующие 7 дней
    today = datetime.utcnow().date()
    slots_created = 0
    
    for day_offset in range(7):
        current_date = today + timedelta(days=day_offset)
        
        # Пропускаем выходные
        if current_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            continue
        
        # Генерируем слоты с 9:00 до 17:00
        current_time = datetime.combine(current_date, datetime.strptime('09:00', '%H:%M').time())
        end_time = datetime.combine(current_date, datetime.strptime('17:00', '%H:%M').time())
        
        while current_time < end_time:
            slot_end = current_time + timedelta(minutes=30)
            
            slot = TimeSlot(
                calendar_id=calendar.id,
                start_time=current_time,
                end_time=slot_end,
                status='available'
            )
            
            db.session.add(slot)
            slots_created += 1
            
            current_time = slot_end
    
    db.session.commit()
    
    return jsonify({
        'message': 'Arzt erfolgreich registriert',
        'doctor_id': str(doctor.id),
        'calendar_created': True,
        'slots_created': slots_created
    })


@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
@auth_web.route('/js-test')
def js_test():
    """Тестовая страница для проверки JavaScript и браузерных функций"""
    return render_template('js_test.html')


@auth_web.route('/browser-test')
def browser_test():
    """Тестовая страница для проверки localStorage и Bootstrap"""
    return render_template('browser_test.html')


def refresh_token():
    """Обновление access токена"""
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({'access_token': access_token})
