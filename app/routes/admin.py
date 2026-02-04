"""
Admin Routes - Админ-панель управления платформой
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from app.models import Admin, Patient, Doctor, Practice, Booking, TimeSlot, Calendar
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from functools import wraps
import uuid

bp = Blueprint('admin', __name__, url_prefix='/admin')
admin_api = Blueprint('admin_api', __name__, url_prefix='/api/admin')


# ===== WEB ROUTES (HTML Pages) =====

@bp.route('/login')
def login_page():
    """Страница входа для администратора"""
    return render_template('admin/login.html')


@bp.route('/dashboard')
def dashboard_page():
    """Главная страница админ-панели"""
    return render_template('admin/dashboard.html')


@bp.route('/users/patients')
def patients_page():
    """Страница со списком пациентов"""
    return render_template('admin/patients.html')


@bp.route('/users/doctors')
def doctors_page():
    """Страница со списком врачей"""
    return render_template('admin/doctors.html')


@bp.route('/users/patients/<patient_id>')
def patient_detail_page(patient_id):
    """Детальная страница пациента"""
    return render_template('admin/patient_detail.html', patient_id=patient_id)


@bp.route('/users/doctors/<doctor_id>')
def doctor_detail_page(doctor_id):
    """Детальная страница врача"""
    return render_template('admin/doctor_detail.html', doctor_id=doctor_id)


@bp.route('/bookings')
def bookings_page():
    """Страница со списком бронирований"""
    return render_template('admin/bookings.html')


@bp.route('/verifications')
def verifications_page():
    """Страница управления верификацией врачей"""
    return render_template('admin/verifications.html')


@bp.route('/analytics')
def analytics_page():
    """Страница с аналитикой"""
    return render_template('admin/analytics.html')


@bp.route('/')
def index():
    """Редирект на дашборд"""
    return redirect(url_for('admin.dashboard'))


# ===== API ROUTES =====


def admin_required(f):
    """Декоратор для проверки прав администратора"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        identity = get_jwt_identity()
        claims = get_jwt()
        
        # Проверяем, что это админ
        if claims.get('type') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Получаем админа
        admin = Admin.query.get(uuid.UUID(identity))
        if not admin or not admin.is_active:
            return jsonify({'error': 'Admin account not active'}), 403
        
        return f(admin, *args, **kwargs)
    
    return decorated_function


def permission_required(permission):
    """Декоратор для проверки конкретного права доступа"""
    def decorator(f):
        @wraps(f)
        @admin_required
        def decorated_function(admin, *args, **kwargs):
            if not admin.has_permission(permission):
                return jsonify({'error': f'Permission denied: {permission}'}), 403
            return f(admin, *args, **kwargs)
        return decorated_function
    return decorator


# ============= WEB ROUTES =============

@bp.route('/login')
def login():
    """Страница входа для администраторов"""
    return render_template('admin/login.html')


@bp.route('/dashboard')
def dashboard():
    """Главная страница админ-панели"""
    return render_template('admin/dashboard.html')


@bp.route('/users/patients')
def patients_list():
    """Список всех пациентов"""
    return render_template('admin/patients.html')


@bp.route('/users/doctors')
def doctors_list():
    """Список всех врачей"""
    return render_template('admin/doctors.html')


@bp.route('/users/patient/<patient_id>')
def patient_detail(patient_id):
    """Детальная страница пациента"""
    return render_template('admin/patient_detail.html', patient_id=patient_id)


@bp.route('/users/doctor/<doctor_id>')
def doctor_detail(doctor_id):
    """Детальная страница врача"""
    return render_template('admin/doctor_detail.html', doctor_id=doctor_id)


@bp.route('/bookings')
def bookings_list():
    """Список всех бронирований"""
    return render_template('admin/bookings.html')


@bp.route('/verifications')
def verifications():
    """Страница управления верификацией"""
    return render_template('admin/verifications.html')


@bp.route('/payments')
def payments():
    """Страница управления платежами"""
    return render_template('admin/payments.html')


@bp.route('/analytics')
def analytics():
    """Страница аналитики"""
    return render_template('admin/analytics.html')


