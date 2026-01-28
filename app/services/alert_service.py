"""
Alert notification service - проверка и отправка уведомлений пациентам
"""
from app.models import PatientAlert, TimeSlot, Doctor
from app import db
from datetime import datetime


def check_and_notify_alerts(slot_id):
    """
    Проверить алерты при появлении нового свободного слота
    
    Args:
        slot_id: ID слота который стал доступным
    """
    slot = TimeSlot.query.get(slot_id)
    if not slot or slot.status != 'available':
        return
    
    doctor = slot.calendar.doctor
    slot_date = slot.start_time.date()
    
    # Находим подходящие алерты
    alerts = PatientAlert.query.filter(
        PatientAlert.is_active == True,
        db.or_(
            # Алерты на конкретного доктора
            PatientAlert.doctor_id == doctor.id,
            # Алерты на специальность этого доктора
            db.and_(
                PatientAlert.doctor_id == None,
                PatientAlert.speciality == doctor.speciality
            )
        )
    ).all()
    
    notifications_sent = []
    
    for alert in alerts:
        # Проверяем диапазон дат
        if alert.date_from and slot_date < alert.date_from:
            continue
        if alert.date_to and slot_date > alert.date_to:
            continue
        
        # Проверяем что это не тот же слот, о котором уже уведомляли
        if alert.last_slot_notified_id == slot_id:
            continue
        
        # Обновляем статистику алерта
        alert.notifications_sent += 1
        alert.last_notification_at = datetime.utcnow()
        alert.last_slot_notified_id = slot_id
        
        # В продакшене здесь будет отправка email/SMS
        # Пока просто фиксируем что уведомление отправлено
        notifications_sent.append({
            'patient_id': alert.patient_id,
            'doctor_name': f"{doctor.first_name} {doctor.last_name}",
            'slot_date': slot_date.strftime('%Y-%m-%d'),
            'slot_time': slot.start_time.strftime('%H:%M')
        })
    
    if notifications_sent:
        db.session.commit()
        print(f"Sent {len(notifications_sent)} alert notifications for slot {slot_id}")
    
    return notifications_sent


def check_alerts_for_doctor(doctor_id, date_from, date_to):
    """
    Проверить все алерты для врача в заданном диапазоне дат
    Используется при массовом создании слотов
    
    Args:
        doctor_id: ID врача
        date_from: начало периода
        date_to: конец периода
    """
    # Находим все свободные слоты врача в периоде
    doctor = Doctor.query.get(doctor_id)
    if not doctor or not doctor.calendar:
        return
    
    slots = TimeSlot.query.filter(
        TimeSlot.calendar_id == doctor.calendar.id,
        TimeSlot.status == 'available',
        TimeSlot.start_time >= datetime.combine(date_from, datetime.min.time()),
        TimeSlot.start_time <= datetime.combine(date_to, datetime.max.time())
    ).all()
    
    notifications_count = 0
    for slot in slots:
        result = check_and_notify_alerts(slot.id)
        if result:
            notifications_count += len(result)
    
    return notifications_count
