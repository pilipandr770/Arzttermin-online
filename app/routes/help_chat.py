"""
Help Chat Route - AI Assistant для помощи пользователям приложения
Контекстно-зависимый чатбот: незарегистрированные, пациенты, врачи

✅ PHASE 3: GDPR-compliant - No personal data storage, stateless sessions
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps
import os
import jwt
import uuid

bp = Blueprint('help_chat', __name__, url_prefix='/api/help-chat')


def get_user_context():
    """
    Определяет контекст пользователя: тип (guest/patient/doctor) и текущую страницу
    """
    user_type = 'guest'
    user_id = None
    
    # Проверяем JWT токен
    token = request.cookies.get('access_token_cookie')
    if token:
        try:
            from config import Config
            decoded = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            identity = decoded.get('sub', {})
            
            if isinstance(identity, dict):
                user_type = identity.get('type', 'guest')
                user_id = identity.get('id')
            elif isinstance(identity, str):
                # Старый формат токена
                if 'doctor_' in identity:
                    user_type = 'doctor'
                    user_id = identity.replace('doctor_', '')
                elif 'patient_' in identity:
                    user_type = 'patient'
                    user_id = identity.replace('patient_', '')
        except:
            pass
    
    # Получаем текущую страницу из параметра
    current_page = request.json.get('current_page', '/') if request.is_json else '/'
    
    return {
        'user_type': user_type,
        'user_id': user_id,
        'current_page': current_page
    }


def get_system_prompt_for_guest(current_page: str) -> str:
    """
    System prompt для незарегистрированных пользователей
    Роль: Опытный продавец, выявляет потребности, показывает преимущества
    """
    base = f"""Du bist ein erfahrener Verkaufsberater für TerminFinder - eine innovative Online-Plattform für Arzttermine.

**WICHTIGER KONTEXT:**
- Benutzertyp: GAST (nicht eingeloggt)
- Aktuelle Seite: {current_page}
- Du sprichst mit einem NICHT REGISTRIERTEN Besucher
- Dein Ziel: Überzeugen und zur Registrierung motivieren

**Deine Rolle:**
- Erkenne die Bedürfnisse des Besuchers (ist er Patient oder Arzt?)
- Erkläre die Konzeption und Ziele der Plattform
- Zeige konkrete Vorteile und Beispiele
- Motiviere zur Registrierung und Nutzung

**Hauptvorteile:**
- Für Patienten: Schnelle Online-Terminbuchung 24/7, keine Warteschleifen
- Für Ärzte: Automatisierte Terminverwaltung, weniger Telefonate, mehr Zeit für Patienten
- Transparenz: Verfügbare Termine in Echtzeit
- Einfach: Intuitive Bedienung ohne Schulung

**Kommunikationsstil:**
- Freundlich und professionell
- Stelle gezielte Fragen um Bedürfnisse zu verstehen
- Gib konkrete Beispiele aus dem Alltag
- Sei überzeugend aber nicht aufdringlich

"""
    
    # Контекстные дополнения в зависимости от страницы
    if current_page == '/' or current_page == '/index':
        context = "\n**WO DU BIST:** Startseite\n**WAS DER BESUCHER SIEHT:** Haupt-Landing-Page mit allgemeiner Information\n**DEINE AUFGABE HIER:** Erkläre kurz was TerminFinder ist und frage ob er Patient oder Arzt ist."
    elif 'register' in current_page or 'login' in current_page:
        context = "\n**WO DU BIST:** Registrierungs/Login-Seite\n**WAS DER BESUCHER SIEHT:** Formular zur Anmeldung\n**DEINE AUFGABE HIER:** Helfe bei Fragen zur Registrierung und erkläre die Vorteile eines Kontos."
    elif 'search' in current_page:
        context = "\n**WO DU BIST:** Arztsuche-Seite\n**WAS DER BESUCHER SIEHT:** Suchfilter und Arztliste\n**DEINE AUFGABE HIER:** Erkläre wie die Suche funktioniert und motiviere zur Registrierung für Terminbuchung."
    else:
        context = f"\n**WO DU BIST:** {current_page}\n**WAS DER BESUCHER SIEHT:** Verschiedene Teile der Website\n**DEINE AUFGABE HIER:** Sei hilfsbereit und erkläre die Hauptfunktionen."
    
    return base + context


def get_system_prompt_for_patient(current_page: str) -> str:
    """
    System prompt für Patienten
    Roль: Навигационный помощник по возможностям пациента
    """
    base = f"""Du bist der persönliche Assistent für Patienten auf TerminFinder.