# ============= API ROUTES =============

@admin_api.route('/login', methods=['POST'])
def api_admin_login():
    """API: Вход администратора"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    # Поиск по username или email
    admin = Admin.query.filter(
        (Admin.username == username) | (Admin.email == username)
    ).first()
    
    # Debug logging
    print(f"Login attempt - Username/Email: {username}")
    print(f"Admin found: {admin is not None}")
    
    if not admin:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Debug password check
    try:
        password_valid = admin.check_password(password)
        print(f"Password valid: {password_valid}")
    except Exception as e:
        print(f"Password check error: {e}")
        return jsonify({'error': 'Authentication error'}), 500
    
    if not password_valid:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not admin.is_active:
        return jsonify({'error': 'Account is deactivated'}), 403
    
    # Обновляем последний вход
    admin.last_login = datetime.utcnow()
    admin.failed_login_attempts = 0
    db.session.commit()
    
    # Создаем токен с типом 'admin'
    access_token = create_access_token(
        identity=str(admin.id),
        additional_claims={'type': 'admin', 'role': admin.role}
    )
    
    return jsonify({
        'access_token': access_token,
        'admin': admin.to_dict()
    })


@admin_api.route('/dashboard/stats', methods=['GET'])
@admin_required
def api_dashboard_stats(admin):
    """API: Статистика для дашборда"""
    
    # Общее количество пользователей
    total_patients = Patient.query.count()
    total_doctors = Doctor.query.count()
    total_practices = Practice.query.count()
    
    # Количество за последние 30 дней
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_patients = Patient.query.filter(Patient.created_at >= thirty_days_ago).count()
    new_doctors = Doctor.query.filter(Doctor.created_at >= thirty_days_ago).count()
    
    # Бронирования
    total_bookings = Booking.query.count()
    active_bookings = Booking.query.filter(Booking.status == 'confirmed').count()
    cancelled_bookings = Booking.query.filter(Booking.status == 'cancelled').count()
    completed_bookings = Booking.query.filter(Booking.status == 'completed').count()
    
    # Бронирования за последние 30 дней
    recent_bookings = Booking.query.filter(Booking.created_at >= thirty_days_ago).count()
    
    # Верификация
    verified_doctors = Doctor.query.filter(Doctor.is_verified == True).count()
    unverified_doctors = Doctor.query.filter(Doctor.is_verified == False).count()
    
    # Доступные слоты
    available_slots = TimeSlot.query.filter(
        TimeSlot.status == 'available',
        TimeSlot.start_time >= datetime.utcnow()
    ).count()
    
    return jsonify({
        'users': {
            'total_patients': total_patients,
            'total_doctors': total_doctors,
            'total_practices': total_practices,
            'new_patients_30d': new_patients,
            'new_doctors_30d': new_doctors
        },
        'bookings': {
            'total': total_bookings,
            'active': active_bookings,
            'cancelled': cancelled_bookings,
            'completed': completed_bookings,
            'recent_30d': recent_bookings
        },
        'verification': {
            'verified_doctors': verified_doctors,
            'unverified_doctors': unverified_doctors
        },
        'slots': {
            'available': available_slots
        }
    })


@admin_api.route('/patients', methods=['GET'])
@admin_required
def api_get_patients(admin):
    """API: Получить список пациентов"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    
    query = Patient.query
    
    # Поиск
    if search:
        query = query.filter(
            or_(
                Patient.phone.like(f'%{search}%'),
                Patient.name.like(f'%{search}%'),
                Patient.email.like(f'%{search}%')
            )
        )
    
    # Пагинация
    pagination = query.order_by(Patient.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    patients = []
    for patient in pagination.items:
        # Подсчет бронирований
        bookings_count = Booking.query.filter_by(patient_id=patient.id).count()
        
        patients.append({
            'id': str(patient.id),
            'phone': patient.phone,
            'name': patient.name or 'N/A',
            'total_bookings': patient.total_bookings or 0,
            'bookings_count': bookings_count,
            'created_at': patient.created_at.isoformat() if patient.created_at else None
        })
    
    return jsonify({
        'patients': patients,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@admin_api.route('/doctors', methods=['GET'])
@admin_required
def api_get_doctors(admin):
    """API: Получить список врачей"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    verified = request.args.get('verified', '')
    
    query = Doctor.query
    
    # Поиск
    if search:
        query = query.filter(
            or_(
                Doctor.first_name.like(f'%{search}%'),
                Doctor.last_name.like(f'%{search}%'),
                Doctor.email.like(f'%{search}%'),
                Doctor.speciality.like(f'%{search}%')
            )
        )
    
    # Фильтр верификации
    if verified == 'true':
        query = query.filter(Doctor.is_verified == True)
    elif verified == 'false':
        query = query.filter(Doctor.is_verified == False)
    
    # Пагинация
    pagination = query.order_by(Doctor.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    doctors = []
    for doctor in pagination.items:
        # Получаем практику
        practice = Practice.query.get(doctor.practice_id) if doctor.practice_id else None
        
        # Подсчет слотов
        calendar = Calendar.query.filter_by(doctor_id=doctor.id).first()
        slots_count = 0
        if calendar:
            slots_count = TimeSlot.query.filter_by(calendar_id=calendar.id).count()
        
        doctors.append({
            'id': str(doctor.id),
            'first_name': doctor.first_name,
            'last_name': doctor.last_name,
            'email': doctor.email,
            'speciality': doctor.speciality,
            'is_verified': doctor.is_verified,
            'practice_name': practice.name if practice else 'N/A',
            'slots_count': slots_count,
            'created_at': doctor.created_at.isoformat() if doctor.created_at else None
        })
    
    return jsonify({
        'doctors': doctors,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@admin_api.route('/patient/<patient_id>', methods=['GET'])
@admin_required
def api_get_patient(admin, patient_id):
    """API: Получить детальную информацию о пациенте"""
    patient = Patient.query.get(uuid.UUID(patient_id))
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Получаем бронирования
    bookings = Booking.query.filter_by(patient_id=patient.id).order_by(Booking.created_at.desc()).all()
    bookings_list = []
    for booking in bookings:
        timeslot = booking.timeslot
        doctor = timeslot.calendar.doctor if timeslot else None
        
        bookings_list.append({
            'id': str(booking.id),
            'booking_code': booking.booking_code,
            'status': booking.status,
            'doctor_name': f'{doctor.first_name} {doctor.last_name}' if doctor else 'N/A',
            'date': timeslot.start_time.strftime('%Y-%m-%d') if timeslot else None,
            'time': timeslot.start_time.strftime('%H:%M') if timeslot else None,
            'created_at': booking.created_at.isoformat()
        })
    
    return jsonify({
        'id': str(patient.id),
        'phone': patient.phone,
        'name': patient.name,
        'email': patient.email,
        'stripe_customer_id': patient.stripe_customer_id,
        'created_at': patient.created_at.isoformat() if patient.created_at else None,
        'bookings': bookings_list
    })


@admin_api.route('/doctor/<doctor_id>', methods=['GET'])
@admin_required
def api_get_doctor(admin, doctor_id):
    """API: Получить детальную информацию о враче"""
    doctor = Doctor.query.get(uuid.UUID(doctor_id))
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    # Получаем практику
    practice = Practice.query.get(doctor.practice_id) if doctor.practice_id else None
    
    # Получаем календарь и слоты
    calendar = Calendar.query.filter_by(doctor_id=doctor.id).first()
    slots_stats = {
        'total': 0,
        'available': 0,
        'booked': 0
    }
    
    if calendar:
        slots_stats['total'] = TimeSlot.query.filter_by(calendar_id=calendar.id).count()
        slots_stats['available'] = TimeSlot.query.filter_by(
            calendar_id=calendar.id, status='available'
        ).count()
        slots_stats['booked'] = TimeSlot.query.filter_by(
            calendar_id=calendar.id, status='booked'
        ).count()
    
    return jsonify({
        'id': str(doctor.id),
        'first_name': doctor.first_name,
        'last_name': doctor.last_name,
        'email': doctor.email,
        'speciality': doctor.speciality,
        'is_verified': doctor.is_verified,
        'tax_number': doctor.tax_number,
        'practice': {
            'id': str(practice.id) if practice else None,
            'name': practice.name if practice else None,
            'verified': practice.verified if practice else False
        } if practice else None,
        'slots': slots_stats,
        'created_at': doctor.created_at.isoformat() if doctor.created_at else None
    })


@admin_api.route('/doctor/<doctor_id>/verify', methods=['POST'])
@permission_required('manage_verifications')
def api_verify_doctor(admin, doctor_id):
    """API: Верифицировать врача"""
    doctor = Doctor.query.get(uuid.UUID(doctor_id))
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    doctor.is_verified = True
    db.session.commit()
    
    return jsonify({
        'message': 'Doctor verified successfully',
        'doctor_id': str(doctor.id)
    })


@admin_api.route('/doctor/<doctor_id>/unverify', methods=['POST'])
@permission_required('manage_verifications')
def api_unverify_doctor(admin, doctor_id):
    """API: Снять верификацию с врача"""
    doctor = Doctor.query.get(uuid.UUID(doctor_id))
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    doctor.is_verified = False
    db.session.commit()
    
    return jsonify({
        'message': 'Doctor verification removed',
        'doctor_id': str(doctor.id)
    })


@admin_api.route('/patient/<patient_id>', methods=['DELETE'])
@permission_required('manage_users')
def api_delete_patient(admin, patient_id):
    """API: Удалить пациента"""
    patient = Patient.query.get(uuid.UUID(patient_id))
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Проверяем активные бронирования
    active_bookings = Booking.query.filter_by(
        patient_id=patient.id, status='confirmed'
    ).count()
    
    if active_bookings > 0:
        return jsonify({
            'error': f'Cannot delete patient with {active_bookings} active bookings'
        }), 400
    
    db.session.delete(patient)
    db.session.commit()
    
    return jsonify({'message': 'Patient deleted successfully'})


@admin_api.route('/doctor/<doctor_id>', methods=['DELETE'])
@permission_required('manage_users')
def api_delete_doctor(admin, doctor_id):
    """API: Удалить врача"""
    doctor = Doctor.query.get(uuid.UUID(doctor_id))
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    # Проверяем активные бронирования
    calendar = Calendar.query.filter_by(doctor_id=doctor.id).first()
    if calendar:
        active_bookings = db.session.query(Booking).join(TimeSlot).filter(
            TimeSlot.calendar_id == calendar.id,
            Booking.status == 'confirmed'
        ).count()
        
        if active_bookings > 0:
            return jsonify({
                'error': f'Cannot delete doctor with {active_bookings} active bookings'
            }), 400
    
    db.session.delete(doctor)
    db.session.commit()
    
    return jsonify({'message': 'Doctor deleted successfully'})


@admin_api.route('/bookings', methods=['GET'])
@admin_required
def api_get_bookings(admin):
    """API: Получить список бронирований"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    status = request.args.get('status', '')
    
    query = Booking.query.join(TimeSlot).join(Calendar).join(Doctor)
    
    # Фильтр по статусу
    if status:
        query = query.filter(Booking.status == status)
    
    # Пагинация
    pagination = query.order_by(Booking.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    bookings = []
    for booking in pagination.items:
        patient = booking.patient
        timeslot = booking.timeslot
        doctor = timeslot.calendar.doctor if timeslot else None
        
        bookings.append({
            'id': str(booking.id),
            'booking_code': booking.booking_code,
            'status': booking.status,
            'patient_name': patient.name or patient.phone,
            'doctor_name': f'{doctor.first_name} {doctor.last_name}' if doctor else 'N/A',
            'date': timeslot.start_time.strftime('%Y-%m-%d') if timeslot else None,
            'time': timeslot.start_time.strftime('%H:%M') if timeslot else None,
            'created_at': booking.created_at.isoformat()
        })
    
    return jsonify({
        'bookings': bookings,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })
