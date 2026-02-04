"""
Event Names Registry
====================

Event-style names for background tasks.
Future-ready for event bus architecture (Kafka, RabbitMQ, etc.)
"""

# Appointment/Booking Events
APPOINTMENT_CREATED = 'appointment.created'
APPOINTMENT_CANCELLED = 'appointment.cancelled'
APPOINTMENT_CONFIRMED = 'appointment.confirmed'
APPOINTMENT_REMINDER = 'appointment.reminder'

# Doctor Events
DOCTOR_CREATED = 'doctor.created'
DOCTOR_UPDATED = 'doctor.updated'
DOCTOR_VERIFIED = 'doctor.verified'
DOCTOR_CALENDAR_SYNC = 'doctor.calendar.sync'

# Patient Events
PATIENT_CREATED = 'patient.created'
PATIENT_UPDATED = 'patient.updated'
PATIENT_ALERT_TRIGGERED = 'patient.alert.triggered'

# Practice Events
PRACTICE_CREATED = 'practice.created'
PRACTICE_VERIFIED = 'practice.verified'
PRACTICE_UPDATED = 'practice.updated'

# Calendar Events
CALENDAR_SYNC_REQUESTED = 'calendar.sync.requested'
CALENDAR_EVENT_CREATED = 'calendar.event.created'
CALENDAR_EVENT_UPDATED = 'calendar.event.updated'

# Notification Events
NOTIFICATION_EMAIL_SEND = 'notification.email.send'
NOTIFICATION_SMS_SEND = 'notification.sms.send'

# Chatbot Events
CHATBOT_MESSAGE_RECEIVED = 'chatbot.message.received'
CHATBOT_RESPONSE_GENERATED = 'chatbot.response.generated'

# All events
EVENTS = {
    # Appointments
    'APPOINTMENT_CREATED': APPOINTMENT_CREATED,
    'APPOINTMENT_CANCELLED': APPOINTMENT_CANCELLED,
    'APPOINTMENT_CONFIRMED': APPOINTMENT_CONFIRMED,
    'APPOINTMENT_REMINDER': APPOINTMENT_REMINDER,
    
    # Doctors
    'DOCTOR_CREATED': DOCTOR_CREATED,
    'DOCTOR_UPDATED': DOCTOR_UPDATED,
    'DOCTOR_VERIFIED': DOCTOR_VERIFIED,
    'DOCTOR_CALENDAR_SYNC': DOCTOR_CALENDAR_SYNC,
    
    # Patients
    'PATIENT_CREATED': PATIENT_CREATED,
    'PATIENT_UPDATED': PATIENT_UPDATED,
    'PATIENT_ALERT_TRIGGERED': PATIENT_ALERT_TRIGGERED,
    
    # Practice
    'PRACTICE_CREATED': PRACTICE_CREATED,
    'PRACTICE_VERIFIED': PRACTICE_VERIFIED,
    'PRACTICE_UPDATED': PRACTICE_UPDATED,
    
    # Calendar
    'CALENDAR_SYNC_REQUESTED': CALENDAR_SYNC_REQUESTED,
    'CALENDAR_EVENT_CREATED': CALENDAR_EVENT_CREATED,
    'CALENDAR_EVENT_UPDATED': CALENDAR_EVENT_UPDATED,
    
    # Notifications
    'NOTIFICATION_EMAIL_SEND': NOTIFICATION_EMAIL_SEND,
    'NOTIFICATION_SMS_SEND': NOTIFICATION_SMS_SEND,
    
    # Chatbot
    'CHATBOT_MESSAGE_RECEIVED': CHATBOT_MESSAGE_RECEIVED,
    'CHATBOT_RESPONSE_GENERATED': CHATBOT_RESPONSE_GENERATED,
}
