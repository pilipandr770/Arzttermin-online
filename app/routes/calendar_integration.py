"""
Calendar Integration Routes - API для управления интеграциями календарей
"""
from flask import Blueprint, request, jsonify, redirect, session
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.jwt_helpers import get_current_user
from app import db
from app.models.doctor import Doctor
from app.models.calendar_integration import CalendarIntegration
from app.services.google_calendar_service import GoogleCalendarService
from app.services.apple_calendar_service import AppleCalendarService
from app.services.outlook_calendar_service import OutlookCalendarService
from app.services.calendar_integration_service import get_calendar_service
import uuid
import secrets
from datetime import datetime, timedelta


# In-memory хранилище для OAuth states (для production использовать Redis)
oauth_states = {}


bp = Blueprint('calendar_integration', __name__, url_prefix='/api/doctor/calendar-integrations')


@bp.route('', methods=['GET'])
@jwt_required()
def list_integrations():
    """
    Получить список всех интеграций текущего врача
    
    Response:
        {
            "integrations": [
                {
                    "id": "uuid",
                    "provider": "google",
                    "sync_enabled": true,
                    "last_sync_at": "2026-01-30T10:00:00Z",
                    ...
                }
            ]
        }
    """
    identity = get_current_user()
    if identity.get('type') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    doctor = Doctor.query.get(uuid.UUID(identity['id']))
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    integrations = CalendarIntegration.query.filter_by(doctor_id=doctor.id).all()
    
    return jsonify({
        'integrations': [i.to_dict() for i in integrations]
    })


