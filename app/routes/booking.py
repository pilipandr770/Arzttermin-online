"""
Маршруты бронирований
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Booking, TimeSlot, Patient, Doctor
from app.constants import SPECIALITIES
from app import db
from datetime import datetime, timedelta
import uuid

bp = Blueprint('booking', __name__)


@bp.route('/<booking_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_booking(booking_id):
    """
    API: Отменить бронирование
    
    Request body:
    - reason: причина отмены (опционально)
    """
    identity = get_jwt_identity()
    
    try:
        booking = Booking.query.get(uuid.UUID(booking_id))
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Проверка прав доступа
        is_patient = identity.get('type') == 'patient' and str(booking.patient_id) == identity['id']
        is_doctor = identity.get('type') == 'doctor' and str(booking.timeslot.calendar.doctor_id) == identity['id']
        
        if not is_patient and not is_doctor:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Проверка, можно ли отменить
        if booking.status not in ['confirmed', 'pending']:
            return jsonify({'error': f'Cannot cancel booking with status: {booking.status}'}), 400
        
        # Для пациента - проверка времени
        if is_patient:
            if not booking.can_be_cancelled():
                return jsonify({
                    'error': 'Cancellation deadline has passed',
                    'cancellable_until': booking.cancellable_until.isoformat()
                }), 400
        
        # Отмена бронирования
        data = request.get_json() or {}
        reason = data.get('reason', '')
        
        booking.status = 'cancelled'
        booking.cancelled_at = datetime.utcnow()
        booking.cancelled_by = 'patient' if is_patient else 'doctor'
        booking.cancellation_reason = reason
        
        # Освобождаем слот
        if booking.timeslot:
            booking.timeslot.status = 'available'
        
        db.session.commit()
        
        # TODO: отправить email уведомление
        # TODO: обработать возврат средств через Stripe
        
        return jsonify({
            'message': 'Booking cancelled successfully',
            'booking': {
                'id': str(booking.id),
                'status': booking.status,
                'cancelled_at': booking.cancelled_at.isoformat(),
                'cancelled_by': booking.cancelled_by
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<booking_id>', methods=['GET'])
@jwt_required()
def get_booking(booking_id):
    """
    API: Получить информацию о бронировании
    """
    identity = get_jwt_identity()
    
    try:
        booking = Booking.query.get(uuid.UUID(booking_id))
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Проверка прав доступа
        is_patient = identity.get('type') == 'patient' and str(booking.patient_id) == identity['id']
        is_doctor = identity.get('type') == 'doctor' and str(booking.timeslot.calendar.doctor_id) == identity['id']
        
        if not is_patient and not is_doctor:
            return jsonify({'error': 'Unauthorized'}), 403
        
        doctor = booking.timeslot.calendar.doctor
        practice = doctor.practice
        
        return jsonify({
            'booking': {
                'id': str(booking.id),
                'booking_code': booking.booking_code,
                'status': booking.status,
                'created_at': booking.created_at.isoformat(),
                'cancellable': booking.can_be_cancelled(),
                'cancellable_until': booking.cancellable_until.isoformat() if booking.cancellable_until else None,
                'cancelled_at': booking.cancelled_at.isoformat() if booking.cancelled_at else None,
                'cancelled_by': booking.cancelled_by,
                'timeslot': {
                    'start_time': booking.timeslot.start_time.isoformat(),
                    'end_time': booking.timeslot.end_time.isoformat(),
                    'date': booking.timeslot.start_time.strftime('%Y-%m-%d'),
                    'time': booking.timeslot.start_time.strftime('%H:%M')
                },
                'doctor': {
                    'id': str(doctor.id),
                    'first_name': doctor.first_name,
                    'last_name': doctor.last_name,
                    'full_name': f"{doctor.first_name} {doctor.last_name}",
                    'speciality': doctor.speciality,
                    'speciality_display': SPECIALITIES.get(doctor.speciality, {}).get('de', doctor.speciality)
                },
                'practice': {
                    'id': str(practice.id) if practice else None,
                    'name': practice.name if practice else None,
                    'address': practice.address if practice else None,
                    'phone': practice.phone if practice else None
                } if practice else None,
                'patient': {
                    'id': str(booking.patient.id),
                    'name': booking.patient.name,
                    'phone': booking.patient.phone
                } if is_doctor else None
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/by-code/<booking_code>', methods=['GET'])
def get_booking_by_code(booking_code):
    """
    API: Получить информацию о бронировании по коду (без авторизации)
    """
    try:
        booking = Booking.query.filter_by(booking_code=booking_code).first()
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        doctor = booking.timeslot.calendar.doctor
        practice = doctor.practice
        
        return jsonify({
            'booking': {
                'id': str(booking.id),
                'booking_code': booking.booking_code,
                'status': booking.status,
                'cancellable': booking.can_be_cancelled(),
                'cancellable_until': booking.cancellable_until.isoformat() if booking.cancellable_until else None,
                'timeslot': {
                    'start_time': booking.timeslot.start_time.isoformat(),
                    'end_time': booking.timeslot.end_time.isoformat(),
                    'date': booking.timeslot.start_time.strftime('%Y-%m-%d'),
                    'time': booking.timeslot.start_time.strftime('%H:%M')
                },
                'doctor': {
                    'first_name': doctor.first_name,
                    'last_name': doctor.last_name,
                    'full_name': f"{doctor.first_name} {doctor.last_name}",
                    'speciality': doctor.speciality,
                    'speciality_display': SPECIALITIES.get(doctor.speciality, {}).get('de', doctor.speciality)
                },
                'practice': {
                    'name': practice.name if practice else None,
                    'address': practice.address if practice else None,
                    'phone': practice.phone if practice else None
                } if practice else None
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
