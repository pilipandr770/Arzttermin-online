"""
Константы приложения: специальности врачей, языки и т.д.
"""

# Специальности врачей
SPECIALITIES = {
    'general_practitioner': {
        'de': 'Allgemeinmediziner / Hausarzt',
        'en': 'General Practitioner',
        'ru': 'Терапевт',
        'icon': '🩺',
        'category': 'primary_care'
    },
    'dentist': {
        'de': 'Zahnarzt',
        'en': 'Dentist',
        'ru': 'Стоматолог',
        'icon': '🦷',
        'category': 'dental'
    },
    'gynecologist': {
        'de': 'Frauenarzt / Gynäkologe',
        'en': 'Gynecologist',
        'ru': 'Гинеколог',
        'icon': '👶',
        'category': 'specialist'
    },
    'pediatrician': {
        'de': 'Kinderarzt / Pädiater',
        'en': 'Pediatrician',
        'ru': 'Педиатр',
        'icon': '👶',
        'category': 'primary_care'
    },
    'dermatologist': {
        'de': 'Hautarzt / Dermatologe',
        'en': 'Dermatologist',
        'ru': 'Дерматолог',
        'icon': '🔬',
        'category': 'specialist'
    },
    'orthopedist': {
        'de': 'Orthopäde',
        'en': 'Orthopedist',
        'ru': 'Ортопед',
        'icon': '🦴',
        'category': 'specialist'
    },
    'ophthalmologist': {
        'de': 'Augenarzt / Ophthalmologe',
        'en': 'Ophthalmologist',
        'ru': 'Офтальмолог',
        'icon': '👁️',
        'category': 'specialist'
    },
    'ent_specialist': {
        'de': 'HNO-Arzt',
        'en': 'ENT Specialist',
        'ru': 'ЛОР',
        'icon': '👂',
        'category': 'specialist'
    },
    'internist': {
        'de': 'Internist',
        'en': 'Internist',
        'ru': 'Интернист',
        'icon': '🫀',
        'category': 'specialist'
    },
    'cardiologist': {
        'de': 'Kardiologe',
        'en': 'Cardiologist',
        'ru': 'Кардиолог',
        'icon': '❤️',
        'category': 'specialist'
    },
    'urologist': {
        'de': 'Urologe',
        'en': 'Urologist',
        'ru': 'Уролог',
        'icon': '💊',
        'category': 'specialist'
    },
    'neurologist': {
        'de': 'Neurologe',
        'en': 'Neurologist',
        'ru': 'Невролог',
        'icon': '🧠',
        'category': 'specialist'
    },
    'psychiatrist': {
        'de': 'Psychiater',
        'en': 'Psychiatrist',
        'ru': 'Психиатр',
        'icon': '🧠',
        'category': 'mental_health'
    },
    'psychotherapist': {
        'de': 'Psychotherapeut',
        'en': 'Psychotherapist',
        'ru': 'Психотерапевт',
        'icon': '💭',
        'category': 'mental_health'
    },
    'radiologist': {
        'de': 'Radiologe',
        'en': 'Radiologist',
        'ru': 'Рентгенолог',
        'icon': '📸',
        'category': 'diagnostic'
    },
    'gastroenterologist': {
        'de': 'Gastroenterologe',
        'en': 'Gastroenterologist',
        'ru': 'Гастроэнтеролог',
        'icon': '🔬',
        'category': 'specialist'
    },
    'endocrinologist': {
        'de': 'Endokrinologe',
        'en': 'Endocrinologist',
        'ru': 'Эндокринолог',
        'icon': '⚕️',
        'category': 'specialist'
    },
    'rheumatologist': {
        'de': 'Rheumatologe',
        'en': 'Rheumatologist',
        'ru': 'Ревматолог',
        'icon': '🦴',
        'category': 'specialist'
    },
    'pulmonologist': {
        'de': 'Pneumologe / Lungenfacharzt',
        'en': 'Pulmonologist',
        'ru': 'Пульмонолог',
        'icon': '🫁',
        'category': 'specialist'
    },
    'physiotherapist': {
        'de': 'Physiotherapeut',
        'en': 'Physiotherapist',
        'ru': 'Физиотерапевт',
        'icon': '🤸',
        'category': 'therapy'
    },
    'surgeon': {
        'de': 'Chirurg',
        'en': 'Surgeon',
        'ru': 'Хирург',
        'icon': '🔪',
        'category': 'surgical'
    },
    'other': {
        'de': 'Andere Fachrichtung',
        'en': 'Other Specialty',
        'ru': 'Другая специальность',
        'icon': '➕',
        'category': 'other',
        'requires_custom_input': True
    }
}

# Категории специальностей (для группировки в UI)
SPECIALITY_CATEGORIES = {
    'primary_care': {
        'de': 'Hausärzte',
        'en': 'Primary Care',
        'ru': 'Первичная помощь'
    },
    'dental': {
        'de': 'Zahnmedizin',
        'en': 'Dental',
        'ru': 'Стоматология'
    },
    'specialist': {
        'de': 'Fachärzte',
        'en': 'Specialists',
        'ru': 'Специалисты'
    },
    'mental_health': {
        'de': 'Psychische Gesundheit',
        'en': 'Mental Health',
        'ru': 'Психическое здоровье'
    },
    'therapy': {
        'de': 'Therapie',
        'en': 'Therapy',
        'ru': 'Терапия'
    },
    'surgical': {
        'de': 'Chirurgie',
        'en': 'Surgery',
        'ru': 'Хирургия'
    },
    'diagnostic': {
        'de': 'Diagnostik',
        'en': 'Diagnostic',
        'ru': 'Диагностика'
    },
    'other': {
        'de': 'Andere',
        'en': 'Other',
        'ru': 'Другое'
    }
}

# Поддерживаемые языки
SUPPORTED_LANGUAGES = [
    ('de', 'Deutsch'),
    ('en', 'English'),
    ('ru', 'Русский'),
    ('fr', 'Français'),
    ('es', 'Español'),
    ('tr', 'Türkçe'),
    ('ar', 'العربية'),
    ('pl', 'Polski'),
    ('it', 'Italiano'),
]

# Временные предпочтения
TIME_PREFERENCES = [
    ('morning', 'Vormittag (08:00-12:00)'),
    ('afternoon', 'Nachmittag (12:00-17:00)'),
    ('evening', 'Abend (17:00-20:00)'),
]

# Статусы бронирования
BOOKING_STATUSES = [
    ('confirmed', 'Bestätigt'),
    ('cancelled', 'Storniert'),
    ('completed', 'Abgeschlossen'),
    ('no_show', 'Nicht erschienen'),
]

# Статусы слотов
SLOT_STATUSES = [
    ('free', 'Frei'),
    ('booked', 'Gebucht'),
    ('blocked', 'Blockiert'),
]
