"""
�������� ������
"""
from flask import Blueprint, jsonify, request
from app.models import Doctor, Calendar, TimeSlot, Practice
from app.constants.specialities import SPECIALITIES
from app.constants.cities import MAJOR_GERMAN_CITIES, GERMAN_STATES
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import math

bp = Blueprint('search', __name__)
search_api = Blueprint('search_api', __name__)


@search_api.route('/doctors/available', methods=['GET'])
def get_available_doctors():
    """
    API: �������� ������ ������ � ����������� ��������� ������
    
    Query params:
    - speciality: ������ �� �������������
    - city: ������ �� ������
    - date_from: ������ ������� (YYYY-MM-DD)
    - date_to: ����� ������� (YYYY-MM-DD)
    - limit: ���������� ����������� (default 20)
    """
    # ��������� ����������
    speciality = request.args.get('speciality')
    city = request.args.get('city')
    date_from_str = request.args.get('date_from')
    date_to_str = request.args.get('date_to')
    limit = int(request.args.get('limit', 20))
    
    # ���� �� ���������: ��������� 7 ����
    if date_from_str:
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
    else:
        date_from = datetime.utcnow()
    
    if date_to_str:
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
    else:
        date_to = date_from + timedelta(days=7)
    
    # ���������: ������� ��������� ������ ��� ������� ���������
    free_slots_subquery = db.session.query(
        TimeSlot.calendar_id,
        func.count(TimeSlot.id).label('free_slots_count')
    ).filter(
        TimeSlot.status == 'available',
        TimeSlot.start_time >= date_from,
        TimeSlot.start_time <= date_to
    ).group_by(TimeSlot.calendar_id).subquery()
    
    # �������� ������: ����� � ����������� ��������� ������
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
    
    # ��������� �������
    if speciality:
        query = query.filter(Doctor.speciality == speciality)
    
    if city:
        # ������ ����� �� ������: ��������� ��������� � JSON ���� address
        # ������������ ��������� ���������� (case-insensitive)
        city_filter = or_(
            func.lower(Practice.address).like(f'%"city": "{city.lower()}"%'),
            func.lower(Practice.address).like(f'%"city":"{city.lower()}"%'),
            func.lower(Practice.address).like(f'%{city.lower()}%')
        )
        query = query.filter(city_filter)
    
    # ����������: ����� � ������� ����������� ������ � ������
    query = query.order_by(func.coalesce(free_slots_subquery.c.free_slots_count, 0).desc())
    
    # ����������� �����������
    results = query.limit(limit).all()
    
    # ������������ ������
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
                'address': practice.address,
                'website': practice.website,
                'google_business_url': practice.google_business_url,
                'phone': practice.phone,
                'description': practice.description
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
    API: �������� ��������� ����� ����������� �����
    
    Query params:
    - date_from: ������ ������� (YYYY-MM-DD)
    - date_to: ����� ������� (YYYY-MM-DD)
    """
    try:
        doctor = Doctor.query.get(doctor_id)
        if not doctor:
            return jsonify({'error': 'Doctor not found'}), 404
        
        if not doctor.calendar:
            return jsonify({'error': 'Doctor has no calendar'}), 404
        
        # ��������� ����������
        date_from_str = request.args.get('date_from')
        date_to_str = request.args.get('date_to')
        
        # ���� �� ���������: ��������� 7 ����
        if date_from_str:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
        else:
            date_from = datetime.utcnow()
        
        if date_to_str:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
        else:
            date_to = date_from + timedelta(days=7)
        
        # �������� ��������� �����
        slots = TimeSlot.query.filter(
            TimeSlot.calendar_id == doctor.calendar.id,
            TimeSlot.status == 'available',
            TimeSlot.start_time >= date_from,
            TimeSlot.start_time <= date_to
        ).order_by(TimeSlot.start_time).all()
        
        # ���������� �� ����
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


@search_api.route('/cities', methods=['GET'])
def search_cities():
    """
    API: Autocomplete ��� �������
    
    Query params:
    - q: ��������� ������ (������� 2 �������)
    - limit: ���������� ����������� (default 10)
    """
    query = request.args.get('q', '').strip()
    limit = int(request.args.get('limit', 10))
    
    if len(query) < 2:
        return jsonify({'cities': MAJOR_GERMAN_CITIES[:limit]})
    
    # ����� �� ������ �������� (case-insensitive)
    query_lower = query.lower()
    matched_cities = [
        city for city in MAJOR_GERMAN_CITIES 
        if city.lower().startswith(query_lower)
    ]
    
    # ���� ��� ���������� �� ������, ���� �� ���������
    if not matched_cities:
        matched_cities = [
            city for city in MAJOR_GERMAN_CITIES 
            if query_lower in city.lower()
        ]
    
    return jsonify({
        'cities': matched_cities[:limit],
        'query': query
    })


@search_api.route('/cities/nearby', methods=['POST'])
def get_nearby_cities():
    """
    API: ����� ��������� ������ �� �����������
    
    Request body:
    - latitude: ������ ������������
    - longitude: ������� ������������
    - radius: ������ ������ � �� (default 50)
    """
    data = request.get_json()
    
    if not data or 'latitude' not in data or 'longitude' not in data:
        return jsonify({'error': 'Latitude and longitude are required'}), 400
    
    user_lat = float(data['latitude'])
    user_lon = float(data['longitude'])
    radius = float(data.get('radius', 50))  # ��
    
    # ����� ������� � �������
    # ���������� ������� Haversine ��� ������� ����������
    practices = Practice.query.filter(
        Practice.latitude.isnot(None),
        Practice.longitude.isnot(None)
    ).all()
    
    nearby_practices = []
    for practice in practices:
        distance = calculate_distance(
            user_lat, user_lon,
            practice.latitude, practice.longitude
        )
        
        if distance <= radius:
            nearby_practices.append({
                'practice_id': str(practice.id),
                'name': practice.name,
                'city': practice.address_dict.get('city'),
                'distance_km': round(distance, 2)
            })
    
    # ��������� �� ����������
    nearby_practices.sort(key=lambda x: x['distance_km'])
    
    return jsonify({
        'practices': nearby_practices,
        'user_location': {
            'latitude': user_lat,
            'longitude': user_lon
        },
        'radius_km': radius
    })


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    ������ ���������� ����� ����� ������� �� ������� Haversine
    ���������� ���������� � ����������
    """
    # ������ ����� � ��
    R = 6371.0
    
    # ������� �������� � �������
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # ������� ���������
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # ������� Haversine
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance
