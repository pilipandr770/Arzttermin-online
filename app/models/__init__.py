"""
Database Models для TerminFinder
"""
from app.models.utils import get_table_args
from app.models.practice import Practice
from app.models.doctor import Doctor
from app.models.calendar import Calendar, TimeSlot
from app.models.calendar_integration import CalendarIntegration
from app.models.patient import Patient
from app.models.patient_alert import PatientAlert
from app.models.booking import Booking
from app.models.practice_review import PracticeReview

__all__ = [
    'Practice',
    'Doctor',
    'Calendar',
    'TimeSlot',
    'CalendarIntegration',
    'Patient',
    'PatientAlert',
    'Booking',
    'PracticeReview',
]
