"""
Скрипт для создания тестовых данных
"""
from app import create_app, db
from app.models import Patient, Doctor, Practice, Calendar, TimeSlot, Booking
from datetime import datetime, timedelta
import uuid

def create_test_data():
    app = create_app()

    with app.app_context():
        # Создаем тестовую практику
        practice = Practice(
            name="Test Practice",
            vat_number="DE123456789",
            handelsregister_nr="HRB123456",
            owner_email="practice@test.com",
            phone="+491234567890",
            address="Test Street 123, Berlin"
        )
        db.session.add(practice)
        db.session.commit()

        # Создаем тестового врача
        doctor = Doctor(
            first_name="Test",
            last_name="Doctor",
            email="doctor@test.com",
            speciality="general_practitioner",
            practice_id=practice.id,
            is_verified=True
        )
        doctor.set_password("123456")
        db.session.add(doctor)
        db.session.commit()

        # Создаем календарь для врача
        calendar = Calendar(
            doctor_id=doctor.id,
            working_hours='{"monday": ["09:00-17:00"], "tuesday": ["09:00-17:00"], "wednesday": ["09:00-17:00"], "thursday": ["09:00-17:00"], "friday": ["09:00-17:00"]}',
            slot_duration=30,
            buffer_time=5
        )
        db.session.add(calendar)
        db.session.commit()

        # Создаем временные слоты на ближайшие дни
        now = datetime.utcnow()
        for i in range(7):  # Следующие 7 дней
            date = now + timedelta(days=i)
            if date.weekday() < 5:  # Пн-Пт
                for hour in range(9, 17):  # 9:00 - 17:00
                    start_time = date.replace(hour=hour, minute=0, second=0, microsecond=0)
                    end_time = start_time + timedelta(minutes=30)

                    slot = TimeSlot(
                        calendar_id=calendar.id,
                        start_time=start_time,
                        end_time=end_time,
                        status='available'
                    )
                    db.session.add(slot)

        db.session.commit()
        print("Тестовые данные созданы успешно!")

if __name__ == "__main__":
    create_test_data()