"""
Chat Route - AI Chatbot Assistant для практик
"""
from flask import Blueprint, request, jsonify, session
from app.models.practice import Practice
from app.models.doctor import Doctor
from app import limiter
import os
import uuid
import json

bp = Blueprint('chat', __name__, url_prefix='/api/chat')


def get_system_prompt(practice: Practice, doctor: Doctor = None) -> str:
    """
    Создает system prompt для AI ассистента практики
    
    Комбинирует:
    - Общую инструкцию для всех ассистентов
    - Данные о практике (адрес, часы работы, контакты)
    - Кастомные инструкции от врача
    """
    
    # Общая инструкция
    base_instruction = """Du bist der AI-Assistent der Arztpraxis. Deine Aufgabe ist es, Patienten freundlich und professionell zu helfen.

Du kannst:
- Informationen über die Praxis geben (Adresse, Öffnungszeiten, Kontaktdaten)
- Häufig gestellte Fragen beantworten
- Wegbeschreibungen und Parkplatzmöglichkeiten erklären
- Über Leistungen und Ausstattung informieren
- Über akzeptierte Versicherungen informieren

Du kannst NICHT:
- Medizinische Diagnosen stellen
- Termine direkt buchen (verweise auf die Terminbuchung)
- Rezepte ausstellen
- Notfälle behandeln (verweise auf Notruf 112)

Antworte immer höflich, kurz und präzise. Bei medizinischen Fragen verweise auf einen Arzttermin."""

    # Информация о практике
    practice_info = f"\n\n=== INFORMATIONEN ÜBER DIE PRAXIS ===\n"
    practice_info += f"Name: {practice.name}\n"
    
    if practice.phone:
        practice_info += f"Telefon: {practice.phone}\n"
    
    if practice.owner_email:
        practice_info += f"Email: {practice.owner_email}\n"
    
    # Адрес
    if practice.address:
        try:
            address = json.loads(practice.address)
            practice_info += f"Adresse: {address.get('street', '')}, {address.get('plz', '')} {address.get('city', '')}\n"
        except:
            practice_info += f"Adresse: {practice.address}\n"
    
    # Часы работы
    if practice.opening_hours:
        try:
            hours = json.loads(practice.opening_hours)
            practice_info += "\nÖffnungszeiten:\n"
            days_de = {
                'monday': 'Montag',
                'tuesday': 'Dienstag',
                'wednesday': 'Mittwoch',
                'thursday': 'Donnerstag',
                'friday': 'Freitag',
                'saturday': 'Samstag',
                'sunday': 'Sonntag'
            }
            for day, times in hours.items():
                day_name = days_de.get(day, day)
                if isinstance(times, list) and times:
                    time_str = ', '.join([f"{t[0]}-{t[1]}" for t in times if isinstance(t, list) and len(t) >= 2])
                    practice_info += f"  {day_name}: {time_str}\n"
                elif isinstance(times, dict):
                    practice_info += f"  {day_name}: {times.get('open', '')}-{times.get('close', '')}\n"
        except:
            pass
    
    # Website
    if practice.website:
        practice_info += f"\nWebsite: {practice.website}\n"
    
    # Парковка
    if practice.parking_info:
        practice_info += f"\nParkmöglichkeiten: {practice.parking_info}\n"
    
    # Общественный транспорт
    if practice.public_transport:
        try:
            transport = json.loads(practice.public_transport)
            if transport:
                practice_info += "\nÖffentliche Verkehrsmittel:\n"
                for t in transport:
                    practice_info += f"  {t.get('type', '').capitalize()} {t.get('line', '')}: Haltestelle {t.get('stop', '')} ({t.get('distance', '')})\n"
        except:
            pass
    
    # Экстренные контакты
    if practice.emergency_phone:
        practice_info += f"\nNotfallkontakt: {practice.emergency_phone}\n"
    
    if practice.whatsapp_number:
        practice_info += f"WhatsApp: {practice.whatsapp_number}\n"
    
    # Особенности
    if practice.features:
        try:
            features = json.loads(practice.features)
            if features:
                practice_info += "\nBesonderheiten:\n"
                feature_names = {
                    'wheelchair_accessible': 'Rollstuhlgerecht',
                    'parking': 'Parkplatz vorhanden',
                    'wifi': 'WLAN für Patienten',
                    'elevator': 'Aufzug vorhanden',
                    'air_conditioning': 'Klimaanlage'
                }
                for f in features:
                    practice_info += f"  - {feature_names.get(f, f)}\n"
        except:
            pass
    
    # Кастомные инструкции от врача
    custom_instructions = ""
    if practice.chatbot_instructions:
        custom_instructions = f"\n\n=== ZUSÄTZLICHE ANWEISUNGEN DES ARZTES ===\n{practice.chatbot_instructions}\n"
    
    return base_instruction + practice_info + custom_instructions


