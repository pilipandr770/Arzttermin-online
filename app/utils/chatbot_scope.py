"""
Chatbot Scope Configuration
============================

GDPR-compliant chatbot restrictions.
NO medical advice, diagnosis, or treatment recommendations.
"""

# Allowed intents - ONLY these topics are permitted
ALLOWED_INTENTS = [
    'platform_usage',      # How to use TerminFinder
    'booking_help',        # How to book appointments
    'practice_info',       # Practice location, hours, contact
    'directions',          # How to get to practice
    'profile_help',        # Account management
    'general_greeting',    # Hello, thank you, etc.
]

# Forbidden keywords - Block medical queries
FORBIDDEN_KEYWORDS = [
    # German medical terms
    'diagnose', 'diagnosen', 'diagnostik',
    'behandlung', 'behandeln', 'therapie', 'heilung',
    'medikament', 'medikamente', 'arznei', 'tablette', 'pille',
    'symptom', 'symptome', 'krankheit', 'schmerz', 'schmerzen',
    'rezept', 'verschreibung', 'verordnung',
    'operation', 'eingriff', 'chirurgie',
    'untersuchung', 'befund', 'testergebnis',
    'impfung', 'immunisierung',
    'notfall', 'akut', 'dringend',
    
    # English medical terms (some users may use)
    'diagnosis', 'diagnose', 'treatment', 'therapy',
    'medication', 'medicine', 'prescription', 'drug',
    'symptom', 'pain', 'disease', 'illness',
    'surgery', 'operation', 'test result',
    'emergency', 'urgent',
    
    # Ukrainian medical terms
    'діагноз', 'лікування', 'ліки', 'препарат',
    'симптом', 'біль', 'хвороба', 'захворювання',
    'рецепт', 'операція', 'аналіз',
]

# Response templates
BLOCKED_RESPONSE_DE = """
❌ Tut mir leid, ich kann keine medizinischen Fragen beantworten.

Ich bin nur ein Assistent für die Plattform TerminFinder und kann Ihnen bei folgenden Themen helfen:
• Terminbuchung
• Praxisinformationen (Adresse, Öffnungszeiten)
• Wegbeschreibung
• Nutzung der Plattform

Für medizinische Fragen wenden Sie sich bitte direkt an einen Arzt.
📞 Notruf: 112
"""

BLOCKED_RESPONSE_UK = """
❌ Вибачте, я не можу відповідати на медичні питання.

Я лише асистент платформи TerminFinder і можу допомогти з:
• Запис на прийом
• Інформація про практику (адреса, години роботи)
• Як дістатися
• Використання платформи

Для медичних питань зверніться безпосередньо до лікаря.
📞 Екстрена служба: 112
"""

BLOCKED_RESPONSE_EN = """
❌ Sorry, I cannot answer medical questions.

I'm only a TerminFinder platform assistant and can help with:
• Appointment booking
• Practice information (address, hours)
• Directions
• Platform usage

For medical questions, please contact a doctor directly.
📞 Emergency: 112
"""

def detect_language(message):
    """Detect message language (simple heuristic)"""
    message_lower = message.lower()
    
    # Ukrainian detection
    ukrainian_chars = any(c in message for c in 'іїєґ')
    if ukrainian_chars:
        return 'uk'
    
    # German common words
    german_words = ['wie', 'ich', 'sind', 'der', 'die', 'das', 'ist', 'zur']
    if any(word in message_lower.split() for word in german_words):
        return 'de'
    
    # Default to German (main language)
    return 'de'


def get_blocked_response(message):
    """Get appropriate blocked response based on language"""
    lang = detect_language(message)
    
    if lang == 'uk':
        return BLOCKED_RESPONSE_UK
    elif lang == 'en':
        return BLOCKED_RESPONSE_EN
    else:
        return BLOCKED_RESPONSE_DE


def contains_forbidden_keyword(message):
    """Check if message contains forbidden medical keywords"""
    message_lower = message.lower()
    
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in message_lower:
            return True, keyword
    
    return False, None


def validate_scope(message):
    """
    Validate if message is within allowed scope.
    
    Returns:
        (is_valid, reason, blocked_response)
    """
    # Check for forbidden keywords first
    has_forbidden, keyword = contains_forbidden_keyword(message)
    
    if has_forbidden:
        return False, f"Forbidden keyword: {keyword}", get_blocked_response(message)
    
    # If no forbidden keywords, allow (we trust OpenAI's system prompt)
    return True, None, None
