"""
Calendar Sync Tasks
===================

Background tasks for calendar synchronization with external providers
(Google Calendar, Outlook Calendar, Apple Calendar).

All blocking API calls are handled here asynchronously.
"""

from app import db
from app.models import CalendarIntegration, Doctor, TimeSlot
from datetime import datetime, timedelta
import json


def sync_calendar_to_external(doctor_id, date_from=None, date_to=None):
    """
    Sync doctor's TerminFinder slots to external calendar
    
    Event: doctor.calendar.sync
    Priority: medium
    
    Args:
        doctor_id: Doctor ID
        date_from: Start date (defaults to today)
        date_to: End date (defaults to +30 days)
    """
    from app import create_app
    app = create_app()
    
    with app.app_context():
        doctor = Doctor.query.get(doctor_id)
        if not doctor or not doctor.calendar:
            return {'error': 'Doctor or calendar not found'}
        
        # Default date range
        if not date_from:
            date_from = datetime.now().date()
        if not date_to:
            date_to = date_from + timedelta(days=30)
        
        # Get all active calendar integrations
        integrations = CalendarIntegration.query.filter_by(
            doctor_id=doctor_id,
            is_active=True
        ).all()
        
        if not integrations:
            return {'status': 'skipped', 'reason': 'no active integrations'}
        
        # Get slots to sync
        slots = TimeSlot.query.filter(
            TimeSlot.calendar_id == doctor.calendar.id,
            TimeSlot.start_time >= datetime.combine(date_from, datetime.min.time()),
            TimeSlot.start_time <= datetime.combine(date_to, datetime.max.time()),
            TimeSlot.status.in_(['available', 'booked'])
        ).all()
        
        synced_count = 0
        errors = []
        
        for integration in integrations:
            try:
                if integration.provider == 'google':
                    result = _sync_to_google(integration, slots)
                elif integration.provider == 'outlook':
                    result = _sync_to_outlook(integration, slots)
                elif integration.provider == 'apple':
                    result = _sync_to_apple(integration, slots)
                else:
                    continue
                
                integration.last_sync_at = datetime.utcnow()
                synced_count += 1
                
            except Exception as e:
                errors.append({
                    'provider': integration.provider,
                    'error': str(e)
                })
        
        db.session.commit()
        
        return {
            'status': 'completed',
            'doctor_id': doctor_id,
            'synced_count': synced_count,
            'errors': errors
        }


def _sync_to_google(integration, slots):
    """
    Sync slots to Google Calendar
    
    Args:
        integration: CalendarIntegration object
        slots: List of TimeSlot objects
    """
    from app.services.google_calendar_service import GoogleCalendarService
    
    service = GoogleCalendarService(integration)
    
    for slot in slots:
        event_data = {
            'summary': f'TerminFinder: {"Available" if slot.status == "available" else "Booked"}',
            'start': {
                'dateTime': slot.start_time.isoformat(),
                'timeZone': 'Europe/Berlin',
            },
            'end': {
                'dateTime': slot.end_time.isoformat(),
                'timeZone': 'Europe/Berlin',
            },
            'description': f'Slot ID: {slot.id}',
            'colorId': '2' if slot.status == 'available' else '11',  # Green for available, red for booked
        }
        
        # Check if event already exists
        if slot.external_event_id:
            # Update existing event
            service.update_event(slot.external_event_id, event_data)
        else:
            # Create new event
            event = service.create_event(event_data)
            slot.external_event_id = event.get('id')
    
    return {'status': 'success', 'slots_synced': len(slots)}


def _sync_to_outlook(integration, slots):
    """
    Sync slots to Outlook Calendar
    
    Args:
        integration: CalendarIntegration object
        slots: List of TimeSlot objects
    """
    from app.services.outlook_calendar_service import OutlookCalendarService
    
    service = OutlookCalendarService(integration)
    
    for slot in slots:
        event_data = {
            'subject': f'TerminFinder: {"Вільно" if slot.status == "available" else "Заброньовано"}',
            'start': {
                'dateTime': slot.start_time.isoformat(),
                'timeZone': 'Europe/Berlin',
            },
            'end': {
                'dateTime': slot.end_time.isoformat(),
                'timeZone': 'Europe/Berlin',
            },
            'body': {
                'contentType': 'HTML',
                'content': f'<p>Slot ID: {slot.id}</p>'
            },
        }
        
        if slot.external_event_id:
            service.update_event(slot.external_event_id, event_data)
        else:
            event = service.create_event(event_data)
            slot.external_event_id = event.get('id')
    
    return {'status': 'success', 'slots_synced': len(slots)}


