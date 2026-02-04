"""
Notification Tasks
==================

Background tasks for sending notifications (email, SMS, alerts).
All blocking I/O operations are handled here to keep Flask routes fast.
"""

import os
from flask_mail import Message
from app import mail, db
from app.models import PatientAlert, TimeSlot, Doctor, Booking
from datetime import datetime
import json


def send_booking_confirmation_email(booking_id):
    """
    Send booking confirmation email to patient
    
    Event: appointment.created
    Priority: high
    
    Args:
        booking_id: Booking ID
    """
    from app import create_app
    app = create_app()
    
    with app.app_context():
        booking = Booking.query.get(booking_id)
        if not booking:
            return {'error': 'Booking not found'}
        
        slot = booking.timeslot
        doctor = slot.calendar.doctor
        patient = booking.patient
        
        subject = f"Підтвердження запису до {doctor.first_name} {doctor.last_name}"
        
        body_html = f"""
        <html>
        <body>
            <h2>Ваш запис підтверджено!</h2>
            <p><strong>Лікар:</strong> {doctor.first_name} {doctor.last_name}</p>
            <p><strong>Спеціальність:</strong> {doctor.speciality}</p>
            <p><strong>Дата:</strong> {slot.start_time.strftime('%d.%m.%Y')}</p>
            <p><strong>Час:</strong> {slot.start_time.strftime('%H:%M')}</p>
            
            {f'<p><strong>Практика:</strong> {doctor.practice.name}</p>' if doctor.practice else ''}
            {f'<p><strong>Адреса:</strong> {doctor.practice.full_address_string}</p>' if doctor.practice else ''}
            
            <p>Дякуємо, що обрали TerminFinder!</p>
        </body>
        </html>
        """
        
        try:
            msg = Message(
                subject=subject,
                recipients=[patient.email] if patient.email else [],
                html=body_html,
                sender=os.getenv('MAIL_DEFAULT_SENDER', 'noreply@terminfinder.de')
            )
            mail.send(msg)
            return {'status': 'sent', 'booking_id': booking_id}
        except Exception as e:
            return {'error': str(e)}


def send_booking_cancellation_email(booking_id, cancelled_by='patient'):
    """
    Send booking cancellation notification
    
    Event: appointment.cancelled
    Priority: high
    
    Args:
        booking_id: Booking ID
        cancelled_by: 'patient' or 'doctor'
    """
    from app import create_app
    app = create_app()
    
    with app.app_context():
        booking = Booking.query.get(booking_id)
        if not booking:
            return {'error': 'Booking not found'}
        
        slot = booking.timeslot
        doctor = slot.calendar.doctor
        patient = booking.patient
        
        subject = f"Скасовано: Запис до {doctor.first_name} {doctor.last_name}"
        
        body_html = f"""
        <html>
        <body>
            <h2>Ваш запис скасовано</h2>
            <p><strong>Лікар:</strong> {doctor.first_name} {doctor.last_name}</p>
            <p><strong>Дата:</strong> {slot.start_time.strftime('%d.%m.%Y')}</p>
            <p><strong>Час:</strong> {slot.start_time.strftime('%H:%M')}</p>
            
            <p>Скасовано: {cancelled_by}</p>
            
            <p>Ви можете знайти іншого лікаря на TerminFinder.</p>
        </body>
        </html>
        """
        
        try:
            msg = Message(
                subject=subject,
                recipients=[patient.email] if patient.email else [],
                html=body_html,
                sender=os.getenv('MAIL_DEFAULT_SENDER', 'noreply@terminfinder.de')
            )
            mail.send(msg)
            return {'status': 'sent', 'booking_id': booking_id}
        except Exception as e:
            return {'error': str(e)}


