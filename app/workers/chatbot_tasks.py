"""
Chatbot Tasks
=============

Background tasks for AI chatbot message processing.
OpenAI API calls can be slow, so we handle them asynchronously.

⚠️ GDPR WARNING: This module will be refactored in Phase 3 to remove personal data storage.
"""

import openai
import os
from app import db
from app.models import Doctor, Practice
from datetime import datetime


def process_chatbot_message(message, practice_id=None, doctor_id=None, session_id=None):
    """
    Process chatbot message with OpenAI
    
    Event: chatbot.message.received
    Priority: medium
    
    ⚠️ PHASE 3 TODO:
    - Remove chat history storage
    - Add hard scope enforcement (ALLOWED_INTENTS)
    - Return structured responses with medical_advice flag
    
    Args:
        message: str - User message
        practice_id: UUID - Practice context (optional)
        doctor_id: UUID - Doctor context (optional)
        session_id: str - Session UUID (no persistent storage)
    
    Returns:
        dict with response
    """
    from app import create_app
    app = create_app()
    
    with app.app_context():
        # Get context
        practice = None
        doctor = None
        
        if practice_id:
            practice = Practice.query.get(practice_id)
        
        if doctor_id:
            doctor = Doctor.query.get(doctor_id)
            if doctor and doctor.practice:
                practice = doctor.practice
        
        # Build system prompt
        system_prompt = _build_system_prompt(practice, doctor)
        
        # Call OpenAI
        try:
            openai.api_key = os.getenv('OPENAI_API_KEY')
            
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
            
            return {
                'status': 'success',
                'response': assistant_message,
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'session_id': session_id
            }


def _build_system_prompt(practice, doctor):
    """
    Build system prompt with practice/doctor context
    
    ⚠️ PHASE 3 TODO: Harden medical disclaimers and scope enforcement
    """
    base_prompt = """
Du bist ein hilfreicher Assistent für die TerminFinder-Plattform.

WICHTIG - DEINE GRENZEN:
- Du darfst KEINE medizinischen Ratschläge, Diagnosen oder Behandlungsempfehlungen geben
- Du darfst KEINE Symptome interpretieren oder Medikamente empfehlen
- Du darfst NUR über die Plattform, Terminbuchung und allgemeine Praxisinformationen sprechen

ERLAUBTE THEMEN:
- Wie man einen Termin bucht
- Wo sich die Praxis befindet
- Öffnungszeiten
- Kontaktinformationen
- Navigation auf der Plattform
- Profilverwaltung

Bei medizinischen Fragen antworte immer:
"Ich kann keine medizinischen Ratschläge geben. Bitte wenden Sie sich direkt an einen Arzt."
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
    
    return base_prompt


def process_help_chatbot_message(message, context_type='general', context_id=None):
    """
    Process help chatbot message (platform assistance)
    
    Event: chatbot.message.received
    Priority: low
    
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
        system_prompt = """
Du bist ein hilfreicher Assistent für die TerminFinder-Plattform.

Du hilfst Benutzern bei:
- Suche nach Ärzten
- Terminbuchung
- Profilverwaltung
- Navigation auf der Website

Du darfst KEINE medizinischen Fragen beantworten.

Antworte kurz und freundlich auf Deutsch oder Ukrainisch.
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
                'response': assistant_message,
                'context_type': context_type,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'context_type': context_type
            }
