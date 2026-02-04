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
    from app import create_app
    app = create_app()
    
    with app.app_context():
        # SCOPE VALIDATION - Block medical queries
        is_valid, reason, blocked_response = validate_scope(message)
        
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
        
        if practice_id:
            practice = Practice.query.get(practice_id)
        
        if doctor_id:
            doctor = Doctor.query.get(doctor_id)
            if doctor and doctor.practice:
                practice = doctor.practice
        
        # Build system prompt with HARD restrictions
        system_prompt = _build_gdpr_safe_system_prompt(practice, doctor)
        
        # Call OpenAI (stateless - no history)
        try:
            openai.api_key = os.getenv('OPENAI_API_KEY')
            
            # NO HISTORY - only current message
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            assistant_message = response.choices[0].message.content
            
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
        
        if practice.full_address_string:
            practice_info += f"Adresse: {practice.full_address_string}\n"
        
        if practice.phone:
            practice_info += f"Telefon: {practice.phone}\n"
        
        if practice.email:
            practice_info += f"Email: {practice.email}\n"
        
        if practice.opening_hours:
            practice_info += f"\nÖffnungszeiten: {practice.opening_hours}\n"
        
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
                max_tokens=300
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
