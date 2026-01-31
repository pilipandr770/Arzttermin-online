"""
Create calendar and available slots for the demo doctor
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.doctor import Doctor
from app.models.calendar import Calendar, TimeSlot

def create_slots_for_demo_doctor():
    app = create_app()
    
    with app.app_context():
        # Find the doctor with extended profile (Test Doctor with practice Test Practice, email testdoctor@example.com)
        doctor = Doctor.query.filter_by(email="testdoctor@example.com").first()
        
        if not doctor:
            print("Demo doctor not found")
            return
        
        print(f"Creating slots for: {doctor.first_name} {doctor.last_name}")
        print(f"Doctor ID: {doctor.id}")
        print("=" * 60)
        
        # Check if doctor has calendar
        if not doctor.calendar:
            print("Creating calendar for doctor...")
            calendar = Calendar(
                doctor_id=doctor.id
            )
            db.session.add(calendar)
            db.session.flush()
            print(f"✓ Calendar created: {calendar.id}")
        else:
            calendar = doctor.calendar
            print(f"Doctor already has calendar: {calendar.id}")
            # Don't try to delete existing slots if there are bookings
            print("Skipping slot deletion to avoid foreign key errors")
            return
        
        # Create slots for next 7 days
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=7)
        slots_created = 0
        for day_offset in range(7):
            current_date = start_date + timedelta(days=day_offset)
            
            # Skip weekends
            if current_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                continue
            
            # Create morning slots (9:00 - 12:00)
            for hour in range(9, 12):
                for minute in [0, 30]:
                    start_time = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=hour, minutes=minute)
                    end_time = start_time + timedelta(minutes=30)
                    
                    slot = TimeSlot(
                        calendar_id=calendar.id,
                        start_time=start_time,
                        end_time=end_time,
                        is_available=True
                    )
                    db.session.add(slot)
                    slots_created += 1
            
            # Create afternoon slots (14:00 - 17:00)
            for hour in range(14, 17):
                for minute in [0, 30]:
                    start_time = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=hour, minutes=minute)
                    end_time = start_time + timedelta(minutes=30)
                    
                    slot = TimeSlot(
                        calendar_id=calendar.id,
                        start_time=start_time,
                        end_time=end_time,
                        is_available=True
                    )
                    db.session.add(slot)
                    slots_created += 1
        
        db.session.commit()
        
        print(f"\n✓ Successfully created {slots_created} slots for next 7 days")
        print(f"  Calendar ID: {calendar.id}")
        print(f"  Date range: {start_date} to {end_date}")
        print(f"\nNow the doctor should appear in search results!")
        print(f"Visit: http://127.0.0.1:5000/patient/search")

if __name__ == "__main__":
    create_slots_for_demo_doctor()
