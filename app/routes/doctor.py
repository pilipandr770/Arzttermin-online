"""
Маршруты врачей
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.jwt_helpers import get_current_user
from app.models.doctor import Doctor
from app.models.calendar import Calendar
from app.models.booking import Booking
from app.models.calendar import TimeSlot
from app import db
import uuid
import json
from datetime import datetime, timedelta

bp = Blueprint('doctor', __name__, url_prefix='/doctor')
doctor_api = Blueprint('doctor_api', __name__)


@bp.route('/dashboard')
def dashboard():
    """Дашборд врача - рендерим страницу, данные загружаем через JS"""
    # Проверяем токен через JavaScript на клиенте
    return render_template('doctor/dashboard.html')


@bp.route('/calendar-test')
def calendar_test():
    """Тестовая страница календаря для отладки"""
    return render_template('doctor/calendar_test.html')


@doctor_api.route('/dashboard')
@jwt_required()
def api_dashboard():
    """API для получения данных дашборда врача"""
    identity = get_current_user()
    if identity.get('type') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    doctor = Doctor.query.get(uuid.UUID(identity['id']))
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    # Получаем календарь врача
    calendar = doctor.calendar
    
    # Сегодняшние данные
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    today_appointments = []
    next_appointment = None
    
    if calendar:
        # Получаем подтвержденные бронирования на сегодня
        today_bookings = Booking.query.join(TimeSlot).filter(
            TimeSlot.calendar_id == calendar.id,
            TimeSlot.start_time >= today_start,
            TimeSlot.start_time <= today_end,
            Booking.status == 'confirmed'
        ).order_by(TimeSlot.start_time).all()
        
        now = datetime.utcnow()
        for booking in today_bookings:
            appointment_data = {
                'id': str(booking.id),
                'patient_name': booking.patient.name if booking.patient else 'Unknown',
                'patient_phone': booking.patient.phone if booking.patient else 'Unknown',
                'time': booking.timeslot.start_time.strftime('%H:%M'),
                'start_time': booking.timeslot.start_time.isoformat(),
                'status': booking.status
            }
            today_appointments.append(appointment_data)
            
            # Найти следующий термин
            if not next_appointment and booking.timeslot.start_time > now:
                next_appointment = appointment_data
        
        # Статистика за эту неделю
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=7)
        
        week_slots = TimeSlot.query.filter(
            TimeSlot.calendar_id == calendar.id,
            TimeSlot.start_time >= week_start,
            TimeSlot.start_time < week_end
        ).all()
        
        total_slots = len(week_slots)
        booked_slots = sum(1 for slot in week_slots if slot.status == 'booked')
        available_slots = sum(1 for slot in week_slots if slot.status == 'available')
        blocked_slots = sum(1 for slot in week_slots if slot.status == 'blocked')
        
        fill_rate = round((booked_slots / total_slots * 100) if total_slots > 0 else 0, 1)
    else:
        total_slots = 0
        booked_slots = 0
        available_slots = 0
        blocked_slots = 0
        fill_rate = 0
    
    return jsonify({
        'doctor': {
            'id': str(doctor.id),
            'name': f'{doctor.first_name} {doctor.last_name}',
            'speciality': doctor.speciality,
            'is_verified': doctor.is_verified,
            'has_calendar': calendar is not None
        },
        'today': {
            'appointments_count': len(today_appointments),
            'appointments': today_appointments,
            'next_appointment': next_appointment
        },
        'this_week': {
            'total_slots': total_slots,
            'booked_slots': booked_slots,
            'available_slots': available_slots,
            'blocked_slots': blocked_slots,
            'fill_rate': fill_rate
        },
        'calendar': {
            'exists': calendar is not None,
            'working_hours': json.loads(calendar.working_hours) if calendar else {},
            'slot_duration': calendar.slot_duration if calendar else 30,
            'buffer_time': calendar.buffer_time if calendar else 5
        } if calendar else {'exists': False}
    })


@bp.route('/calendar')
def calendar():
    """Управление календарем врача"""
    # Проверяем токен через JavaScript на клиенте
    return render_template('doctor/calendar.html')


@bp.route('/bookings')
def bookings():
    """Управление бронированиями врача"""
    # Проверяем токен через JavaScript на клиенте
    return render_template('doctor/bookings.html')


@doctor_api.route('/profile', methods=['GET', 'PUT'])
@jwt_required()
def api_profile():
    """API: Получение и обновление профиля врача"""
    identity = get_current_user()
    print(f"Doctor profile API called with identity: {identity}")  # Debug log
    
    if identity.get('type') != 'doctor':
        print(f"Wrong user type: {identity.get('type')}")  # Debug log
        return jsonify({'error': 'Unauthorized'}), 403
    
    doctor = Doctor.query.get(uuid.UUID(identity['id']))
    if not doctor:
        print(f"Doctor not found with ID: {identity['id']}")  # Debug log
        return jsonify({'error': 'Doctor not found'}), 404
    
    if request.method == 'GET':
        return jsonify({
            'doctor': {
                'id': str(doctor.id),
                'first_name': doctor.first_name,
                'last_name': doctor.last_name,
                'email': doctor.email,
                'speciality': doctor.speciality,
                'is_verified': doctor.is_verified,
                'languages': json.loads(doctor.languages) if doctor.languages else ['de'],
                'schedule_settings': {
                    'slot_duration_minutes': doctor.slot_duration_minutes or 30,
                    'work_days': json.loads(doctor.work_days) if doctor.work_days else ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
                    'work_start_time': doctor.work_start_time.strftime('%H:%M') if doctor.work_start_time else '09:00',
                    'work_end_time': doctor.work_end_time.strftime('%H:%M') if doctor.work_end_time else '17:00'
                }
            }
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        
        # Обновляем поля
        if 'first_name' in data:
            doctor.first_name = data['first_name']
        if 'last_name' in data:
            doctor.last_name = data['last_name']
        if 'speciality' in data:
            doctor.speciality = data['speciality']
        if 'languages' in data:
            doctor.languages = json.dumps(data['languages'])
        
        db.session.commit()
        
        return jsonify({'message': 'Profile updated successfully'})


@bp.route('/profile')
def profile():
    """Профиль врача"""
    # Проверяем токен через JavaScript на клиенте
    return render_template('doctor/profile.html')


@bp.route('/schedule-settings')
def schedule_settings():
    """Настройки расписания врача"""
    # Проверяем токен через JavaScript на клиенте
    return render_template('doctor/schedule_settings.html')


# API endpoints для управления календарем

@doctor_api.route('/calendar/create', methods=['POST'])
@jwt_required()
def api_create_calendar():
    """API: Создать календарь для врача"""
    identity = get_current_user()
    if identity.get('type') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    doctor = Doctor.query.get(uuid.UUID(identity['id']))
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    # Проверяем, есть ли уже календарь
    if doctor.calendar:
        return jsonify({'error': 'Calendar already exists'}), 400
    
    data = request.get_json()
    working_hours = data.get('working_hours', {})
    slot_duration = data.get('slot_duration', 30)
    buffer_time = data.get('buffer_time', 5)
    
    # Создаем календарь
    calendar = Calendar(
        doctor_id=doctor.id,
        working_hours=json.dumps(working_hours),
        slot_duration=slot_duration,
        buffer_time=buffer_time
    )
    db.session.add(calendar)
    db.session.commit()
    
    return jsonify({
        'message': 'Calendar created successfully',
        'calendar_id': str(calendar.id)
    })


@doctor_api.route('/bookings', methods=['GET'])
@jwt_required()
def api_get_bookings():
    """API: Получить все бронирования врача"""
    identity = get_current_user()
    if identity.get('type') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    doctor = Doctor.query.get(uuid.UUID(identity['id']))
    if not doctor or not doctor.calendar:
        return jsonify({'error': 'Calendar not found'}), 404
    
    # Параметры фильтрации
    status = request.args.get('status')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Базовый запрос
    query = Booking.query.join(Booking.timeslot).filter(
        Booking.timeslot.has(calendar_id=doctor.calendar.id)
    )
    
    # Фильтры
    if status:
        query = query.filter(Booking.status == status)
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Booking.timeslot.has(TimeSlot.start_time >= from_date))
        except ValueError:
            pass
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            to_date = to_date + timedelta(days=1)  # Include the entire day
            query = query.filter(Booking.timeslot.has(TimeSlot.start_time <= to_date))
        except ValueError:
            pass
    
    bookings = query.order_by(Booking.created_at.desc()).all()
    
    bookings_data = []
    for booking in bookings:
        bookings_data.append({
            'id': str(booking.id),
            'patient_name': booking.patient.name if booking.patient else 'Unknown',
            'date': booking.timeslot.start_time.strftime('%Y-%m-%d'),
            'time': booking.timeslot.start_time.strftime('%H:%M'),
            'status': booking.status,
            'booking_code': booking.booking_code,
            'created_at': booking.created_at.isoformat()
        })
    
    return jsonify({'bookings': bookings_data})

@doctor_api.route('/calendar/slots', methods=['GET', 'POST'])
@jwt_required()
def api_manage_slots():
    """API: Управление временными слотами"""
    identity = get_current_user()
    if identity.get('type') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    doctor = Doctor.query.get(uuid.UUID(identity['id']))
    if not doctor or not doctor.calendar:
        return jsonify({'error': 'Calendar not found'}), 404
    
    if request.method == 'GET':
        # Получить слоты за период (для календаря месяц/неделя/день)
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        date_str = request.args.get('date')  # для обратной совместимости
        
        if date_str:
            # Если передана одиночная дата (старый формат)
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                start_of_day = datetime.combine(target_date, datetime.min.time())
                end_of_day = datetime.combine(target_date, datetime.max.time())
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
        elif start_date_str and end_date_str:
            # Если передан диапазон дат
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                start_of_day = datetime.combine(start_date, datetime.min.time())
                end_of_day = datetime.combine(end_date, datetime.max.time())
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
        else:
            return jsonify({'error': 'Date parameters required'}), 400
        
        # Получаем слоты за период
        slots = TimeSlot.query.filter(
            TimeSlot.calendar_id == doctor.calendar.id,
            TimeSlot.start_time >= start_of_day,
            TimeSlot.start_time <= end_of_day
        ).order_by(TimeSlot.start_time).all()
        
        slots_data = []
        for slot in slots:
            slot_data = {
                'id': str(slot.id),
                'start_time': slot.start_time.isoformat(),
                'end_time': slot.end_time.isoformat(),
                'status': slot.status
            }
            
            slots_data.append(slot_data)
        
        return jsonify({'slots': slots_data})
    
    elif request.method == 'POST':
        # Создать или обновить слоты
        data = request.get_json()
        action = data.get('action')  # 'generate', 'block', 'unblock'
        
        if action == 'generate':
            # Генерировать слоты на основе календаря
            date_str = data.get('date')
            if not date_str:
                return jsonify({'error': 'Date required for generation'}), 400
            
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Получаем рабочие часы из календаря
            working_hours = json.loads(doctor.calendar.working_hours)
            day_name = target_date.strftime('%A').lower()
            
            if day_name in working_hours and working_hours[day_name]:
                # Создаем слоты для каждого интервала
                for interval in working_hours[day_name]:
                    if isinstance(interval, list) and len(interval) == 2:
                        # Старая структура: ["09:00", "18:00"]
                        start_hour, start_min = map(int, interval[0].split(':'))
                        end_hour, end_min = map(int, interval[1].split(':'))
                    elif isinstance(interval, dict) and 'start' in interval and 'end' in interval:
                        # Новая структура: {"start": "09:00", "end": "18:00"}
                        start_hour, start_min = map(int, interval['start'].split(':'))
                        end_hour, end_min = map(int, interval['end'].split(':'))
                    else:
                        continue
                    
                    current_time = datetime.combine(target_date, datetime.time(start_hour, start_min))
                    end_time = datetime.combine(target_date, datetime.time(end_hour, end_min))
                    
                    while current_time < end_time:
                        slot_end = current_time + timedelta(minutes=doctor.calendar.slot_duration)
                        if slot_end > end_time:
                            break
                        
                        # Проверяем, не существует ли уже слот
                        existing = TimeSlot.query.filter(
                            TimeSlot.calendar_id == doctor.calendar.id,
                            TimeSlot.start_time == current_time
                        ).first()
                        
                        if not existing:
                            slot = TimeSlot(
                                calendar_id=doctor.calendar.id,
                                start_time=current_time,
                                end_time=slot_end,
                                status='available'
                            )
                            db.session.add(slot)
                        
                        current_time = slot_end + timedelta(minutes=doctor.calendar.buffer_time)
                
                db.session.commit()
                return jsonify({'message': 'Slots generated successfully'})
            
            return jsonify({'error': 'No working hours for this day'}), 400
        
        elif action in ['block', 'unblock']:
            slot_id = data.get('slot_id')
            if not slot_id:
                return jsonify({'error': 'Slot ID required'}), 400
            
            slot = TimeSlot.query.filter(
                TimeSlot.id == uuid.UUID(slot_id),
                TimeSlot.calendar_id == doctor.calendar.id
            ).first()
            
            if not slot:
                return jsonify({'error': 'Slot not found'}), 404
            
            if action == 'block':
                if slot.status == 'available':
                    slot.status = 'blocked'
                    db.session.commit()
                    return jsonify({'message': 'Slot blocked'})
                else:
                    return jsonify({'error': 'Slot cannot be blocked'}), 400
            else:  # unblock
                if slot.status == 'blocked':
                    slot.status = 'available'
                    db.session.commit()
                    return jsonify({'message': 'Slot unblocked'})
                else:
                    return jsonify({'error': 'Slot is not blocked'}), 400
        
        return jsonify({'error': 'Invalid action'}), 400


@doctor_api.route('/schedule-settings', methods=['PUT'])
@jwt_required()
def api_update_schedule_settings():
    """API: Обновить настройки расписания врача"""
    identity = get_current_user()
    print(f"Update schedule settings - identity: {identity}")  # Debug
    
    if identity.get('type') != 'doctor':
        print("Wrong user type")  # Debug
        return jsonify({'error': 'Unauthorized'}), 403
    
    doctor = Doctor.query.get(uuid.UUID(identity['id']))
    if not doctor:
        print(f"Doctor not found: {identity['id']}")  # Debug
        return jsonify({'error': 'Doctor not found'}), 404
    
    data = request.get_json()
    print(f"Received data: {data}")  # Debug
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        # Обновляем настройки
        if 'slot_duration_minutes' in data:
            doctor.slot_duration_minutes = data['slot_duration_minutes']
            print(f"Updated slot_duration: {doctor.slot_duration_minutes}")  # Debug
        if 'work_days' in data:
            doctor.work_days_list = data['work_days']
            print(f"Updated work_days: {doctor.work_days_list}")  # Debug
        if 'work_start_time' in data:
            from datetime import datetime
            doctor.work_start_time = datetime.strptime(data['work_start_time'], '%H:%M').time()
            print(f"Updated work_start_time: {doctor.work_start_time}")  # Debug
        if 'work_end_time' in data:
            from datetime import datetime
            doctor.work_end_time = datetime.strptime(data['work_end_time'], '%H:%M').time()
            print(f"Updated work_end_time: {doctor.work_end_time}")  # Debug
        
        db.session.commit()
        print("Settings updated successfully")  # Debug
        
        return jsonify({
            'message': 'Schedule settings updated successfully',
            'settings': {
                'slot_duration_minutes': doctor.slot_duration_minutes,
                'work_days': doctor.work_days_list,
                'work_start_time': doctor.work_start_time.strftime('%H:%M'),
                'work_end_time': doctor.work_end_time.strftime('%H:%M')
            }
        })
    except Exception as e:
        print(f"Error updating settings: {e}")  # Debug
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@doctor_api.route('/calendar/generate-slots', methods=['POST'])
@jwt_required()
def api_generate_slots():
    """API: Генерировать термины на основе настроек расписания"""
    identity = get_current_user()
    if identity.get('type') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    doctor = Doctor.query.get(uuid.UUID(identity['id']))
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    data = request.get_json() or {}
    weeks_ahead = data.get('weeks_ahead', 1)
    
    # Проверяем, есть ли календарь у врача
    if not doctor.calendar:
        # Создаем календарь, если его нет
        from app.models.calendar import Calendar
        calendar = Calendar(doctor_id=doctor.id, name=f"Calendar of {doctor.name}")
        db.session.add(calendar)
        db.session.commit()
    else:
        calendar = doctor.calendar
    
    from datetime import datetime, timedelta, time
    import calendar as cal_module
    
    generated_slots = []
    today = datetime.now().date()
    
    # Генерируем на указанное количество недель вперед
    for week_offset in range(weeks_ahead):
        week_start = today + timedelta(weeks=week_offset)
        
        # Находим понедельник текущей недели
        monday = week_start - timedelta(days=week_start.weekday())
        
        for day_offset in range(7):
            current_date = monday + timedelta(days=day_offset)
            
            # Проверяем, является ли день рабочим
            day_name = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'][day_offset]
            if day_name not in doctor.work_days_list:
                continue
            
            # Генерируем слоты на этот день
            current_time = datetime.combine(current_date, doctor.work_start_time)
            end_time = datetime.combine(current_date, doctor.work_end_time)
            
            while current_time < end_time:
                slot_end = current_time + timedelta(minutes=doctor.slot_duration_minutes)
                
                # Проверяем, не существует ли уже такой слот
                existing_slot = TimeSlot.query.filter_by(
                    calendar_id=calendar.id,
                    start_time=current_time,
                    end_time=slot_end
                ).first()
                
                if not existing_slot:
                    new_slot = TimeSlot(
                        calendar_id=calendar.id,
                        start_time=current_time,
                        end_time=slot_end,
                        status='available'
                    )
                    db.session.add(new_slot)
                    generated_slots.append({
                        'id': str(new_slot.id),
                        'start_time': current_time.isoformat(),
                        'end_time': slot_end.isoformat(),
                        'status': 'available'
                    })
                
                current_time = slot_end
    
    db.session.commit()
    
    return jsonify({
        'message': f'Generated {len(generated_slots)} time slots',
        'generated_slots': generated_slots
    })


@doctor_api.route('/calendar/close-day', methods=['POST'])
@jwt_required()
def api_close_day():
    """
    API: Закрыть день (заблокировать все слоты на день)
    
    Request body:
    - date: дата в формате YYYY-MM-DD
    - reason: причина (опционально)
    """
    identity = get_current_user()
    if identity.get('type') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    doctor = Doctor.query.get(uuid.UUID(identity['id']))
    if not doctor or not doctor.calendar:
        return jsonify({'error': 'Calendar not found'}), 404
    
    data = request.get_json()
    if not data or 'date' not in data:
        return jsonify({'error': 'Date is required'}), 400
    
    try:
        target_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        # Получаем все слоты на этот день
        slots = TimeSlot.query.filter(
            TimeSlot.calendar_id == doctor.calendar.id,
            TimeSlot.start_time >= start_of_day,
            TimeSlot.start_time <= end_of_day
        ).all()
        
        blocked_count = 0
        booked_count = 0
        
        for slot in slots:
            if slot.status == 'available':
                slot.status = 'blocked'
                blocked_count += 1
            elif slot.status == 'booked':
                booked_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'Day closed successfully',
            'date': data['date'],
            'blocked_slots': blocked_count,
            'booked_slots': booked_count,
            'warning': f'{booked_count} slots have existing bookings' if booked_count > 0 else None
        })
    
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@doctor_api.route('/analytics', methods=['GET'])
@jwt_required()
def api_analytics():
    """
    API: Получить аналитику врача
    
    Query params:
    - period: week, month, year (default: week)
    """
    identity = get_current_user()
    if identity.get('type') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    doctor = Doctor.query.get(uuid.UUID(identity['id']))
    if not doctor or not doctor.calendar:
        return jsonify({'error': 'Calendar not found'}), 404
    
    period = request.args.get('period', 'week')
    
    # Определяем временной диапазон
    now = datetime.utcnow()
    if period == 'week':
        start_date = now - timedelta(days=7)
    elif period == 'month':
        start_date = now - timedelta(days=30)
    elif period == 'year':
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=7)
    
    # Получаем все слоты за период
    all_slots = TimeSlot.query.filter(
        TimeSlot.calendar_id == doctor.calendar.id,
        TimeSlot.start_time >= start_date,
        TimeSlot.start_time <= now
    ).all()
    
    # Получаем все бронирования за период
    all_bookings = Booking.query.join(TimeSlot).filter(
        TimeSlot.calendar_id == doctor.calendar.id,
        TimeSlot.start_time >= start_date,
        TimeSlot.start_time <= now
    ).all()
    
    # Статистика
    total_slots = len(all_slots)
    booked_slots = sum(1 for slot in all_slots if slot.status == 'booked')
    available_slots = sum(1 for slot in all_slots if slot.status == 'available')
    blocked_slots = sum(1 for slot in all_slots if slot.status == 'blocked')
    
    total_appointments = len(all_bookings)
    confirmed_appointments = sum(1 for b in all_bookings if b.status == 'confirmed')
    completed_appointments = sum(1 for b in all_bookings if b.status == 'completed')
    cancelled_appointments = sum(1 for b in all_bookings if b.status == 'cancelled')
    no_show_appointments = sum(1 for b in all_bookings if b.status == 'no_show')
    
    fill_rate = round((booked_slots / total_slots * 100) if total_slots > 0 else 0, 1)
    no_show_rate = round((no_show_appointments / completed_appointments * 100) if completed_appointments > 0 else 0, 1)
    cancellation_rate = round((cancelled_appointments / total_appointments * 100) if total_appointments > 0 else 0, 1)
    
    # Распределение по дням недели
    bookings_by_day = {
        'monday': 0, 'tuesday': 0, 'wednesday': 0, 
        'thursday': 0, 'friday': 0, 'saturday': 0, 'sunday': 0
    }
    day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    for booking in all_bookings:
        if booking.status in ['confirmed', 'completed']:
            day_name = day_names[booking.timeslot.start_time.weekday()]
            bookings_by_day[day_name] += 1
    
    return jsonify({
        'period': {
            'type': period,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': now.strftime('%Y-%m-%d')
        },
        'slots': {
            'total': total_slots,
            'booked': booked_slots,
            'available': available_slots,
            'blocked': blocked_slots,
            'fill_rate': fill_rate
        },
        'appointments': {
            'total': total_appointments,
            'confirmed': confirmed_appointments,
            'completed': completed_appointments,
            'cancelled': cancelled_appointments,
            'no_show': no_show_appointments,
            'no_show_rate': no_show_rate,
            'cancellation_rate': cancellation_rate
        },
        'bookings_by_day': bookings_by_day
    })
    """
    API: Открыть день (разблокировать все слоты на день)
    
    Request body:
    - date: дата в формате YYYY-MM-DD
    """
    identity = get_current_user()
    if identity.get('type') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    doctor = Doctor.query.get(uuid.UUID(identity['id']))
    if not doctor or not doctor.calendar:
        return jsonify({'error': 'Calendar not found'}), 404
    
    data = request.get_json()
    if not data or 'date' not in data:
        return jsonify({'error': 'Date is required'}), 400
    
    try:
        target_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        # Получаем все заблокированные слоты на этот день
        slots = TimeSlot.query.filter(
            TimeSlot.calendar_id == doctor.calendar.id,
            TimeSlot.start_time >= start_of_day,
            TimeSlot.start_time <= end_of_day,
            TimeSlot.status == 'blocked'
        ).all()
        
        unblocked_count = 0
        for slot in slots:
            slot.status = 'available'
            unblocked_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'Day opened successfully',
            'date': data['date'],
            'unblocked_slots': unblocked_count
        })
    
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@doctor_api.route('/delete-account', methods=['DELETE'])
@jwt_required()
def api_delete_account():
    """API: Delete doctor account (GDPR compliance)"""
    identity = get_current_user()
    if identity.get('type') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    doctor = Doctor.query.get(uuid.UUID(identity['id']))
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    # Check for active bookings
    now = datetime.utcnow()
    if doctor.calendar:
        active_bookings = Booking.query.join(TimeSlot).filter(
            TimeSlot.calendar_id == doctor.calendar.id,
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
    # but doctor data is anonymized
    
    # Delete future time slots
    if doctor.calendar:
        TimeSlot.query.filter(
            TimeSlot.calendar_id == doctor.calendar.id,
            TimeSlot.start_time > now
        ).delete()
    
    # Anonymize doctor data
    doctor.first_name = "Gelöscht"
    doctor.last_name = str(doctor.id)
    doctor.phone = "deleted"
    doctor.password_hash = None
    doctor.is_verified = False
    
    # Anonymize practice data if exists
    if doctor.practice:
        doctor.practice.name = "Gelöschte Praxis"
        doctor.practice.phone = "deleted"
        doctor.practice.email = None
        doctor.practice.website = None
    
    db.session.commit()
    
    return jsonify({
        'message': 'Account successfully deleted',
        'info': 'Buchungsdaten werden gemäß gesetzlicher Aufbewahrungspflicht aufbewahrt.'
    })