@bp.route('/connect/<provider>', methods=['POST'])
@jwt_required()
def connect_integration(provider):
    """
    Начать процесс подключения календаря
    
    Для OAuth провайдеров (Google, Outlook): возвращает redirect URL
    Для CalDAV (Apple): принимает credentials напрямую
    
    Args:
        provider: 'google', 'apple', 'outlook', или 'caldav'
    
    Body (для CalDAV):
        {
            "caldav_url": "https://caldav.icloud.com",
            "caldav_username": "user@icloud.com",
            "caldav_password": "app-specific-password"
        }
    
    Response (OAuth):
        {
            "authorization_url": "https://accounts.google.com/..."
        }
    
    Response (CalDAV):
        {
            "success": true,
            "integration_id": "uuid"
        }
    """
    identity = get_current_user()
    if identity.get('type') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    doctor = Doctor.query.get(uuid.UUID(identity['id']))
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    if provider not in ['google', 'apple', 'outlook', 'caldav']:
        return jsonify({'error': 'Invalid provider'}), 400
    
    # Проверить существующую интеграцию
    existing = CalendarIntegration.query.filter_by(
        doctor_id=doctor.id,
        provider=provider
    ).first()
    
    if existing:
        return jsonify({'error': 'Integration already exists. Disconnect first.'}), 400
    
    # CalDAV (Apple) - прямое подключение
    if provider in ['apple', 'caldav']:
        data = request.get_json()
        
        if not all(k in data for k in ['caldav_url', 'caldav_username', 'caldav_password']):
            return jsonify({'error': 'Missing CalDAV credentials'}), 400
        
        try:
            # Создать временную интеграцию для теста (без шифрования пока)
            temp_integration = CalendarIntegration(
                doctor_id=doctor.id,
                provider=provider,
                caldav_url=data['caldav_url'],
                caldav_username=data['caldav_username'],
                caldav_password=data['caldav_password']  # Временно открытый текст
            )
            
            # Тест подключения с открытым паролем
            test_service = AppleCalendarService(temp_integration)
            if not test_service.authenticate():
                return jsonify({'error': 'CalDAV authentication failed. Check credentials.'}), 401
            
            # Если тест успешен, создать реальную интеграцию с шифрованием
            integration = CalendarIntegration(
                doctor_id=doctor.id,
                provider=provider,
                caldav_url=data['caldav_url'],
                caldav_username=data['caldav_username']
            )
            
            # Зашифровать пароль
            service = AppleCalendarService(integration)
            integration.caldav_password = service.encrypt(data['caldav_password'])
            
            # Сохранить интеграцию
            db.session.add(integration)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'integration_id': str(integration.id),
                'integration': integration.to_dict()
            })
            
        except Exception as e:
            print(f"Apple Calendar connection error: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Failed to connect: {str(e)}'}), 500
    
    # OAuth (Google, Outlook)
    else:
        try:
            # Сгенерировать state для защиты от CSRF
            state = secrets.token_urlsafe(32)
            
            # Сохранить state в памяти (вместо session)
            oauth_states[state] = {
                'doctor_id': str(doctor.id),
                'provider': provider,
                'expires_at': datetime.utcnow() + timedelta(minutes=10)
            }
            
            # Получить authorization URL
            if provider == 'google':
                auth_url = GoogleCalendarService.get_authorization_url(state)
            elif provider == 'outlook':
                auth_url = OutlookCalendarService.get_authorization_url(state)
            else:
                return jsonify({'error': 'Unknown OAuth provider'}), 400
            
            return jsonify({
                'authorization_url': auth_url
            })
            
        except Exception as e:
            print(f"Error generating authorization URL for {provider}: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Failed to generate authorization URL: {str(e)}'}), 500


@bp.route('/callback/<provider>', methods=['GET'])
def oauth_callback(provider):
    """
    OAuth callback endpoint
    
    Принимает authorization code и обменивает на токены
    
    Query params:
        code: Authorization code
        state: CSRF protection state
    """
    code = request.args.get('code')
    state = request.args.get('state')
    
    print(f"\n=== OAuth Callback for {provider} ===")
    print(f"State: {state}")
    print(f"Code: {code[:20]}..." if code else "No code")
    print(f"Available states in memory: {list(oauth_states.keys())}")
    
    if not code or not state:
        error_msg = 'Missing code or state'
        print(f"ERROR: {error_msg}")
        return redirect(f'/doctor/calendar-integrations?error={error_msg}')
    
    # Проверить state
    saved_state_data = oauth_states.get(state)
    
    if not saved_state_data:
        error_msg = 'Invalid state. CSRF protection or state expired.'
        print(f"ERROR: {error_msg}")
        return redirect(f'/doctor/calendar-integrations?error={error_msg}')
    
    # Проверить expiration
    if datetime.utcnow() > saved_state_data['expires_at']:
        del oauth_states[state]
        error_msg = 'State expired. Please try again.'
        print(f"ERROR: {error_msg}")
        return redirect(f'/doctor/calendar-integrations?error={error_msg}')
    
    # Проверить provider
    if saved_state_data['provider'] != provider:
        del oauth_states[state]
        error_msg = 'Provider mismatch.'
        print(f"ERROR: {error_msg}")
        return redirect(f'/doctor/calendar-integrations?error={error_msg}')
    
    doctor_id = saved_state_data['doctor_id']
    doctor = Doctor.query.get(uuid.UUID(doctor_id))
    
    # Удалить использованный state
    del oauth_states[state]
    
    if not doctor:
        error_msg = 'Doctor not found'
        print(f"ERROR: {error_msg}")
        return redirect(f'/doctor/calendar-integrations?error={error_msg}')
    
    try:
        # Обменять code на токены
        if provider == 'google':
            tokens = GoogleCalendarService.exchange_code_for_tokens(code)
        elif provider == 'outlook':
            tokens = OutlookCalendarService.exchange_code_for_tokens(code)
        else:
            return jsonify({'error': 'Unknown provider'}), 400
        
        # Создать интеграцию
        integration = CalendarIntegration(
            doctor_id=doctor.id,
            provider=provider,
            oauth_scope=' '.join(tokens.get('scopes', []))
        )
        
        # Зашифровать и сохранить токены используя конкретный сервис
        if provider == 'google':
            service = GoogleCalendarService(integration)
        elif provider == 'outlook':
            service = OutlookCalendarService(integration)
        
        integration.oauth_access_token = service.encrypt(tokens['access_token'])
        if tokens.get('refresh_token'):
            integration.oauth_refresh_token = service.encrypt(tokens['refresh_token'])
        integration.oauth_token_expires_at = tokens.get('expires_at')
        
        db.session.add(integration)
        db.session.commit()
        
        # Настроить webhook если возможно
        try:
            service = get_calendar_service(integration)
            callback_url = request.url_root + f'webhooks/calendar/{provider}'
            if provider == 'google':
                service.setup_webhook(callback_url)
            elif provider == 'outlook':
                service.setup_webhook(callback_url)
        except Exception as e:
            print(f"Failed to setup webhook: {e}")
        
        print(f"SUCCESS: {provider} calendar connected for doctor {doctor.id}")
        
        # Redirect на страницу настроек календаря
        return redirect(f'/doctor/calendar-integrations?success=true&provider={provider}')
        
    except Exception as e:
        error_msg = f'Failed to exchange code: {str(e)}'
        print(f"ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return redirect(f'/doctor/calendar-integrations?error={error_msg}')


@bp.route('/<integration_id>', methods=['GET'])
@jwt_required()
def get_integration(integration_id):
    """
    Получить детали конкретной интеграции
    """
    identity = get_current_user()
    if identity.get('type') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    integration = CalendarIntegration.query.get(uuid.UUID(integration_id))
    
    if not integration or str(integration.doctor_id) != identity['id']:
        return jsonify({'error': 'Integration not found'}), 404
    
    return jsonify(integration.to_dict())


@bp.route('/<integration_id>', methods=['PUT', 'PATCH'])
@jwt_required()
def update_integration(integration_id):
    """
    Обновить настройки интеграции
    
    Body:
        {
            "sync_enabled": true,
            "sync_direction": "both",
            "event_title_template": "Termin mit {patient_name}",
            "auto_block_conflicts": true,
            ...
        }
    """
    identity = get_current_user()
    if identity.get('type') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    integration = CalendarIntegration.query.get(uuid.UUID(integration_id))
    
    if not integration or str(integration.doctor_id) != identity['id']:
        return jsonify({'error': 'Integration not found'}), 404
    
    data = request.get_json()
    
    # Обновляемые поля
    updatable_fields = [
        'sync_enabled', 'sync_direction', 'event_title_template',
        'event_description_template', 'event_color_id', 'event_reminders',
        'import_free_busy', 'import_event_titles', 'auto_block_conflicts'
    ]
    
    for field in updatable_fields:
        if field in data:
            setattr(integration, field, data[field])
    
    db.session.commit()
    
    return jsonify(integration.to_dict())


@bp.route('/<integration_id>', methods=['DELETE'])
@jwt_required()
def delete_integration(integration_id):
    """
    Отключить и удалить интеграцию
    """
    identity = get_current_user()
    if identity.get('type') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    integration = CalendarIntegration.query.get(uuid.UUID(integration_id))
    
    if not integration or str(integration.doctor_id) != identity['id']:
        return jsonify({'error': 'Integration not found'}), 404
    
    # Остановить webhook если есть
    try:
        service = get_calendar_service(integration)
        if integration.provider == 'google':
            service.stop_webhook()
    except Exception as e:
        print(f"Failed to stop webhook: {e}")
    
    # Удалить интеграцию
    db.session.delete(integration)
    db.session.commit()
    
    return jsonify({'success': True})


@bp.route('/<integration_id>/sync', methods=['POST'])
@jwt_required()
def trigger_sync(integration_id):
    """
    Принудительная синхронизация конкретной интеграции
    
    Response:
        {
            "success": true,
            "external_events_count": 5,
            "slots_blocked": 3
        }
    """
    identity = get_current_user()
    if identity.get('type') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    integration = CalendarIntegration.query.get(uuid.UUID(integration_id))
    
    if not integration or str(integration.doctor_id) != identity['id']:
        return jsonify({'error': 'Integration not found'}), 404
    
    try:
        service = get_calendar_service(integration)
        result = service.sync_from_external()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/sync-all', methods=['POST'])
@jwt_required()
def sync_all_integrations():
    """
    Синхронизировать все интеграции текущего врача
    """
    identity = get_current_user()
    if identity.get('type') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    doctor = Doctor.query.get(uuid.UUID(identity['id']))
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    integrations = CalendarIntegration.query.filter_by(
        doctor_id=doctor.id,
        sync_enabled=True,
        sync_status='active'
    ).all()
    
    results = []
    for integration in integrations:
        try:
            service = get_calendar_service(integration)
            result = service.sync_from_external()
            results.append({
                'integration_id': str(integration.id),
                'provider': integration.provider,
                **result
            })
        except Exception as e:
            results.append({
                'integration_id': str(integration.id),
                'provider': integration.provider,
                'success': False,
                'error': str(e)
            })
    
    return jsonify({
        'results': results,
        'total': len(integrations)
    })


# Webhook endpoints для real-time обновлений

@bp.route('/webhooks/calendar/google', methods=['POST'])
def google_webhook():
    """
    Google Calendar Push Notification webhook
    
    Headers:
        X-Goog-Channel-ID: Channel ID
        X-Goog-Resource-State: 'sync', 'exists', 'not_exists'
    """
    channel_id = request.headers.get('X-Goog-Channel-ID')
    resource_state = request.headers.get('X-Goog-Resource-State')
    
    if not channel_id:
        return '', 400
    
    # Найти интеграцию по channel_id
    integration = CalendarIntegration.query.filter_by(
        external_webhook_id=channel_id
    ).first()
    
    if not integration:
        return '', 404
    
    # Sync notification - ничего не делаем
    if resource_state == 'sync':
        return '', 200
    
    # Изменение в календаре - запустить синхронизацию
    if resource_state in ['exists', 'not_exists']:
        try:
            service = GoogleCalendarService(integration)
            service.sync_from_external()
        except Exception as e:
            print(f"Webhook sync error: {e}")
    
    return '', 200


@bp.route('/webhooks/calendar/outlook', methods=['POST'])
def outlook_webhook():
    """
    Microsoft Outlook Calendar webhook
    
    Body:
        {
            "value": [
                {
                    "subscriptionId": "...",
                    "clientState": "terminfinder-secret-state",
                    "changeType": "created",
                    "resource": "...",
                    ...
                }
            ]
        }
    """
    data = request.get_json()
    
    # Validation token для настройки webhook
    if 'validationToken' in request.args:
        return request.args['validationToken'], 200
    
    if not data or 'value' not in data:
        return '', 400
    
    for notification in data['value']:
        subscription_id = notification.get('subscriptionId')
        client_state = notification.get('clientState')
        
        # Проверить clientState
        if client_state != 'terminfinder-secret-state':
            continue
        
        # Найти интеграцию
        integration = CalendarIntegration.query.filter_by(
            external_webhook_id=subscription_id
        ).first()
        
        if not integration:
            continue
        
        # Запустить синхронизацию
        try:
            service = OutlookCalendarService(integration)
            service.sync_from_external()
        except Exception as e:
            print(f"Webhook sync error: {e}")
    
    return '', 200
