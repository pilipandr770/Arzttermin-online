"""
Маршруты врачей
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
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
    identity = get_jwt_identity()
    if identity.get('type') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    doctor = Doctor.query.get(uuid.UUID(identity['id']))
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    # Получаем календарь врача
    calendar = doctor.calendar
    
    # Получаем предстоящие бронирования
    upcoming_bookings = []
    if calendar:
        upcoming_bookings = Booking.query.join(Booking.timeslot).filter(
            Booking.timeslot.has(calendar_id=calendar.id),
            Booking.status.in_(['confirmed', 'pending'])
        ).order_by(Booking.created_at).limit(5).all()
    
    return jsonify({
        'doctor': {
            'id': str(doctor.id),
            'name': f'{doctor.first_name} {doctor.last_name}',
            'speciality': doctor.speciality,
            'is_verified': doctor.is_verified,
            'has_calendar': calendar is not None
        },
        'calendar': {
            'exists': calendar is not None,
            'working_hours': json.loads(calendar.working_hours) if calendar else {},
            'slot_duration': calendar.slot_duration if calendar else 30,
            'buffer_time': calendar.buffer_time if calendar else 5
        } if calendar else {'exists': False},
        'upcoming_bookings': [{
            'id': str(booking.id),
            'patient_name': booking.patient.name if booking.patient else 'Unknown',
            'date': booking.timeslot.start_time.strftime('%Y-%m-%d'),
            'time': booking.timeslot.start_time.strftime('%H:%M'),
            'status': booking.status
        } for booking in upcoming_bookings]
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
    identity = get_jwt_identity()
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
    identity = get_jwt_identity()
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
    identity = get_jwt_identity()
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
            query = query.filter(Booking.timeslot.has(start_time >= from_date))
        except ValueError:
            pass
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Booking.timeslot.has(start_time <= to_date))
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
    identity = get_jwt_identity()
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
    identity = get_jwt_identity()
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
    identity = get_jwt_identity()
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