def _sync_to_apple(integration, slots):
    """
    Sync slots to Apple Calendar (CalDAV)
    
    Args:
        integration: CalendarIntegration object
        slots: List of TimeSlot objects
    """
    from app.services.apple_calendar_service import AppleCalendarService
    
    service = AppleCalendarService(integration)
    
    for slot in slots:
        # CalDAV uses iCalendar format
        event_data = {
            'summary': f'TerminFinder: {"Доступно" if slot.status == "available" else "Заброньовано"}',
            'dtstart': slot.start_time,
            'dtend': slot.end_time,
            'description': f'Slot ID: {slot.id}',
        }
        
        if slot.external_event_id:
            service.update_event(slot.external_event_id, event_data)
        else:
            event = service.create_event(event_data)
            slot.external_event_id = event.get('uid')
    
    return {'status': 'success', 'slots_synced': len(slots)}


def sync_external_to_terminfinder(doctor_id):
    """
    Import events from external calendar to TerminFinder
    (Creates blocking slots for existing appointments)
    
    Event: calendar.sync.requested
    Priority: low
    
    Args:
        doctor_id: Doctor ID
    """
    from app import create_app
    app = create_app()
    
    with app.app_context():
        doctor = Doctor.query.get(doctor_id)
        if not doctor or not doctor.calendar:
            return {'error': 'Doctor or calendar not found'}
        
        integrations = CalendarIntegration.query.filter_by(
            doctor_id=doctor_id,
            is_active=True
        ).all()
        
        if not integrations:
            return {'status': 'skipped', 'reason': 'no active integrations'}
        
        imported_count = 0
        
        for integration in integrations:
            try:
                if integration.provider == 'google':
                    events = _import_from_google(integration)
                elif integration.provider == 'outlook':
                    events = _import_from_outlook(integration)
                elif integration.provider == 'apple':
                    events = _import_from_apple(integration)
                else:
                    continue
                
                # Create blocked slots for external events
                for event in events:
                    # Check if slot already exists
                    existing_slot = TimeSlot.query.filter_by(
                        calendar_id=doctor.calendar.id,
                        external_event_id=event['id']
                    ).first()
                    
                    if not existing_slot:
                        new_slot = TimeSlot(
                            calendar_id=doctor.calendar.id,
                            start_time=event['start'],
                            end_time=event['end'],
                            status='blocked',
                            external_event_id=event['id']
                        )
                        db.session.add(new_slot)
                        imported_count += 1
                
            except Exception as e:
                print(f"Failed to import from {integration.provider}: {e}")
        
        db.session.commit()
        
        return {
            'status': 'completed',
            'doctor_id': doctor_id,
            'imported_count': imported_count
        }


def _import_from_google(integration):
    """Import events from Google Calendar"""
    from app.services.google_calendar_service import GoogleCalendarService
    service = GoogleCalendarService(integration)
    return service.get_events(time_min=datetime.now(), time_max=datetime.now() + timedelta(days=30))


def _import_from_outlook(integration):
    """Import events from Outlook Calendar"""
    from app.services.outlook_calendar_service import OutlookCalendarService
    service = OutlookCalendarService(integration)
    return service.get_events(time_min=datetime.now(), time_max=datetime.now() + timedelta(days=30))


def _import_from_apple(integration):
    """Import events from Apple Calendar (CalDAV)"""
    from app.services.apple_calendar_service import AppleCalendarService
    service = AppleCalendarService(integration)
    return service.get_events(time_min=datetime.now(), time_max=datetime.now() + timedelta(days=30))
