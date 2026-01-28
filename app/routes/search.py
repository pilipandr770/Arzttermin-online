"""
Маршруты поиска
"""
from flask import Blueprint, jsonify, request
from app.models import Doctor, Calendar, TimeSlot, Practice
from app.constants import SPECIALITIES
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func, and_

bp = Blueprint('search', __name__)
search_api = Blueprint('search_api', __name__)


@search_api.route('/doctors/available', methods=['GET'])
def get_available_doctors():
    """
    API: Получить список врачей с количеством свободных слотов
    
    Query params:
    - speciality: фильтр по специальности
    - city: фильтр по городу
    - date_from: начало периода (YYYY-MM-DD)
    - date_to: конец периода (YYYY-MM-DD)
    - limit: количество результатов (default 20)
    """
    # Параметры фильтрации
    speciality = request.args.get('speciality')
    city = request.args.get('city')
    date_from_str = request.args.get('date_from')
    date_to_str = request.args.get('date_to')
    limit = int(request.args.get('limit', 20))
    
    # Даты по умолчанию: следующие 7 дней
    if date_from_str:
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
    else:
        date_from = datetime.utcnow()
    
    if date_to_str:
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
    else:
        date_to = date_from + timedelta(days=7)
    
    # Подзапрос: подсчет свободных слотов для каждого календаря
    free_slots_subquery = db.session.query(
        TimeSlot.calendar_id,
        func.count(TimeSlot.id).label('free_slots_count')
    ).filter(
        TimeSlot.status == 'available',
        TimeSlot.start_time >= date_from,
        TimeSlot.start_time <= date_to
    ).group_by(TimeSlot.calendar_id).subquery()
    
    # Основной запрос: врачи с количеством свободных слотов
    query = db.session.query(
        Doctor,
        Calendar,
        Practice,
        func.coalesce(free_slots_subquery.c.free_slots_count, 0).label('free_slots')
    ).join(
        Calendar, Doctor.id == Calendar.doctor_id
    ).outerjoin(
        Practice, Doctor.practice_id == Practice.id
    ).outerjoin(
        free_slots_subquery, Calendar.id == free_slots_subquery.c.calendar_id
    ).filter(
        Doctor.is_verified == True
    )
    
    # Применяем фильтры
    if speciality:
        query = query.filter(Doctor.speciality == speciality)
    
    if city:
        query = query.filter(Practice.city == city)
    
    # Сортировка: врачи с большим количеством слотов в начале
    query = query.order_by(func.coalesce(free_slots_subquery.c.free_slots_count, 0).desc())
    
    # Ограничение результатов
    results = query.limit(limit).all()
    
    # Формирование ответа
    doctors_list = []
    for doctor, calendar, practice, free_slots in results:
        # Get speciality display from constants
        speciality_info = SPECIALITIES.get(doctor.speciality, {})
        speciality_display = speciality_info.get('de', doctor.speciality)
        
        # Parse practice address (it's stored as JSON text)
        practice_data = None
        if practice:
            import json
            try:
                address_json = json.loads(practice.address) if practice.address else {}
            except:
                address_json = {}
            
            practice_data = {
                'id': str(practice.id),
                'name': practice.name,
                'city': address_json.get('city'),
                'address': practice.address
            }
        
        doctors_list.append({
            'id': str(doctor.id),
            'first_name': doctor.first_name,
            'last_name': doctor.last_name,
            'full_name': f"{doctor.first_name} {doctor.last_name}",
            'speciality': doctor.speciality,
            'speciality_display': speciality_display,
            'practice': practice_data,
            'free_slots_count': int(free_slots),
            'has_available_slots': int(free_slots) > 0
        })
    
    return jsonify({
        'doctors': doctors_list,
        'total': len(doctors_list),
        'filters': {
            'speciality': speciality,
            'city': city,
            'date_from': date_from.strftime('%Y-%m-%d'),
            'date_to': date_to.strftime('%Y-%m-%d')
        }
    })


@search_api.route('/doctors/<doctor_id>/slots', methods=['GET'])
def get_doctor_slots(doctor_id):
    """
    API: Получить свободные слоты конкретного врача
    
    Query params:
    - date_from: начало периода (YYYY-MM-DD)
    - date_to: конец периода (YYYY-MM-DD)
    """
    try:
        doctor = Doctor.query.get(doctor_id)
        if not doctor:
            return jsonify({'error': 'Doctor not found'}), 404
        
        if not doctor.calendar:
            return jsonify({'error': 'Doctor has no calendar'}), 404
        
        # Параметры фильтрации
        date_from_str = request.args.get('date_from')
        date_to_str = request.args.get('date_to')
        
        # Даты по умолчанию: следующие 7 дней
        if date_from_str:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
        else:
            date_from = datetime.utcnow()
        
        if date_to_str:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
        else:
            date_to = date_from + timedelta(days=7)
        
        # Получаем свободные слоты
        slots = TimeSlot.query.filter(
            TimeSlot.calendar_id == doctor.calendar.id,
            TimeSlot.status == 'available',
            TimeSlot.start_time >= date_from,
            TimeSlot.start_time <= date_to
        ).order_by(TimeSlot.start_time).all()
        
        # Группируем по дням
        slots_by_date = {}
        for slot in slots:
            date_key = slot.start_time.strftime('%Y-%m-%d')
            if date_key not in slots_by_date:
                slots_by_date[date_key] = []
            
            slots_by_date[date_key].append({
                'id': str(slot.id),
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
                'datetime': slot.start_time.isoformat()
            })
        
        # Get speciality display from constants
        speciality_info = SPECIALITIES.get(doctor.speciality, {})
        speciality_display = speciality_info.get('de', doctor.speciality)
        
        return jsonify({
            'doctor': {
                'id': str(doctor.id),
                'first_name': doctor.first_name,
                'last_name': doctor.last_name,
                'speciality': doctor.speciality,
                'speciality_display': speciality_display
            },
            'slots_by_date': slots_by_date,
            'total_slots': len(slots),
            'period': {
                'date_from': date_from.strftime('%Y-%m-%d'),
                'date_to': date_to.strftime('%Y-%m-%d')
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
