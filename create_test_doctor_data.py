"""
Script to create test doctor data for development and production
Creates a test doctor with calendar and time slots
"""
import os
import json
from datetime import datetime, timedelta
from app import create_app, db
from app.models import Doctor, Calendar, TimeSlot, Patient

def create_test_doctor_data():
    """Create test doctor with calendar and slots"""
    app = create_app()

    with app.app_context():
        print("Creating test doctor data...")

        # Check if test doctor already exists
        existing_doctor = Doctor.query.filter_by(email='freedoctor@example.com').first()
        if existing_doctor:
            print("Test doctor already exists")
            return

        # Create test doctor
        doctor = Doctor(
            email='freedoctor@example.com',
            first_name='Free',
            last_name='Doctor',
            speciality='general_practitioner',
            practice_id=None,  # No practice
            is_verified=True
        )
        doctor.set_password('123456')
        db.session.add(doctor)
        db.session.commit()

        print(f"Created doctor: {doctor.first_name} {doctor.last_name}")

        # Create calendar for doctor
        working_hours = {
            'monday': [['09:00', '17:00']],
            'tuesday': [['09:00', '17:00']],
            'wednesday': [['09:00', '17:00']],
            'thursday': [['09:00', '17:00']],
            'friday': [['09:00', '17:00']],
            'saturday': [],
            'sunday': []
        }

        calendar = Calendar(
            doctor_id=doctor.id,
            working_hours=json.dumps(working_hours),
            slot_duration=30,
            buffer_time=5,
            max_advance_booking_days=30,
            min_advance_booking_hours=24
        )
        db.session.add(calendar)
        db.session.commit()

        print(f"Created calendar for doctor")

        # Generate slots for next 7 days
        today = datetime.utcnow().date()
        slots_created = 0

        for day_offset in range(7):
            current_date = today + timedelta(days=day_offset)

            # Skip weekends
            if current_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                continue

            # Generate slots from 9:00 to 17:00
            current_time = datetime.combine(current_date, datetime.strptime('09:00', '%H:%M').time())
            end_time = datetime.combine(current_date, datetime.strptime('17:00', '%H:%M').time())

            while current_time < end_time:
                slot_end = current_time + timedelta(minutes=30)

                slot = TimeSlot(
                    calendar_id=calendar.id,
                    start_time=current_time,
                    end_time=slot_end,
                    status='available'
                )

                db.session.add(slot)
                slots_created += 1

                current_time = slot_end

        db.session.commit()
        print(f"Created {slots_created} time slots")

        # Create test patient if doesn't exist
        existing_patient = Patient.query.filter_by(phone='+49123456789').first()
        if not existing_patient:
            patient = Patient(
                phone='+49123456789',
                name='Test Patient'
            )
            db.session.add(patient)
            db.session.commit()
            print("Created test patient")

        print("✅ Test data creation completed!")

if __name__ == '__main__':
    create_test_doctor_data()</content>
<parameter name="file_path">c:\Users\ПК\Downloads\terminfinder-mvp_1\terminfinder-mvp\create_test_doctor_data.py