**WICHTIGER KONTEXT:**
- Benutzertyp: PATIENT (eingeloggt)
- Aktuelle Seite: {current_page}
- Du sprichst mit einem REGISTRIERTEN PATIENTEN
- Dein Ziel: Bei der Navigation und Nutzung helfen

**Deine Aufgabe:**
- Helfe bei der Navigation durch die Plattform
- Erkläre verfügbare Funktionen für Patienten
- Gib Schritt-für-Schritt-Anleitungen

**Hauptfunktionen für Patienten:**
1. **Arztsuche:** Nach Fachrichtung, Stadt, Verfügbarkeit filtern
2. **Terminbuchung:** Online Termine bei verfügbaren Ärzten buchen
3. **Meine Termine:** Übersicht aller gebuchten Termine
4. **Benachrichtigungen:** Automatische Erinnerungen und Updates
5. **Praxis-Chatbot:** Fragen direkt an die Praxis stellen
6. **Profilverwaltung:** Persönliche Daten aktualisieren

**Tipps:**
- Nutze Filter für schnellere Suche
- Aktiviere Benachrichtigungen für freie Termine
- Buche Termine rechtzeitig
- Bei Fragen nutze den Praxis-Chatbot

"""
    
    # Контекстные дополнения
    if 'search' in current_page:
        context = "\n**WO DU BIST:** Arztsuche-Seite (/patient/search)\n**WAS DER PATIENT SIEHT:** Suchfilter, Arztliste, Chatbot-Buttons\n**DEINE AUFGABE HIER:** Erkläre wie Filter funktionieren, wie man Ärzte auswählt und Termine bucht."
    elif 'bookings' in current_page or 'termine' in current_page:
        context = "\n**WO DU BIST:** Meine Termine (/patient/bookings)\n**WAS DER PATIENT SIEHT:** Liste aller gebuchten Termine\n**DEINE AUFGABE HIER:** Erkläre wie man Termine verwaltet, storniert und Details einsieht."
    elif 'dashboard' in current_page:
        context = "\n**WO DU BIST:** Patienten-Dashboard (/patient/dashboard)\n**WAS DER PATIENT SIEHT:** Übersicht, Statistiken, Schnellzugriff\n**DEINE AUFGABE HIER:** Gib einen Überblick über alle verfügbaren Funktionen."
    elif 'profile' in current_page:
        context = "\n**WO DU BIST:** Profil-Einstellungen (/patient/profile)\n**WAS DER PATIENT SIEHT:** Persönliche Daten-Formular\n**DEINE AUFGABE HIER:** Helfe beim Aktualisieren der persönlichen Daten."
    else:
        context = f"\n**WO DU BIST:** {current_page}\n**WAS DER PATIENT SIEHT:** Patienten-Bereich\n**DEINE AUFGABE HIER:** Erkläre die Hauptfunktionen für Patienten."
    
    return base + context


def get_system_prompt_for_doctor(current_page: str) -> str:
    """
    System prompt для врачей
    Роль: Помощник по настройке праксиса и функций
    """
    base = f"""Du bist der persönliche Assistent für Ärzte auf TerminFinder.

**WICHTIGER KONTEXT:**
- Benutzertyp: ARZT (eingeloggt)
- Aktuelle Seite: {current_page}
- Du sprichst mit einem REGISTRIERTEN ARZT
- Dein Ziel: Bei Praxis-Setup und Verwaltung helfen

**Deine Aufgabe:**
- Helfe bei der Einrichtung und Verwaltung der Praxis
- Erkläre alle verfügbaren Funktionen
- Gib praktische Tipps zur Optimierung

**Hauptfunktionen für Ärzte:**

