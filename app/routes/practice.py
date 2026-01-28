"""
Маршруты практик
"""
from flask import Blueprint, render_template, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Practice, Doctor
from app import db
import json

bp = Blueprint('practice', __name__)

# API Blueprint для практик
practice_api = Blueprint('practice_api', __name__)


@bp.route('/profile')
def practice_profile():
    """Страница профиля практики"""
    return render_template('doctor/practice_profile.html')


@practice_api.route('/profile', methods=['GET'])
@jwt_required()
def api_get_practice_profile():
    """API: Получить информацию о практике врача"""
    identity = get_jwt_identity()
    
    # Получаем доктора
    import uuid
    doctor = Doctor.query.get(uuid.UUID(identity['id']))
    if not doctor or not doctor.practice_id:
        return jsonify({'error': 'Practice not found'}), 404
    
    practice = Practice.query.get(doctor.practice_id)
    if not practice:
        return jsonify({'error': 'Practice not found'}), 404
    
    # Возвращаем расширенную информацию
    return jsonify({
        'id': str(practice.id),
        'name': practice.name,
        'vat_number': practice.vat_number,
        'phone': practice.phone,
        'owner_email': practice.owner_email,
        'address': practice.address_dict,
        'website': practice.website,
        'google_business_url': practice.google_business_url,
        'description': practice.description,
        'opening_hours': practice.opening_hours_dict,
        'social_media': practice.social_media_dict,
        'photos': practice.photos_list,
        'verified': practice.verified,
        'stats': {
            'total_appointments': practice.total_appointments,
            'average_rating': round(practice.average_rating, 2) if practice.average_rating else 0
        }
    })


@practice_api.route('/profile', methods=['PUT'])
@jwt_required()
def api_update_practice_profile():
    """API: Обновить информацию о практике"""
    identity = get_jwt_identity()
    data = request.get_json()
    
    # Получаем доктора и проверяем права
    import uuid
    doctor = Doctor.query.get(uuid.UUID(identity['id']))
    if not doctor or not doctor.practice_id:
        return jsonify({'error': 'Practice not found'}), 404
    
    practice = Practice.query.get(doctor.practice_id)
    if not practice:
        return jsonify({'error': 'Practice not found'}), 404
    
    # Обновляем только разрешенные поля
    if 'website' in data:
        practice.website = data['website']
    
    if 'google_business_url' in data:
        practice.google_business_url = data['google_business_url']
    
    if 'description' in data:
        practice.description = data['description']
    
    if 'phone' in data:
        practice.phone = data['phone']
    
    if 'opening_hours' in data:
        practice.opening_hours_dict = data['opening_hours']
    
    if 'social_media' in data:
        practice.social_media_dict = data['social_media']
    
    if 'photos' in data:
        practice.photos_list = data['photos']
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Practice profile updated successfully',
            'practice': {
                'id': str(practice.id),
                'name': practice.name,
                'website': practice.website,
                'google_business_url': practice.google_business_url,
                'description': practice.description
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
