"""
Chatbot Tasks
=============

Background tasks for AI chatbot message processing.
OpenAI API calls can be slow, so we handle them asynchronously.

✅ PHASE 3: GDPR-compliant - No personal data storage, hard scope enforcement
"""

import openai
import os
from app import db
from app.models import Doctor, Practice
from app.utils.chatbot_scope import validate_scope, ALLOWED_INTENTS
from datetime import datetime


def process_chatbot_message(message, practice_id=None, doctor_id=None, session_id=None):
    """
    Process chatbot message with OpenAI (GDPR-compliant)
    
    Event: chatbot.message.received
    Priority: medium
    
    ✅ PHASE 3 COMPLIANCE:
    - NO chat history storage
    - Hard scope enforcement (ALLOWED_INTENTS)
    - Structured responses with medical_advice flag
    - Anonymous session_id (no persistence)
    
    Args:
        message: str - User message
        practice_id: UUID - Practice context (optional)
        doctor_id: UUID - Doctor context (optional)
        session_id: str - Anonymous session UUID (ephemeral)
    
    Returns:
        dict with structured response
    """
    print(f"🚀 RQ WORKER: process_chatbot_message started - practice_id={practice_id}, session={session_id}")
    print(f"🚀 Message: '{message[:50]}...'")
    
    from app import create_app
    app = create_app()
    
    with app.app_context():
        print(f"🚀 App context created")
        
        # SCOPE VALIDATION - Block medical queries
        is_valid, reason, blocked_response = validate_scope(message)
        
        print(f"🚀 Scope validation: valid={is_valid}, reason={reason if not is_valid else 'OK'}")
        
        if not is_valid:
            return {
                'status': 'blocked',
                'type': 'scope_violation',
                'medical_advice': False,
                'response': blocked_response,
                'reason': reason,
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Get context
        practice = None
        doctor = None
        
        print(f"🚀 Fetching practice/doctor context...")
        
        if practice_id:
            practice = Practice.query.get(practice_id)
            print(f"🚀 Practice loaded: {practice.name if practice else 'NOT FOUND'}")
        
        if doctor_id:
            doctor = Doctor.query.get(doctor_id)
            if doctor and doctor.practice:
                practice = doctor.practice
            print(f"🚀 Doctor loaded: {doctor.user.email if doctor else 'NOT FOUND'}")
        
        # Build system prompt with HARD restrictions
        system_prompt = _build_gdpr_safe_system_prompt(practice, doctor)
        
        # Call OpenAI (stateless - no history)
        try:
            openai_api_key = os.getenv('OPENAI_API_KEY')
            
            print(f"🔍 Starting OpenAI API call for practice={practice.name if practice else 'None'}, session={session_id}")
            print(f"🔍 API key present: {bool(openai_api_key)}, length: {len(openai_api_key) if openai_api_key else 0}")
            
            if not openai_api_key:
                print("❌ ERROR: OPENAI_API_KEY not configured!")
                return {
                    'status': 'error',
                    'error': 'OpenAI API key not configured',
                    'session_id': session_id,
                    'medical_advice': False
                }
            
            # ✅ RENDER.COM FIX: Remove proxy vars that block OpenAI API
            proxy_vars = {}
            for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
                if key in os.environ:
                    proxy_vars[key] = os.environ[key]
                    del os.environ[key]
            
            try:
                # NO HISTORY - only current message
                # Use OpenAI v1.x client syntax
                print(f"🔍 Creating OpenAI client...")
                
                import httpx
                http_client = httpx.Client(
                    timeout=60.0,
                    follow_redirects=True
                )
                
                client = openai.OpenAI(
                    api_key=openai_api_key,
                    http_client=http_client
                )
                
                print(f"🔍 Calling OpenAI API (model=gpt-4, timeout=60s)...")
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    temperature=0.7,
                    max_tokens=500,
                    timeout=60  # 60 second timeout for OpenAI API
                )
                
                print(f"🔍 OpenAI API response received!")
                assistant_message = response.choices[0].message.content
            finally:
                # Restore proxy vars
                for key, value in proxy_vars.items():
                    os.environ[key] = value
            
            print(f"✅ Practice chatbot success: practice={practice.name if practice else 'None'}, response_length={len(assistant_message)}")
            
            # Structured response
            return {
                'status': 'success',
                'type': 'platform_help',
                'medical_advice': False,  # ALWAYS false
                'response': assistant_message,
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat(),
                'disclaimer': 'Dies ist keine medizinische Beratung. Wenden Sie sich für medizinische Fragen an einen Arzt.'
            }
            
        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'error': str(e),
                'session_id': session_id,
                'medical_advice': False
            }