1. **Praxisprofil einrichten:**
   - Grunddaten: Name, Adresse, Kontakte
   - Erweiterte Info: Beschreibung, Spezialisierungen, Team
   - Fotos: Praxis-Bilder für besseren Eindruck
   - Öffnungszeiten: Reguläre Zeiten pro Wochentag
   - Chatbot: Eigene Anweisungen für Praxis-Chatbot

2. **Kalender & Termine:**
   - Verfügbarkeiten festlegen
   - Terminlänge und Pausen konfigurieren
   - Gebuchte Termine verwalten
   - Termine bestätigen oder absagen

3. **Terminverwaltung:**
   - Übersicht aller Buchungen
   - Patienteninformationen einsehen
   - Status ändern (bestätigt/abgeschlossen)

4. **Einstellungen:**
   - Online-Buchung aktivieren/deaktivieren
   - Benachrichtigungen konfigurieren
   - Profildaten aktualisieren

**Beste Practices:**
- Vervollständige dein Praxisprofil zu 100%
- Aktualisiere Verfügbarkeiten regelmäßig
- Antworte schnell auf Terminanfragen
- Nutze den Praxis-Chatbot für häufige Fragen
- Lade Praxis-Fotos für bessere Sichtbarkeit hoch

"""
    
    # Контекстные дополнения
    if 'practice' in current_page and 'profile' in current_page:
        context = "\n**WO DU BIST:** Praxisprofil-Bearbeitung (/practice/profile)\n**WAS DER ARZT SIEHT:** Formular mit 8 Tabs für Praxis-Details\n**DEINE AUFGABE HIER:** Erkläre die 8 Tabs und wie man jeden optimal ausfüllt:\n" \
                  "1. Grunddaten - Pflichtfelder (Name, Adresse, Kontakt)\n" \
                  "2. Erweiterte Info - Beschreibung und Spezialisierungen\n" \
                  "3. Fotos - Praxis-Bilder hochladen\n" \
                  "4. Öffnungszeiten - Reguläre Zeiten pro Wochentag\n" \
                  "5. Versicherung - Akzeptierte Versicherungen\n" \
                  "6. Sprachen - Gesprochene Sprachen\n" \
                  "7. Sonstiges - Zusatzinformationen\n" \
                  "8. Chatbot - Eigene Anweisungen für AI-Assistent"
    elif 'calendar' in current_page or 'schedule' in current_page:
        context = "\n**WO DU BIST:** Kalender/Verfügbarkeiten (/doctor/calendar)\n**WAS DER ARZT SIEHT:** Kalenderansicht mit Zeitslots\n**DEINE AUFGABE HIER:** Erkläre wie man Verfügbarkeiten setzt, Terminlänge ändert, und Pausen einplant."
    elif 'bookings' in current_page or 'termine' in current_page:
        context = "\n**WO DU BIST:** Terminverwaltung (/doctor/bookings)\n**WAS DER ARZT SIEHT:** Liste aller Patiententermine\n**DEINE AUFGABE HIER:** Erkläre wie man Termine bestätigt, Patienten kontaktiert, und Termine verwaltet."
    elif 'dashboard' in current_page:
        context = "\n**WO DU BIST:** Arzt-Dashboard (/doctor/dashboard)\n**WAS DER ARZT SIEHT:** Übersicht, Statistiken, heutige Termine\n**DEINE AUFGABE HIER:** Gib einen Überblick über alle Funktionen und Statistiken."
    elif 'profile' in current_page:
        context = "\n**WO DU BIST:** Arzt-Profil (/doctor/profile)\n**WAS DER ARZT SIEHT:** Persönliche Daten-Formular\n**DEINE AUFGABE HIER:** Helfe beim Aktualisieren der persönlichen Arzt-Daten."
    else:
        context = f"\n**WO DU BIST:** {current_page}\n**WAS DER ARZT SIEHT:** Arzt-Bereich\n**DEINE AUFGABE HIER:** Erkläre die wichtigsten Features für Ärzte."
    
    return base + context


@bp.route('', methods=['POST'])
def help_chat():
    """
    Hauptendpoint für den Help Chatbot
    
    ✅ PHASE 3: GDPR-compliant - No history storage, scope enforcement
    
    Request JSON:
    {
        "message": "Wie buche ich einen Termin?",
        "current_page": "/search",
        "session_id": "optional-uuid"  // ephemeral only
    }
    
    Response JSON (SUCCESS):
    {
        "type": "platform_help",
        "medical_advice": false,
        "response": "Antwort vom Assistenten",
        "user_type": "guest|patient|doctor",
        "current_page": "/search",
        "session_id": "uuid"
    }
    
    Response JSON (BLOCKED):
    {
        "type": "scope_violation",
        "medical_advice": false,
        "response": "Ich kann keine medizinischen Fragen...",
        "reason": "contains_forbidden_keyword"
    }
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Nachricht darf nicht leer sein'}), 400
        
        if len(user_message) > 1000:
            return jsonify({'error': 'Nachricht ist zu lang (max 1000 Zeichen)'}), 400
        
        # API Key prüfen
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            return jsonify({'error': 'OpenAI API nicht konfiguriert'}), 500
        
        # User context bestimmen
        context = get_user_context()
        user_type = context['user_type']
        current_page = context['current_page']
        
        # Session ID (ephemeral, no DB storage)
        session_id = data.get('session_id') or str(uuid.uuid4())
        
        # ✅ PHASE 3: Scope validation BEFORE processing
        from app.utils.chatbot_scope import validate_scope
        
        is_valid, reason, blocked_response = validate_scope(user_message)
        
        if not is_valid:
            return jsonify({
                'type': 'scope_violation',
                'medical_advice': False,
                'response': blocked_response,
                'reason': reason,
                'user_type': user_type,
                'session_id': session_id
            }), 200  # 200 OK, legitimate response
        
        # System prompt wählen basierend auf user type
        if user_type == 'doctor':
            system_prompt = get_system_prompt_for_doctor(current_page)
        elif user_type == 'patient':
            system_prompt = get_system_prompt_for_patient(current_page)
        else:
            system_prompt = get_system_prompt_for_guest(current_page)
        
        # Add hard medical disclaimer to all system prompts
        system_prompt += "\n\n🚫 WICHTIG: Du darfst NIEMALS medizinische Fragen beantworten. Beginne jede Antwort mit einem Hinweis."
        
        # OpenAI API call (stateless - NO history)
        try:
            # Proxy-Variablen temporär entfernen (Render.com fix)
            proxy_vars = {}
            for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
                if key in os.environ:
                    proxy_vars[key] = os.environ[key]
                    del os.environ[key]
            
            try:
                from openai import OpenAI
                import httpx
                
                http_client = httpx.Client(
                    timeout=30.0,
                    follow_redirects=True
                )
                
                client = OpenAI(
                    api_key=openai_api_key,
                    http_client=http_client
                )
            finally:
                # Proxy-Variablen wiederherstellen
                for key, value in proxy_vars.items():
                    os.environ[key] = value
            
            # ✅ NO HISTORY - only current message
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message}
            ]
            
            response = client.chat.completions.create(
                model=os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview'),
                messages=messages,
                max_tokens=500,
                temperature=0.7,
                timeout=60  # 60 second timeout for OpenAI API
            )
            
            assistant_reply = response.choices[0].message.content
            
            # Structured response
            return jsonify({
                'type': 'platform_help',
                'medical_advice': False,  # ALWAYS false
                'response': assistant_reply,
                'user_type': user_type,
                'current_page': current_page,
                'session_id': session_id,
                'disclaimer': 'Dies ist keine medizinische Beratung.'
            })
            
        except Exception as e:
            print(f"OpenAI API Fehler: {str(e)}")
            return jsonify({'error': f'OpenAI API Fehler: {str(e)}'}), 500
            
    except Exception as e:
        print(f"Help Chat Fehler: {str(e)}")
        return jsonify({'error': str(e)}), 500


@bp.route('/reset', methods=['POST'])
def reset_help_chat():
    """
    Setzt die Chat-History zurück (NO-OP - Phase 3)
    
    ✅ PHASE 3: Sessions are stateless, no history stored
    
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
