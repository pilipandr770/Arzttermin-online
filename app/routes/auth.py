"""
Маршруты аутентификации
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app.models import Patient, Doctor
from app import db
import re

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
    return render_template('auth/doctor_register.html')


# API маршруты
@bp.route('/patient/login', methods=['POST'])
def api_patient_login():
    """API: Вход пациента"""
    data = request.get_json()
    phone = data.get('phone')
    
    if not phone:
        return jsonify({'error': 'Telefonnummer erforderlich'}), 400
    
    # Простая валидация номера телефона (Германия)
    if not re.match(r'^\+49\d{10,11}$', phone):
        return jsonify({'error': 'Ungültige Telefonnummer'}), 400
    
    # Создаем или находим пациента
    patient = Patient.query.filter_by(phone=phone).first()
    if not patient:
        patient = Patient(phone=phone)
        db.session.add(patient)
        db.session.commit()
    
    # Создаем токен
    access_token = create_access_token(identity={'id': str(patient.id), 'type': 'patient'})
    refresh_token = create_refresh_token(identity={'id': str(patient.id), 'type': 'patient'})
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'patient_id': str(patient.id)
    })


@bp.route('/patient/register', methods=['POST'])
def api_patient_register():
    """API: Регистрация пациента с верификацией через Stripe"""
    data = request.get_json()
    phone = data.get('phone')
    name = data.get('name', '')
    
    if not phone:
        return jsonify({'error': 'Telefonnummer erforderlich'}), 400
    
    # Проверка существования
    existing = Patient.query.filter_by(phone=phone).first()
    if existing:
        return jsonify({'error': 'Telefonnummer bereits registriert'}), 400
    
    # Создаем пациента
    patient = Patient(phone=phone, name=name)
    db.session.add(patient)
    db.session.commit()
    
    # TODO: Интеграция с Stripe для верификации
    # Для тестирования: считаем верифицированным
    patient.stripe_customer_id = f'test_customer_{patient.id}'
    db.session.commit()
    
    return jsonify({
        'message': 'Patient erfolgreich registriert und verifiziert',
        'patient_id': str(patient.id)
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
    
    access_token = create_access_token(identity={'id': str(doctor.id), 'type': 'doctor'})
    refresh_token = create_refresh_token(identity={'id': str(doctor.id), 'type': 'doctor'})
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'doctor_id': str(doctor.id)
    })


@bp.route('/doctor/register', methods=['POST'])
def api_doctor_register():
    """API: Регистрация врача с верификацией"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    tax_number = data.get('tax_number')
    speciality = data.get('speciality')
    practice_id = data.get('practice_id')
    
    if not all([email, password, first_name, last_name, speciality]):
        return jsonify({'error': 'Alle Pflichtfelder erforderlich'}), 400
    
    # Проверка существования
    existing = Doctor.query.filter_by(email=email).first()
    if existing:
        return jsonify({'error': 'Email bereits registriert'}), 400
    
    # TODO: Верификация tax_number и Handelsregister
    
    doctor = Doctor(
        email=email,
        first_name=first_name,
        last_name=last_name,
        tax_number=tax_number,
        speciality=speciality,
        practice_id=practice_id,
        is_verified=False  # Требует верификации
    )
    doctor.set_password(password)
    
    db.session.add(doctor)
    db.session.commit()
    
    return jsonify({
        'message': 'Arzt erfolgreich registriert. Warten auf Verifizierung.',
        'doctor_id': str(doctor.id)
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
