"""
Patient routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_jwt_extended import jwt_required
from app.utils.jwt_helpers import get_current_user
from app.models import Patient, Booking, Doctor, Calendar, TimeSlot, PatientAlert
from app.constants.specialities import SPECIALITIES
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
    """������� �������� - �������� ��������, ������ ��������� ����� JS"""
    # ��������� ����� ����� JavaScript �� �������
    return render_template('patient/dashboard.html')
    
@patient_api.route('/dashboard')
@jwt_required()
def api_dashboard():
    """API ��� ��������� ������ �������� ��������"""
    identity = get_current_user()
    if identity.get('type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    patient = Patient.query.get(uuid.UUID(identity['id']))
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    now = datetime.utcnow()
    
    # �������� ��������� ����������� ������
    next_booking = Booking.query.join(TimeSlot).filter(
        Booking.patient_id == patient.id,
        Booking.status == 'confirmed',
        TimeSlot.start_time > now
    ).order_by(TimeSlot.start_time).first()
    
    next_appointment = None
    if next_booking:
        doctor = next_booking.timeslot.calendar.doctor
        practice = doctor.practice
        
        # ��������� city �� JSON address
        practice_city = None
        if practice:
            address_dict = practice.address_dict
            practice_city = address_dict.get('city') if isinstance(address_dict, dict) else None
        
        next_appointment = {
            'id': str(next_booking.id),
            'booking_code': next_booking.booking_code,
            'date': next_booking.timeslot.start_time.strftime('%Y-%m-%d'),
            'time': next_booking.timeslot.start_time.strftime('%H:%M'),
            'datetime': next_booking.timeslot.start_time.isoformat(),
            'doctor': {
                'id': str(doctor.id),
                'name': f'{doctor.first_name} {doctor.last_name}',
                'speciality': doctor.speciality,
                'speciality_display': SPECIALITIES.get(doctor.speciality, {}).get('de', doctor.speciality)
            },
            'practice': {
                'name': practice.name if practice else None,
                'address': practice.address if practice else None,
                'phone': practice.phone if practice else None,
                'city': practice_city
            } if practice else None,
            'cancellable': next_booking.can_be_cancelled(),
            'cancellable_until': next_booking.cancellable_until.isoformat() if next_booking.cancellable_until else None
        }
    
    # �������� ������� (��������� 5 ����������� ��� ���������� ��������)
    history_bookings = Booking.query.join(TimeSlot).filter(
        Booking.patient_id == patient.id,
        Booking.status.in_(['completed', 'cancelled'])
    ).order_by(TimeSlot.start_time.desc()).limit(5).all()
    
    history = []
    for booking in history_bookings:
        doctor = booking.timeslot.calendar.doctor
        history.append({
            'id': str(booking.id),
            'date': booking.timeslot.start_time.strftime('%Y-%m-%d'),
            'time': booking.timeslot.start_time.strftime('%H:%M'),
            'doctor_name': f'{doctor.first_name} {doctor.last_name}',
            'speciality': SPECIALITIES.get(doctor.speciality, {}).get('de', doctor.speciality),
            'status': booking.status
        })
    
    # ��������������� ����� (���� ���� ��������� ������)
    recommended_doctors = []
    if next_booking or history_bookings:
        # ����� ������������� �� ���������� �������
        last_speciality = None
        if next_booking:
            last_speciality = next_booking.timeslot.calendar.doctor.speciality
        elif history_bookings:
            last_speciality = history_bookings[0].timeslot.calendar.doctor.speciality
        
        if last_speciality:
            # ������� ������ ������ ��� �� ������������� � ���������� �������
            from sqlalchemy import func
            
            # ��������� ��� �������� ��������� ������
            from app.models import Calendar
            
            recommended = db.session.query(Doctor).join(Calendar).join(TimeSlot).filter(
                Doctor.speciality == last_speciality,
                Doctor.is_verified == True,
                TimeSlot.status == 'available',
                TimeSlot.start_time > now
            ).group_by(Doctor.id).limit(3).all()
            
            for doc in recommended:
                # ������������ ��������� ����� ��� ������� �����
                free_count = TimeSlot.query.filter(
                    TimeSlot.calendar_id == doc.calendar.id,
                    TimeSlot.status == 'available',
                    TimeSlot.start_time > now
                ).count()
                
                # ��������� city �� JSON address
                practice_city = None
                if doc.practice:
                    address_dict = doc.practice.address_dict
                    practice_city = address_dict.get('city') if isinstance(address_dict, dict) else None
                
                recommended_doctors.append({
                    'id': str(doc.id),
                    'name': f'{doc.first_name} {doc.last_name}',
                    'speciality': doc.speciality,
                    'speciality_display': SPECIALITIES.get(doc.speciality, {}).get('de', doc.speciality),
                    'free_slots_count': free_count,
                    'practice': {
                        'name': doc.practice.name if doc.practice else None,
                        'city': practice_city
                    } if doc.practice else None
                })
    
    # �������� �������� ������ ��������
    active_alerts = PatientAlert.query.filter_by(
        patient_id=patient.id,
        is_active=True
    ).order_by(PatientAlert.created_at.desc()).all()
    
    # �������� ��������� ����������� (���������� ������, ������� ���������)
    recent_notifications = PatientAlert.query.filter_by(
        patient_id=patient.id,
        is_active=False
    ).filter(
        PatientAlert.last_notification_at != None
    ).order_by(PatientAlert.last_notification_at.desc()).limit(5).all()
    
    return jsonify({
        'patient': {
            'id': str(patient.id),
            'name': patient.name,
            'phone': patient.phone,
            'total_bookings': patient.total_bookings,
            'attended_appointments': patient.attended_appointments
        },
        'next_appointment': next_appointment,
        'history': history,
        'recommended_doctors': recommended_doctors,
        'active_alerts': [alert.to_dict() for alert in active_alerts],
        'recent_notifications': [alert.to_dict() for alert in recent_notifications]
    })


@patient_api.route('/profile')
@jwt_required()
def api_profile():
    """API ��� ��������� ������ ������� ��������"""
    identity = get_current_user()
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
    """API ��� ��������� ������� ������������ ��������"""
    identity = get_current_user()
    if identity.get('type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    patient = Patient.query.get(uuid.UUID(identity['id']))
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # �������� ��� ������������ ��������
    all_bookings = Booking.query.filter_by(
        patient_id=patient.id
    ).order_by(Booking.created_at.desc()).all()
    
    return jsonify({
        'bookings': [{
            'id': str(booking.id),
            'booking_code': booking.booking_code,
            'doctor_id': str(booking.timeslot.calendar.doctor_id) if booking.timeslot and booking.timeslot.calendar else None,
            'doctor_name': booking.timeslot.calendar.doctor.first_name + ' ' + booking.timeslot.calendar.doctor.last_name if booking.timeslot and booking.timeslot.calendar and booking.timeslot.calendar.doctor else 'Unknown',
            'practice_name': booking.timeslot.calendar.doctor.practice.name if booking.timeslot and booking.timeslot.calendar and booking.timeslot.calendar.doctor and booking.timeslot.calendar.doctor.practice else 'Unknown',
            'speciality': booking.timeslot.calendar.doctor.speciality if booking.timeslot and booking.timeslot.calendar and booking.timeslot.calendar.doctor else 'Unknown',
            'appointment_date': booking.timeslot.start_time.strftime('%Y-%m-%d') if booking.timeslot else '',
            'appointment_time': booking.timeslot.start_time.strftime('%H:%M') if booking.timeslot else '',
            'date': booking.timeslot.start_time.strftime('%Y-%m-%d') if booking.timeslot else '',
            'time': booking.timeslot.start_time.strftime('%H:%M') if booking.timeslot else '',
            'status': booking.status,
            'created_at': booking.created_at.strftime('%Y-%m-%d %H:%M') if booking.created_at else ''
        } for booking in all_bookings]
    })


@bp.route('/profile')
def profile():
    """������� ��������"""
    # ��������� ����� ����� JavaScript �� �������
    return render_template('patient/profile.html')


@bp.route('/bookings')
def bookings():
    """������� ������������ ��������"""
    # ��������� ����� ����� JavaScript �� �������
    return render_template('patient/bookings.html')


@bp.route('/search')
def search():
    """�������� ������ ������"""
    from app.constants.specialities import SPECIALITIES
    return render_template('patient/search.html', specialities=SPECIALITIES)


@bp.route('/calendar')
def calendar():
    """��������� ��������� ��������"""
    from app.constants.specialities import SPECIALITIES
    return render_template('patient/calendar.html', specialities=SPECIALITIES)


@patient_api.route('/available-slots-overview', methods=['GET'])
def api_get_available_slots_overview():
    """API: ����� ��������� ������ �� �������������� (���������)"""
    from app.constants.specialities import SPECIALITIES
    
    # �������� ��� ��������� �����
    available_slots = TimeSlot.query.filter_by(status='available').all()
    
    # ���������� �� ��������������
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
    """API: ����� ������ � ���������"""
    identity = get_current_user()
    if identity.get('type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # ��������� ������
    speciality = request.args.get('speciality')
    city = request.args.get('city')
    name = request.args.get('name')
    
    # ������� ������
    query = Doctor.query.filter(Doctor.is_verified == True)
    
    # �������
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
    
    # ��������� �����
    doctors_data = []
    for doctor in doctors:
        # �������� ��������� ��������� �����
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
    """API: �������� ��������� ����� �����"""
    identity = get_current_user()
    if identity.get('type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    doctor = Doctor.query.get(uuid.UUID(doctor_id))
    if not doctor or not doctor.calendar:
        return jsonify({'error': 'Doctor or calendar not found'}), 404
    
    # ���������
    date_from = request.args.get('from', datetime.utcnow().strftime('%Y-%m-%d'))
    days = int(request.args.get('days', 7))
    
    try:
        start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    end_date = start_date + timedelta(days=days)
    
    # �������� �����
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


@patient_api.route('/book', methods=['POST'])
@jwt_required()
def api_book_slot():
    """API: ������������� ����"""
    identity = get_current_user()
    if identity.get('type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    patient = Patient.query.get(uuid.UUID(identity['id']))
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    data = request.get_json()
    slot_id = data.get('slot_id')
    
    print(f"[DEBUG] Booking request from patient {patient.id} for slot {slot_id}")
    
    if not slot_id:
        return jsonify({'error': 'Slot ID required'}), 400
    
    slot = TimeSlot.query.get(uuid.UUID(slot_id))
    if not slot or slot.status != 'available':
        print(f"[ERROR] Slot not available: slot={slot}, status={slot.status if slot else 'None'}")
        return jsonify({'error': 'Slot not available'}), 400
    
    # ���������, �� ������������ �� ��� ���� ����
    existing_booking = Booking.query.filter_by(timeslot_id=slot.id).first()
    if existing_booking:
        print(f"[ERROR] Slot already booked: {existing_booking.id}")
        return jsonify({'error': 'Slot already booked'}), 400
    
    # ������� ������������
    booking = Booking(
        timeslot_id=slot.id,
        patient_id=patient.id,
        status='confirmed',
        payment_intent_id=f'pi_test_{uuid.uuid4().hex[:16]}',  # ��������� payment intent ��� MVP
        amount_paid=50.00,  # ��������� ���� ��� MVP
        booking_code=''.join(random.choices(string.ascii_uppercase + string.digits, k=8)),
        cancellable_until=slot.start_time - timedelta(hours=24)  # ����� �������� �� 24 ����
    )
    
    # ��������� ������ �����
    slot.status = 'booked'
    
    # ��������� ���������� ��������
    patient.total_bookings += 1
    
    db.session.add(booking)
    db.session.commit()
    
    print(f"[SUCCESS] Booking created: {booking.id}, code: {booking.booking_code}")
    
    # TODO: Send confirmation email
    # Note: Email notifications temporarily disabled after Redis removal
    # Will implement direct email sending in future if needed
    
    return jsonify({
        'message': 'Booking created successfully',
        'booking_id': str(booking.id),
        'booking_code': booking.booking_code,
        'doctor_name': f'{slot.calendar.doctor.first_name} {slot.calendar.doctor.last_name}',
        'date': slot.start_time.strftime('%Y-%m-%d'),
        'time': slot.start_time.strftime('%H:%M')
    })


@patient_api.route('/bookings/<booking_id>/cancel', methods=['POST'])
@jwt_required()
def api_cancel_booking(booking_id):
    """API: �������� ������������"""
    identity = get_current_user()
    if identity.get('type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    patient = Patient.query.get(uuid.UUID(identity['id']))
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    print(f"[DEBUG] Cancelling booking: {booking_id} by patient: {patient.id}")
    
    # ������� ������������
    booking = Booking.query.filter_by(
        id=uuid.UUID(booking_id),
        patient_id=patient.id
    ).first()
    
    if not booking:
        print(f"[ERROR] Booking not found: {booking_id}")
        return jsonify({'error': 'Booking not found'}), 404
    
    print(f"[DEBUG] Booking status: {booking.status}, can_cancel: {booking.can_be_cancelled()}")
    print(f"[DEBUG] Cancellable until: {booking.cancellable_until}, now: {datetime.utcnow()}")
    
    # ��������� ����������� ������
    if not booking.can_be_cancelled():
        print(f"[ERROR] Cannot cancel - deadline passed or wrong status")
        return jsonify({
            'error': 'Booking cannot be cancelled',
            'reason': 'Cancellation deadline has passed'
        }), 400
    
    # �������� ������ �� �������
    data = request.get_json() or {}
    reason = data.get('reason', '')
    
    # �������� ������������
    if booking.cancel(cancelled_by='patient', reason=reason):
        return jsonify({
            'message': 'Booking cancelled successfully',
            'refund_amount': float(booking.refund_amount),
            'booking_code': booking.booking_code
        })
    else:
        return jsonify({'error': 'Failed to cancel booking'}), 500


# ==================== ALERTS ENDPOINTS ====================

@patient_api.route('/alerts', methods=['GET'])
@jwt_required()
def api_get_alerts():
    """API: �������� ��� ������ ��������"""
    identity = get_current_user()
    if identity.get('type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    patient = Patient.query.get(uuid.UUID(identity['id']))
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # �������� �������� ������
    active_alerts = PatientAlert.query.filter_by(
        patient_id=patient.id,
        is_active=True
    ).order_by(PatientAlert.created_at.desc()).all()
    
    # �������� ���������� (��� �����������)
    inactive_alerts = PatientAlert.query.filter_by(
        patient_id=patient.id,
        is_active=False
    ).order_by(PatientAlert.last_notification_at.desc()).limit(10).all()
    
    return jsonify({
        'active_alerts': [alert.to_dict() for alert in active_alerts],
        'recent_notifications': [alert.to_dict() for alert in inactive_alerts]
    })


@patient_api.route('/alerts', methods=['POST'])
@jwt_required()
def api_create_alert():
    """API: ������� ����� �����"""
    identity = get_current_user()
    if identity.get('type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    patient = Patient.query.get(uuid.UUID(identity['id']))
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    data = request.get_json()
    print(f"[DEBUG] Creating alert with data: {data}")
    
    # ��������: ���� �� doctor_id ��� speciality ������ ���� ������
    doctor_id = data.get('doctor_id')
    speciality = data.get('speciality')
    
    if not doctor_id and not speciality:
        print(f"[ERROR] Neither doctor_id nor speciality provided")
        return jsonify({'error': 'Either doctor_id or speciality must be provided'}), 400
    
    # ��������� ��� ����� ����� ��� �� ����������
    if doctor_id:
        # ���� ������ ���������� ����, ��������� �� doctor_id
        existing_alert = PatientAlert.query.filter_by(
            patient_id=patient.id,
            doctor_id=uuid.UUID(doctor_id),
            is_active=True
        ).first()
        print(f"[DEBUG] Checking doctor alert: existing={existing_alert is not None}")
    else:
        # ���� ������ �������������, ��������� �� speciality
        existing_alert = PatientAlert.query.filter_by(
            patient_id=patient.id,
            speciality=speciality,
            is_active=True
        ).first()
        print(f"[DEBUG] Checking speciality alert: existing={existing_alert is not None}")
    
    if existing_alert:
        print(f"[ERROR] Alert already exists: {existing_alert.to_dict()}")
        return jsonify({'error': 'Alert already exists for this doctor/speciality'}), 400
    
    # ������� �����
    # ��������: ���� ������ ����, �������� ��� ��������������
    if doctor_id:
        doctor = Doctor.query.get(uuid.UUID(doctor_id))
        if doctor:
            speciality = doctor.speciality  # ����� speciality � �����
    
    alert = PatientAlert(
        patient_id=patient.id,
        doctor_id=uuid.UUID(doctor_id) if doctor_id else None,
        speciality=speciality,  # ������ ������ ���������
        city=data.get('city'),
        date_from=datetime.strptime(data['date_from'], '%Y-%m-%d').date() if data.get('date_from') else None,
        date_to=datetime.strptime(data['date_to'], '%Y-%m-%d').date() if data.get('date_to') else None,
        email_notifications=data.get('email_notifications', True)
    )
    
    print(f"[DEBUG] Created alert object: doctor_id={alert.doctor_id}, speciality={alert.speciality}")
    
    db.session.add(alert)
    db.session.commit()
    
    print(f"[SUCCESS] Alert saved with ID: {alert.id}")
    
    return jsonify({
        'message': 'Alert created successfully',
        'alert': alert.to_dict()
    }), 201


@patient_api.route('/alerts/check', methods=['POST'])
@jwt_required()
def api_check_alert():
    """API: Проверить существует ли алерт для данного врача/специальности"""
    identity = get_current_user()
    if identity.get('type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    patient = Patient.query.get(uuid.UUID(identity['id']))
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    data = request.get_json()
    doctor_id = data.get('doctor_id')
    speciality = data.get('speciality')
    
    if doctor_id:
        existing_alert = PatientAlert.query.filter_by(
            patient_id=patient.id,
            doctor_id=uuid.UUID(doctor_id),
            is_active=True
        ).first()
    else:
        existing_alert = PatientAlert.query.filter_by(
            patient_id=patient.id,
            speciality=speciality,
            is_active=True
        ).first()
    
    return jsonify({
        'exists': existing_alert is not None,
        'alert_id': str(existing_alert.id) if existing_alert else None
    })


@patient_api.route('/alerts/<alert_id>', methods=['DELETE'])
@jwt_required()
def api_delete_alert(alert_id):
    """API: ������� �����"""
    identity = get_current_user()
    if identity.get('type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    patient = Patient.query.get(uuid.UUID(identity['id']))
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    alert = PatientAlert.query.get(uuid.UUID(alert_id))
    if not alert or str(alert.patient_id) != identity['id']:
        return jsonify({'error': 'Alert not found'}), 404
    
    db.session.delete(alert)
    db.session.commit()
    
    return jsonify({'message': 'Alert deleted successfully'})


@patient_api.route('/alerts/<alert_id>/deactivate', methods=['POST'])
@jwt_required()
def api_deactivate_alert(alert_id):
    """API: �������������� ����� (����� ���� ��� ������� ������������ ����)"""
    identity = get_current_user()
    if identity.get('type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    patient = Patient.query.get(uuid.UUID(identity['id']))
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    alert = PatientAlert.query.get(uuid.UUID(alert_id))
    if not alert or str(alert.patient_id) != identity['id']:
        return jsonify({'error': 'Alert not found'}), 404
    
    alert.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'Alert deactivated successfully'})


@patient_api.route('/delete-account', methods=['DELETE'])
@jwt_required()
def api_delete_account():
    """API: Delete patient account (GDPR compliance)"""
    identity = get_current_user()
    if identity.get('type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    patient = Patient.query.get(uuid.UUID(identity['id']))
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Check for active bookings
    now = datetime.utcnow()
    active_bookings = Booking.query.join(TimeSlot).filter(
        Booking.patient_id == patient.id,
        Booking.status.in_(['confirmed', 'pending']),
        TimeSlot.start_time > now
    ).count()
    
    if active_bookings > 0:
        return jsonify({
            'error': 'Cannot delete account with active bookings',
            'message': 'Bitte stornieren Sie zuerst alle aktiven Buchungen.'
        }), 400
    
    # Delete related data
    # Note: Historical bookings are kept for legal compliance (10 years)
    # but anonymized
    
    # Deactivate all alerts
    PatientAlert.query.filter_by(patient_id=patient.id).update({'is_active': False})
    
    # Anonymize patient data
    patient.name = f"Gelöschter Benutzer {patient.id}"
    patient.phone = "deleted"
    patient.password_hash = None
    patient.is_active = False
    
    db.session.commit()
    
    return jsonify({
        'message': 'Account successfully deleted',
        'info': 'Buchungsdaten werden gemäß gesetzlicher Aufbewahrungspflicht aufbewahrt.'
    })