def _build_gdpr_safe_system_prompt(practice, doctor):
    """
    Build GDPR-compliant system prompt with HARD medical restrictions
    
    ✅ PHASE 3: Hardened disclaimers and scope enforcement
    """
    base_prompt = f"""
Du bist ein hilfreicher Assistent für die TerminFinder-Plattform.

🚫 ABSOLUTES VERBOT - DU DARFST NIEMALS:
- Medizinische Diagnosen stellen oder interpretieren
- Symptome deuten oder Krankheiten identifizieren
- Medikamente empfehlen oder über Nebenwirkungen sprechen
- Behandlungsratschläge geben
- Testergebnisse erklären
- Bei Notfällen helfen (verweise auf 112)
- Gesundheitsfragen beantworten

✅ ERLAUBT - DU DARFST NUR:
- Informationen über die Plattform TerminFinder geben
- Erklären wie man einen Termin bucht
- Praxisinformationen teilen (Adresse, Öffnungszeiten, Kontakt)
- Wegbeschreibungen geben
- Bei Account-Verwaltung helfen

WICHTIG: Wenn jemand nach IRGENDETWAS Medizinischem fragt, antworte:
"Ich kann keine medizinischen Fragen beantworten. Bitte wenden Sie sich direkt an einen Arzt. Notruf: 112"

ERLAUBTE THEMEN ({', '.join(ALLOWED_INTENTS)}):
"""
    
    if practice:
        # Add practice-specific context
        practice_info = f"""

PRAXIS INFORMATION:
Name: {practice.name}
"""
        
        # Address (may be JSON or string)
        if practice.address:
            try:
                import json
                address_data = json.loads(practice.address) if isinstance(practice.address, str) else practice.address
                if isinstance(address_data, dict):
                    street = address_data.get('street', '')
                    plz = address_data.get('plz', '')
                    city = address_data.get('city', '')
                    practice_info += f"Adresse: {street}, {plz} {city}\n"
                else:
                    practice_info += f"Adresse: {practice.address}\n"
            except:
                practice_info += f"Adresse: {practice.address}\n"
        
        if practice.phone:
            practice_info += f"Telefon: {practice.phone}\n"
        
        if practice.owner_email:
            practice_info += f"Email: {practice.owner_email}\n"
        
        if practice.website:
            practice_info += f"Website: {practice.website}\n"
        
        # Opening hours (may be JSON)
        if practice.opening_hours:
            try:
                import json
                hours = json.loads(practice.opening_hours) if isinstance(practice.opening_hours, str) else practice.opening_hours
                if isinstance(hours, dict):
                    practice_info += "\nÖffnungszeiten:\n"
                    days_de = {
                        'monday': 'Montag', 'tuesday': 'Dienstag', 'wednesday': 'Mittwoch',
                        'thursday': 'Donnerstag', 'friday': 'Freitag', 'saturday': 'Samstag', 'sunday': 'Sonntag'
                    }
                    for day, times in hours.items():
                        day_name = days_de.get(day, day)
                        if isinstance(times, list) and times:
                            time_str = ', '.join([f"{t[0]}-{t[1]}" for t in times if isinstance(t, list) and len(t) >= 2])
                            practice_info += f"  {day_name}: {time_str}\n"
                else:
                    practice_info += f"\nÖffnungszeiten: {practice.opening_hours}\n"
            except:
                practice_info += f"\nÖffnungszeiten: {practice.opening_hours}\n"
        
        # Parking info
        if practice.parking_info:
            practice_info += f"\nParkmöglichkeiten: {practice.parking_info}\n"
        
        # Public transport (may be JSON)
        if practice.public_transport:
            try:
                import json
                transport = json.loads(practice.public_transport) if isinstance(practice.public_transport, str) else practice.public_transport
                if isinstance(transport, list) and transport:
                    practice_info += "\nÖffentliche Verkehrsmittel:\n"
                    for t in transport:
                        if isinstance(t, dict):
                            practice_info += f"  {t.get('type', '').capitalize()} {t.get('line', '')}: Haltestelle {t.get('stop', '')} ({t.get('distance', '')})\n"
            except:
                pass
        
        # Emergency contacts
        if practice.emergency_phone:
            practice_info += f"\nNotfallkontakt: {practice.emergency_phone}\n"
        
        if practice.whatsapp_number:
            practice_info += f"WhatsApp: {practice.whatsapp_number}\n"
        
        # Custom instructions from practice
        if practice.chatbot_instructions:
            practice_info += f"\nZusätzliche Anweisungen:\n{practice.chatbot_instructions}\n"
        
        base_prompt += practice_info
    
    if doctor:
        doctor_info = f"""

ARZT INFORMATION:
Name: Dr. {doctor.first_name} {doctor.last_name}
Fachgebiet: {doctor.speciality}
"""
        base_prompt += doctor_info
    
    # Final hard disclaimer
    base_prompt += """

WICHTIG: Beginne JEDE Antwort mit einem Hinweis, dass dies keine medizinische Beratung ist.
Antworte kurz und präzise nur zu erlaubten Themen.
"""
    
    return base_prompt


def process_help_chatbot_message(message, context_type='general', context_id=None):
    """
    Process help chatbot message (platform assistance)
    
    Event: chatbot.message.received
    Priority: low
    
    ✅ PHASE 3: GDPR-compliant, no personal data
    
    Args:
        message: str - User message
        context_type: str - 'general', 'booking', 'profile', 'search'
        context_id: str - Context-specific ID (optional)
    
    Returns:
        dict with response
    """
    from app import create_app
    app = create_app()
    
    with app.app_context():
        # SCOPE VALIDATION
        is_valid, reason, blocked_response = validate_scope(message)
        
        if not is_valid:
            return {
                'status': 'blocked',
                'type': 'scope_violation',
                'medical_advice': False,
                'response': blocked_response,
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        system_prompt = """
Du bist ein hilfreicher Assistent für die TerminFinder-Plattform.

Du hilfst Benutzern bei:
- Suche nach Ärzten
- Terminbuchung
- Profilverwaltung
- Navigation auf der Website

🚫 DU DARFST KEINE medizinischen Fragen beantworten.

Antworte kurz und freundlich auf Deutsch oder Ukrainisch.
Beginne mit: "ℹ️ Dies ist keine medizinische Beratung."
"""
        
        try:
            openai.api_key = os.getenv('OPENAI_API_KEY')
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=300,
                timeout=60  # 60 second timeout for OpenAI API
            )
            
            assistant_message = response.choices[0].message.content
            
            return {
                'status': 'success',
                'type': 'platform_help',
                'medical_advice': False,
                'response': assistant_message,
                'context_type': context_type,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'context_type': context_type,
                'medical_advice': False
            }
