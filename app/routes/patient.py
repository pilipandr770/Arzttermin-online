"""
Маршруты пациентов
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Patient, Booking, Doctor, Calendar, TimeSlot, PatientAlert
from app import db
import uuid
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
import random
import string

bp = Blueprint('patient', __name__, url_prefix='/patient')
patient_api = Blueprint('patient_api', __name__)


@bp.route('/dashboard')
def dashboard():
    """Дашборд пациента - рендерим страницу, данные загружаем через JS"""
    # Проверяем токен через JavaScript на клиенте
    return render_template('patient/dashboard.html')
    
@patient_api.route('/dashboard')
@jwt_required()
def api_dashboard():
    """API для получения данных дашборда пациента"""
    identity = get_jwt_identity()
    if identity.get('type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    patient = Patient.query.get(uuid.UUID(identity['id']))
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Получаем активные бронирования
    active_bookings = Booking.query.filter_by(
        patient_id=patient.id,
        status='confirmed'
    ).order_by(Booking.created_at.desc()).limit(5).all()
    
    return jsonify({
        'patient': {
            'id': str(patient.id),
            'name': patient.name,
            'phone': patient.phone,
            'total_bookings': patient.total_bookings,
            'attended_appointments': patient.attended_appointments
        },
        'active_bookings': [{
            'id': str(booking.id),
            'doctor_name': booking.timeslot.calendar.doctor.first_name + ' ' + booking.timeslot.calendar.doctor.last_name if booking.timeslot and booking.timeslot.calendar and booking.timeslot.calendar.doctor else 'Unknown',
            'practice_name': booking.timeslot.calendar.doctor.practice.name if booking.timeslot and booking.timeslot.calendar and booking.timeslot.calendar.doctor and booking.timeslot.calendar.doctor.practice else 'Unknown',
            'date': booking.timeslot.start_time.strftime('%Y-%m-%d') if booking.timeslot else '',
            'time': booking.timeslot.start_time.strftime('%H:%M') if booking.timeslot else '',
            'status': booking.status
        } for booking in active_bookings]
    })


@patient_api.route('/profile')
@jwt_required()
def api_profile():
    """API для получения данных профиля пациента"""
    identity = get_jwt_identity()
    if identity.get('type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    patient = Patient.query.get(uuid.UUID(identity['id']))
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    return jsonify({
        'patient': {
            'id': str(patient.id),
            'name': patient.name,
            'phone': patient.phone,
            'total_bookings': patient.total_bookings,
            'attended_appointments': patient.attended_appointments
        }
    })


@patient_api.route('/bookings')
@jwt_required()
def api_bookings():
    """API для получения истории бронирований пациента"""
    identity = get_jwt_identity()
    if identity.get('type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    patient = Patient.query.get(uuid.UUID(identity['id']))
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Получаем все бронирования пациента
    all_bookings = Booking.query.filter_by(
        patient_id=patient.id
    ).order_by(Booking.created_at.desc()).all()
    
    return jsonify({
        'bookings': [{
            'id': str(booking.id),
            'doctor_name': booking.timeslot.calendar.doctor.first_name + ' ' + booking.timeslot.calendar.doctor.last_name if booking.timeslot and booking.timeslot.calendar and booking.timeslot.calendar.doctor else 'Unknown',
            'practice_name': booking.timeslot.calendar.doctor.practice.name if booking.timeslot and booking.timeslot.calendar and booking.timeslot.calendar.doctor and booking.timeslot.calendar.doctor.practice else 'Unknown',
            'speciality': booking.timeslot.calendar.doctor.speciality if booking.timeslot and booking.timeslot.calendar and booking.timeslot.calendar.doctor else 'Unknown',
            'date': booking.timeslot.start_time.strftime('%Y-%m-%d') if booking.timeslot else '',
            'time': booking.timeslot.start_time.strftime('%H:%M') if booking.timeslot else '',
            'status': booking.status,
            'created_at': booking.created_at.strftime('%Y-%m-%d %H:%M') if booking.created_at else ''
        } for booking in all_bookings]
    })


@bp.route('/profile')
def profile():
    """Профиль пациента"""
    # Проверяем токен через JavaScript на клиенте
    return render_template('patient/profile.html')


@bp.route('/bookings')
def bookings():
    """История бронирований пациента"""
    # Проверяем токен через JavaScript на клиенте
    return render_template('patient/bookings.html')


@bp.route('/search')
def search():
    """Страница поиска врачей"""
    from app.constants import SPECIALITIES
    return render_template('patient/search.html', specialities=SPECIALITIES)


@bp.route('/calendar')
def calendar():
    """Календарь доступных терминов"""
    from app.constants import SPECIALITIES
    return render_template('patient/calendar.html', specialities=SPECIALITIES)


@patient_api.route('/available-slots-overview', methods=['GET'])
def api_get_available_slots_overview():
    """API: Обзор доступных слотов по специальностям (публичный)"""
    from app.constants import SPECIALITIES
    
    # Получаем все доступные слоты
    available_slots = TimeSlot.query.filter_by(status='available').all()
    
    # Группируем по специальностям
    speciality_overview = {}
    
    for slot in available_slots:
        if slot.calendar and slot.calendar.doctor:
            speciality = slot.calendar.doctor.speciality
            if speciality not in speciality_overview:
                speciality_info = SPECIALITIES.get(speciality, {})
                speciality_overview[speciality] = {
                    'code': speciality,
                    'name': speciality_info.get('de', speciality),
                    'name_en': speciality_info.get('en'),
                    'icon': speciality_info.get('icon'),
                    'count': 0
                }
            speciality_overview[speciality]['count'] += 1
    
    return jsonify(speciality_overview)


@patient_api.route('/search/doctors', methods=['GET'])
@jwt_required()
def api_search_doctors():
    """API: Поиск врачей с фильтрами"""
    identity = get_jwt_identity()
    if identity.get('type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Параметры поиска
    speciality = request.args.get('speciality')
    city = request.args.get('city')
    name = request.args.get('name')
    
    # Базовый запрос
    query = Doctor.query.filter(Doctor.is_verified == True)
    
    # Фильтры
    if speciality:
        query = query.filter(Doctor.speciality == speciality)
    if name:
        query = query.filter(
            or_(
                Doctor.first_name.ilike(f'%{name}%'),
                Doctor.last_name.ilike(f'%{name}%')
            )
        )
    
    doctors = query.all()
    
    # Формируем ответ
    doctors_data = []
    for doctor in doctors:
        # Получаем ближайшие доступные слоты
        available_slots = []
        if doctor.calendar:
            now = datetime.utcnow()
            future_slots = TimeSlot.query.filter(
                TimeSlot.calendar_id == doctor.calendar.id,
                TimeSlot.status == 'available',
                TimeSlot.start_time > now
            ).order_by(TimeSlot.start_time).limit(3).all()
            
            available_slots = [{
                'id': str(slot.id),
                'date': slot.start_time.strftime('%Y-%m-%d'),
                'time': slot.start_time.strftime('%H:%M'),
                'duration': (slot.end_time - slot.start_time).seconds // 60
            } for slot in future_slots]
        
        doctors_data.append({
            'id': str(doctor.id),
            'first_name': doctor.first_name,
            'last_name': doctor.last_name,
            'name': f'{doctor.first_name} {doctor.last_name}',
            'speciality': doctor.speciality,
            'available_slots': available_slots,
            'has_calendar': doctor.calendar is not None
        })
    
    return jsonify({'doctors': doctors_data})


@patient_api.route('/slots/<doctor_id>', methods=['GET'])
@jwt_required()
def api_get_doctor_slots(doctor_id):
    """API: Получить доступные слоты врача"""
    identity = get_jwt_identity()
    if identity.get('type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    doctor = Doctor.query.get(uuid.UUID(doctor_id))
    if not doctor or not doctor.calendar:
        return jsonify({'error': 'Doctor or calendar not found'}), 404
    
    # Параметры
    date_from = request.args.get('from', datetime.utcnow().strftime('%Y-%m-%d'))
    days = int(request.args.get('days', 7))
    
    try:
        start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    end_date = start_date + timedelta(days=days)
    
    # Получаем слоты
    slots = TimeSlot.query.filter(
        TimeSlot.calendar_id == doctor.calendar.id,
        TimeSlot.status == 'available',
        TimeSlot.start_time >= datetime.combine(start_date, datetime.min.time()),
        TimeSlot.start_time < datetime.combine(end_date, datetime.min.time())
    ).order_by(TimeSlot.start_time).all()
    
    slots_data = {}
    for slot in slots:
        date_str = slot.start_time.strftime('%Y-%m-%d')
        if date_str not in slots_data:
            slots_data[date_str] = []
        
        slots_data[date_str].append({
            'id': str(slot.id),
            'time': slot.start_time.strftime('%H:%M'),
            'duration': (slot.end_time - slot.start_time).seconds // 60
        })
    
    return jsonify({
        'doctor': {
            'id': str(doctor.id),
            'name': f'{doctor.first_name} {doctor.last_name}',
            'speciality': doctor.speciality
        },
        'slots': slots_data
    })


@patient_api.route('/alerts', methods=['GET', 'POST', 'DELETE'])
@jwt_required()
def api_manage_alerts():
    """API: Управление алертами пациента"""
    identity = get_jwt_identity()
    if identity.get('type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    patient = Patient.query.get(uuid.UUID(identity['id']))
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    if request.method == 'GET':
        # Получить все алерты пациента
        alerts = PatientAlert.query.filter_by(patient_id=patient.id).all()
        alerts_data = [{
            'id': str(alert.id),
            'doctor_id': str(alert.doctor_id),
            'doctor_name': f'{alert.doctor.first_name} {alert.doctor.last_name}',
            'speciality': alert.doctor.speciality,
            'created_at': alert.created_at.isoformat(),
            'is_active': alert.is_active
        } for alert in alerts]
        
        return jsonify({'alerts': alerts_data})
    
    elif request.method == 'POST':
        # Создать новый алерт
        data = request.get_json()
        doctor_id = data.get('doctor_id')
        
        if not doctor_id:
            return jsonify({'error': 'Doctor ID required'}), 400
        
        doctor = Doctor.query.get(uuid.UUID(doctor_id))
        if not doctor:
            return jsonify({'error': 'Doctor not found'}), 404
        
        # Проверяем, не существует ли уже алерт
        existing = PatientAlert.query.filter_by(
            patient_id=patient.id,
            doctor_id=doctor.id
        ).first()
        
        if existing:
            return jsonify({'error': 'Alert already exists'}), 400
        
        alert = PatientAlert(
            patient_id=patient.id,
            doctor_id=doctor.id
        )
        db.session.add(alert)
        db.session.commit()
        
        return jsonify({
            'message': 'Alert created successfully',
            'alert_id': str(alert.id)
        })
    
    elif request.method == 'DELETE':
        # Удалить алерт
        alert_id = request.args.get('alert_id')
        if not alert_id:
            return jsonify({'error': 'Alert ID required'}), 400
        
        alert = PatientAlert.query.filter_by(
            id=uuid.UUID(alert_id),
            patient_id=patient.id
        ).first()
        
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
        
        db.session.delete(alert)
        db.session.commit()
        
        return jsonify({'message': 'Alert deleted successfully'})


@patient_api.route('/book', methods=['POST'])
@jwt_required()
def api_book_slot():
    """API: Забронировать слот"""
    identity = get_jwt_identity()
    if identity.get('type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    patient = Patient.query.get(uuid.UUID(identity['id']))
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    data = request.get_json()
    slot_id = data.get('slot_id')
    
    if not slot_id:
        return jsonify({'error': 'Slot ID required'}), 400
    
    slot = TimeSlot.query.get(uuid.UUID(slot_id))
    if not slot or slot.status != 'available':
        return jsonify({'error': 'Slot not available'}), 400
    
    # Проверяем, не забронирован ли уже этот слот
    existing_booking = Booking.query.filter_by(timeslot_id=slot.id).first()
    if existing_booking:
        return jsonify({'error': 'Slot already booked'}), 400
    
    # Создаем бронирование
    booking = Booking(
        timeslot_id=slot.id,
        patient_id=patient.id,
        status='confirmed',
        payment_intent_id=f'pi_test_{uuid.uuid4().hex[:16]}',  # Фиктивный payment intent для MVP
        amount_paid=50.00,  # Фиктивная цена для MVP
        booking_code=''.join(random.choices(string.ascii_uppercase + string.digits, k=8)),
        cancellable_until=slot.start_time - timedelta(hours=24)  # Можно отменить за 24 часа
    )
    
    # Обновляем статус слота
    slot.status = 'booked'
    
    # Обновляем статистику пациента
    patient.total_bookings += 1
    
    db.session.add(booking)
    db.session.commit()
    
    return jsonify({
        'message': 'Booking created successfully',
        'booking_id': str(booking.id),
        'doctor_name': f'{slot.calendar.doctor.first_name} {slot.calendar.doctor.last_name}',
        'date': slot.start_time.strftime('%Y-%m-%d'),
        'time': slot.start_time.strftime('%H:%M')
    })