@bp.route('/<practice_id>', methods=['POST'])
@limiter.limit("10 per minute")
def chat_with_practice(practice_id):
    """
    Чат с AI ассистентом практики
    
    ✅ PHASE 3: GDPR-compliant - No history storage, hard scope enforcement
    
    Request JSON:
    {
        "message": "Wie komme ich zu Ihrer Praxis?",
        "session_id": "optional-uuid"  // anonymous session, ephemeral only
    }
    
    Response JSON (SUCCESS):
    {
        "type": "platform_help",
        "medical_advice": false,
        "response": "Antwort vom Assistenten",
        "session_id": "uuid",
        "disclaimer": "Dies ist keine medizinische Beratung..."
    }
    
    Response JSON (BLOCKED):
    {
        "type": "scope_violation",
        "medical_advice": false,
        "response": "Ich kann keine medizinischen Fragen...",
        "reason": "contains_forbidden_keyword",
        "session_id": "uuid"
    }
    """
    try:
        # Получаем практику
        practice = Practice.query.get(uuid.UUID(practice_id))
        if not practice:
            return jsonify({'error': 'Praxis nicht gefunden'}), 404
        
        # Получаем сообщение пользователя
        data = request.get_json()
        if not data or not data.get('message'):
            return jsonify({'error': 'Nachricht ist erforderlich'}), 400
        
        user_message = data.get('message', '').strip()
        if len(user_message) > 1000:
            return jsonify({'error': 'Nachricht ist zu lang (max 1000 Zeichen)'}), 400
        
        # Session ID (anonymous, ephemeral - no DB storage)
        session_id = data.get('session_id') or str(uuid.uuid4())
        
        # ✅ PHASE 3: Pre-validate scope BEFORE enqueuing
        from app.utils.chatbot_scope import validate_scope
        
        is_valid, reason, blocked_response = validate_scope(user_message)
        
        if not is_valid:
            # Return blocked response immediately
            return jsonify({
                'type': 'scope_violation',
                'medical_advice': False,
                'response': blocked_response,
                'reason': reason,
                'session_id': session_id
            }), 200  # 200 OK, not an error - legitimate response
        
        # PHASE 3: Direct OpenAI API call (no Redis/RQ needed)
        # Same approach as help_chat.py - simple, reliable, fast
        
        # SCOPE VALIDATION - Block medical queries
        from app.utils.chatbot_scope import validate_scope
        is_valid, reason, blocked_response = validate_scope(user_message)
        
        if not is_valid:
            print(f"⚠️ Blocked medical query: {reason}")
            return jsonify({
                'type': 'scope_violation',
                'medical_advice': False,
                'response': blocked_response,
                'reason': reason,
                'session_id': session_id
            }), 200
        
        # Call OpenAI API directly
        try:
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if not openai_api_key:
                print("❌ ERROR: OPENAI_API_KEY not configured!")
                return jsonify({
                    'error': 'Der Chatbot-Service ist derzeit nicht verfügbar.',
                    'code': 'config_error'
                }), 503
            
            # Build system prompt with practice context
            system_prompt = get_system_prompt(practice)
            
            # Remove Render.com proxy (blocks OpenAI API)
            proxy_vars = {}
            for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
                if var in os.environ:
                    proxy_vars[var] = os.environ[var]
                    del os.environ[var]
            
            try:
                from openai import OpenAI
                import httpx
                
                # Create httpx client with timeout
                http_client = httpx.Client(timeout=60.0)
                
                client = OpenAI(
                    api_key=openai_api_key,
                    http_client=http_client
                )
                
                print(f"🔍 Calling OpenAI API for practice={practice.name}, session={session_id}")
                
                response = client.chat.completions.create(
                    model=os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview'),
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    timeout=60
                )
                
                assistant_message = response.choices[0].message.content
                
                print(f"✅ Practice chatbot success: practice={practice.name}, response_length={len(assistant_message)}")
                
                return jsonify({
                    'type': 'platform_help',
                    'medical_advice': False,
                    'response': assistant_message,
                    'session_id': session_id,
                    'disclaimer': 'Dies ist keine medizinische Beratung.'
                }), 200
                
            finally:
                # Restore proxy variables
                for key, value in proxy_vars.items():
                    os.environ[key] = value
                    
        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'error': 'Der Chatbot-Service ist derzeit nicht verfügbar. Bitte kontaktieren Sie die Praxis direkt.',
                'code': 'openai_error'
            }), 503
            
    except ValueError:
        return jsonify({'error': 'Ungültige Praxis-ID'}), 400
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            'error': 'Ein unerwarteter Fehler ist aufgetreten',
            'code': 'server_error'
        }), 500


@bp.route('/<practice_id>/reset', methods=['POST'])
def reset_conversation(practice_id):
    """
    Сброс истории разговора (NO-OP - No history stored in Phase 3)
    
    ✅ PHASE 3: Sessions are ephemeral, no persistent storage
    
    Request JSON:
    {
        "session_id": "uuid"  // ignored, sessions are stateless
    }
    
    Response:
    {
        "message": "Sessions sind stateless (keine Historie gespeichert)"
    }
    """
    # NO-OP: We don't store history anymore
    return jsonify({
        'message': 'Sessions sind stateless (keine Historie gespeichert)',
        'gdpr_compliant': True
    })