def check_and_send_slot_alerts(slot_id):
    """
    Check patient alerts and send notifications for new available slot
    
    Event: doctor.calendar.sync
    Priority: low (can be delayed)
    
    Args:
        slot_id: TimeSlot ID
    """
    from app import create_app
    app = create_app()
    
    with app.app_context():
        slot = TimeSlot.query.get(slot_id)
        if not slot or slot.status != 'available':
            return {'status': 'skipped', 'reason': 'slot not available'}
        
        doctor = slot.calendar.doctor
        slot_date = slot.start_time.date()
        
        # Get practice city
        practice_city = None
        if doctor.practice:
            try:
                address_dict = json.loads(doctor.practice.address) if doctor.practice.address else {}
                practice_city = address_dict.get('city', '').lower() if address_dict else None
            except:
                practice_city = None
        
        # Find matching alerts
        alerts = PatientAlert.query.filter(
            PatientAlert.is_active == True,
            db.or_(
                PatientAlert.doctor_id == doctor.id,
                db.and_(
                    PatientAlert.doctor_id == None,
                    PatientAlert.speciality == doctor.speciality
                )
            )
        ).all()
        
        notifications_sent = 0
        
        for alert in alerts:
            # Check city
            if alert.city and practice_city:
                if alert.city.lower() != practice_city:
                    continue
            
            # Check date range
            if alert.date_from and slot_date < alert.date_from:
                continue
            if alert.date_to and slot_date > alert.date_to:
                continue
            
            # Check if already notified
            if alert.last_slot_notified_id == slot_id:
                continue
            
            # Send notification email
            patient = alert.patient
            if patient and patient.email:
                subject = f"Новий вільний час: {doctor.first_name} {doctor.last_name}"
                
                body_html = f"""
                <html>
                <body>
                    <h2>Знайдено вільний час!</h2>
                    <p><strong>Лікар:</strong> {doctor.first_name} {doctor.last_name}</p>
                    <p><strong>Спеціальність:</strong> {doctor.speciality}</p>
                    <p><strong>Дата:</strong> {slot_date.strftime('%d.%m.%Y')}</p>
                    <p><strong>Час:</strong> {slot.start_time.strftime('%H:%M')}</p>
                    {f'<p><strong>Місто:</strong> {practice_city}</p>' if practice_city else ''}
                    
                    <p><a href="https://terminfinder.de/booking/slot/{slot_id}">Записатися</a></p>
                </body>
                </html>
                """
                
                try:
                    msg = Message(
                        subject=subject,
                        recipients=[patient.email],
                        html=body_html,
                        sender=os.getenv('MAIL_DEFAULT_SENDER', 'noreply@terminfinder.de')
                    )
                    mail.send(msg)
                    
                    # Update alert stats
                    alert.notifications_sent += 1
                    alert.last_notification_at = datetime.utcnow()
                    alert.last_slot_notified_id = slot_id
                    notifications_sent += 1
                    
                except Exception as e:
                    print(f"Failed to send alert for patient {patient.id}: {e}")
        
        db.session.commit()
        
        return {
            'status': 'completed',
            'slot_id': slot_id,
            'notifications_sent': notifications_sent
        }


def send_doctor_verification_email(doctor_id):
    """
    Send email to doctor about verification status
    
    Event: doctor.verified
    Priority: medium
    
    Args:
        doctor_id: Doctor ID
    """
    from app import create_app
    app = create_app()
    
    with app.app_context():
        doctor = Doctor.query.get(doctor_id)
        if not doctor:
            return {'error': 'Doctor not found'}
        
        subject = "Ваш профіль верифіковано - TerminFinder"
        
        body_html = f"""
        <html>
        <body>
            <h2>Вітаємо, {doctor.first_name}!</h2>
            <p>Ваш профіль лікаря на TerminFinder успішно верифіковано.</p>
            
            <p>Тепер ви можете:</p>
            <ul>
                <li>Створювати часові слоти для пацієнтів</li>
                <li>Приймати онлайн-записи</li>
                <li>Керувати своїм календарем</li>
            </ul>
            
            <p><a href="https://terminfinder.de/doctor/dashboard">Перейти до панелі</a></p>
        </body>
        </html>
        """
        
        try:
            msg = Message(
                subject=subject,
                recipients=[doctor.email],
                html=body_html,
                sender=os.getenv('MAIL_DEFAULT_SENDER', 'noreply@terminfinder.de')
            )
            mail.send(msg)
            return {'status': 'sent', 'doctor_id': doctor_id}
        except Exception as e:
            return {'error': str(e)}
