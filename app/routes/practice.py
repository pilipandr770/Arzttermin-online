"""
Маршруты практик
"""
from flask import Blueprint, render_template, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.utils.jwt_helpers import get_current_user
from app.models import Practice, Doctor
from app import db
import json

bp = Blueprint('practice', __name__)

# API Blueprint для практик
practice_api = Blueprint('practice_api', __name__)


@bp.route('/profile')
def practice_profile():
    """Страница расширенного профиля практики"""
    return render_template('doctor/practice_profile_extended.html')


@practice_api.route('/profile', methods=['GET'])
@jwt_required()
def api_get_practice_profile():
    """API: Получить информацию о практике врача"""
    doctor_id = get_jwt_identity()  # Now it's just the ID string
    claims = get_jwt()
    
    # Проверяем, что это врач
    if claims.get('type') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Получаем доктора
    import uuid
    doctor = Doctor.query.get(uuid.UUID(doctor_id))
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
        'photos': practice.photos if practice.photos else None,
        'verified': practice.verified,
        'stats': {
            'total_appointments': practice.total_appointments,
            'average_rating': round(practice.average_rating, 2) if practice.average_rating else 0
        },
        # Extended fields
        'gallery_photos': practice.gallery_photos_list,
        'video_url': practice.video_url,
        'virtual_tour_url': practice.virtual_tour_url,
        'services': practice.services_list,
        'team_members': practice.team_members_list,
        'equipment': practice.equipment_list,
        'accepted_insurances': practice.accepted_insurances_list,
        'features': practice.features_list,
        'certifications': practice.certifications_list,
        'faq': practice.faq_list,
        'rating_avg': practice.rating_avg,
        'rating_count': practice.rating_count,
        'parking_info': practice.parking_info,
        'public_transport': practice.public_transport_list,
        'emergency_phone': practice.emergency_phone,
        'whatsapp_number': practice.whatsapp_number,
        'telegram_username': practice.telegram_username,
        'meta_title': practice.meta_title,
        'meta_description': practice.meta_description,
        'slug': practice.slug,
        'chatbot_instructions': practice.chatbot_instructions
    })


@practice_api.route('/profile', methods=['PUT'])
@jwt_required()
def api_update_practice_profile():
    """API: Обновить информацию о практике"""
    identity = get_current_user()
    data = request.get_json()
    
    # Проверяем, что это врач
    if identity.get('type') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
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


@practice_api.route('/profile/extended', methods=['PUT'])
@jwt_required()
def api_update_extended_practice_profile():
    """API: Обновить расширенный профиль практики"""
    identity = get_current_user()
    data = request.get_json()
    
    # Проверяем, что это врач
    if identity.get('type') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Получаем доктора и проверяем права
    import uuid
    doctor = Doctor.query.get(uuid.UUID(identity['id']))
    if not doctor or not doctor.practice_id:
        return jsonify({'error': 'Practice not found'}), 404
    
    practice = Practice.query.get(doctor.practice_id)
    if not practice:
        return jsonify({'error': 'Practice not found'}), 404
    
    # Update basic fields
    if 'phone' in data:
        practice.phone = data['phone']
    if 'emergency_phone' in data:
        practice.emergency_phone = data['emergency_phone']
    if 'whatsapp_number' in data:
        practice.whatsapp_number = data['whatsapp_number']
    if 'telegram_username' in data:
        practice.telegram_username = data['telegram_username']
    if 'website' in data:
        practice.website = data['website']
    if 'slug' in data:
        # Validate slug format
        slug = data['slug'].lower().strip()
        if slug and all(c.isalnum() or c == '-' for c in slug):
            practice.slug = slug
    if 'description' in data:
        practice.description = data['description']
    if 'parking_info' in data:
        practice.parking_info = data['parking_info']
    
    # Social media
    if 'social_media' in data:
        practice.social_media_dict = data['social_media']
    
    # Media
    if 'video_url' in data:
        practice.video_url = data['video_url']
    if 'virtual_tour_url' in data:
        practice.virtual_tour_url = data['virtual_tour_url']
    if 'gallery_photos' in data:
        practice.gallery_photos_list = data['gallery_photos']
    
    # Services
    if 'services' in data:
        practice.services_list = data['services']
    
    # Equipment
    if 'equipment' in data:
        practice.equipment_list = data['equipment']
    
    # Insurances
    if 'accepted_insurances' in data:
        practice.accepted_insurances_list = data['accepted_insurances']
    
    # Features
    if 'features' in data:
        practice.features_list = data['features']
    
    # FAQ
    if 'faq' in data:
        practice.faq_list = data['faq']
    
    # Chatbot instructions
    if 'chatbot_instructions' in data:
        practice.chatbot_instructions = data['chatbot_instructions']
    
    # Public transport
    if 'public_transport' in data:
        practice.public_transport_list = data['public_transport']
    
    # SEO fields
    if 'meta_title' in data:
        practice.meta_title = data['meta_title']
    if 'meta_description' in data:
        practice.meta_description = data['meta_description']
    
    try:
        db.session.commit()
        
        # Calculate completeness
        completeness = practice.get_profile_completeness()
        
        return jsonify({
            'message': 'Extended practice profile updated successfully',
            'completeness': completeness,
            'practice': {
                'id': str(practice.id),
                'name': practice.name,
                'slug': practice.slug
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



