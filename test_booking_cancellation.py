"""
Test script для проверки отмены бронирования и срабатывания алертов
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000"
# BASE_URL = "https://arzttermin-online.onrender.com"  # Для production

# Данные для входа
PATIENT1_EMAIL = "patient1@test.com"
PATIENT1_PASS = "test123"

PATIENT2_EMAIL = "patient2@test.com"
PATIENT2_PASS = "test123"

DOCTOR_EMAIL = "dr.mueller@test.com"
DOCTOR_PASS = "test123"


def login_patient(email, password):
    """Логин пациента и получение токена"""
    response = requests.post(
        f"{BASE_URL}/api/auth/patient/login",
        json={"email": email, "password": password}
    )
    if response.status_code == 200:
        # Token в cookies
        return response.cookies.get('access_token_cookie')
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None


def get_patient_bookings(token):
    """Получить все бронирования пациента"""
    response = requests.get(
        f"{BASE_URL}/api/patient/bookings",
        cookies={"access_token_cookie": token}
    )
    if response.status_code == 200:
        return response.json()
    return None


def cancel_booking(token, booking_id, reason="Test cancellation"):
    """Отменить бронирование"""
    response = requests.post(
        f"{BASE_URL}/api/patient/bookings/{booking_id}/cancel",
        json={"reason": reason},
        cookies={"access_token_cookie": token}
    )
    return response


def create_alert(token, doctor_id=None, speciality=None, date_from=None, date_to=None):
    """Создать алерт"""
    data = {}
    if doctor_id:
        data['doctor_id'] = doctor_id
    if speciality:
        data['speciality'] = speciality
    if date_from:
        data['date_from'] = date_from
    if date_to:
        data['date_to'] = date_to
    
    response = requests.post(
        f"{BASE_URL}/api/patient/alerts",
        json=data,
        cookies={"access_token_cookie": token}
    )
    return response


def get_alerts(token):
    """Получить алерты пациента"""
    response = requests.get(
        f"{BASE_URL}/api/patient/alerts",
        cookies={"access_token_cookie": token}
    )
    if response.status_code == 200:
        return response.json()
    return None


def check_slot_availability(doctor_id, date):
    """Проверить доступные слоты врача"""
    response = requests.get(
        f"{BASE_URL}/api/search/doctors/{doctor_id}/available-slots",
        params={"date": date}
    )
    if response.status_code == 200:
        return response.json()
    return None


def test_booking_cancellation_flow():
    """
    Полный тест: создание алерта → бронирование → отмена → проверка что слот вернулся и алерт сработал
    """
    print("=" * 80)
    print("TEST: Booking Cancellation + Alert Triggering")
    print("=" * 80)
    
    # 1. Логинимся как Patient 1
    print("\n1. Login as Patient 1...")
    patient1_token = login_patient(PATIENT1_EMAIL, PATIENT1_PASS)
    if not patient1_token:
        print("❌ Failed to login as Patient 1")
        return
    print("✓ Patient 1 logged in")
    
    # 2. Логинимся как Patient 2
    print("\n2. Login as Patient 2...")
    patient2_token = login_patient(PATIENT2_EMAIL, PATIENT2_PASS)
    if not patient2_token:
        print("❌ Failed to login as Patient 2")
        return
    print("✓ Patient 2 logged in")
    
    # 3. Patient 1: получаем его бронирования
    print("\n3. Get Patient 1 bookings...")
    bookings = get_patient_bookings(patient1_token)
    if not bookings:
        print("❌ No bookings found")
        return
    
    print(f"Found {len(bookings)} bookings")
    
    # Находим активное бронирование
    active_booking = None
    for booking in bookings:
        if booking['status'] in ['confirmed', 'pending']:
            active_booking = booking
            break
    
    if not active_booking:
        print("❌ No active bookings to cancel")
        print("\n💡 Please create a booking first:")
        print("   1. Login as patient1@test.com")
        print("   2. Go to /patient/search")
        print("   3. Book an appointment with a doctor")
        print("   4. Run this test again")
        return
    
    print(f"✓ Found active booking: {active_booking['booking_code']}")
    print(f"  Doctor: {active_booking.get('doctor_name', 'N/A')}")
    print(f"  Date: {active_booking['appointment_date']}")
    print(f"  Time: {active_booking['appointment_time']}")
    
    doctor_id = active_booking.get('doctor_id')
    appointment_date = active_booking['appointment_date']
    
    if not doctor_id:
        print("❌ Doctor ID not found in booking")
        return
    
    # 4. Patient 2: создаем алерт на этого врача
    print(f"\n4. Patient 2: Create alert for doctor {doctor_id}...")
    
    # Используем дату бронирования для алерта
    date_from = appointment_date
    date_to = (datetime.fromisoformat(appointment_date.replace('Z', '+00:00')) + timedelta(days=7)).date().isoformat()
    
    alert_response = create_alert(
        patient2_token,
        doctor_id=doctor_id,
        date_from=date_from,
        date_to=date_to
    )
    
    if alert_response.status_code == 201:
        alert_data = alert_response.json()
        print(f"✓ Alert created: {alert_data.get('id')}")
        print(f"  Date range: {date_from} to {date_to}")
    else:
        print(f"❌ Failed to create alert: {alert_response.status_code}")
        print(f"   Response: {alert_response.text}")
    
    # 5. Проверяем количество доступных слотов ДО отмены
    print(f"\n5. Check available slots BEFORE cancellation...")
    slots_before = check_slot_availability(doctor_id, appointment_date)
    if slots_before:
        available_count_before = len([s for s in slots_before.get('slots', []) if s.get('status') == 'available'])
        print(f"✓ Available slots: {available_count_before}")
    else:
        available_count_before = 0
        print("⚠ Could not fetch slots")
    
    # 6. Patient 1: отменяем бронирование
    print(f"\n6. Patient 1: Cancel booking {active_booking['booking_code']}...")
    cancel_response = cancel_booking(
        patient1_token,
        active_booking['id'],
        reason="Testing alert system"
    )
    
    if cancel_response.status_code == 200:
        cancel_data = cancel_response.json()
        print("✓ Booking cancelled successfully")
        print(f"  Refund amount: {cancel_data.get('refund_amount', 0)}")
    else:
        print(f"❌ Failed to cancel: {cancel_response.status_code}")
        print(f"   Response: {cancel_response.text}")
        return
    
    # 7. Проверяем количество доступных слотов ПОСЛЕ отмены
    print(f"\n7. Check available slots AFTER cancellation...")
    import time
    time.sleep(1)  # Даем время на обработку
    
    slots_after = check_slot_availability(doctor_id, appointment_date)
    if slots_after:
        available_count_after = len([s for s in slots_after.get('slots', []) if s.get('status') == 'available'])
        print(f"✓ Available slots: {available_count_after}")
        
        if available_count_after > available_count_before:
            print(f"✅ SLOT RETURNED TO CALENDAR (+{available_count_after - available_count_before} slot)")
        else:
            print("⚠ Slot count didn't increase")
    else:
        print("⚠ Could not fetch slots")
    
    # 8. Patient 2: проверяем алерты (должно быть уведомление)
    print(f"\n8. Patient 2: Check if alert was triggered...")
    time.sleep(1)
    
    alerts = get_alerts(patient2_token)
    if alerts:
        for alert in alerts:
            if alert.get('doctor_id') == doctor_id:
                notifications_sent = alert.get('notifications_sent', 0)
                last_notification = alert.get('last_notification_at')
                
                print(f"✓ Alert found for doctor {doctor_id}")
                print(f"  Notifications sent: {notifications_sent}")
                print(f"  Last notification: {last_notification}")
                
                if notifications_sent > 0 and last_notification:
                    print("✅ ALERT TRIGGERED SUCCESSFULLY!")
                else:
                    print("⚠ Alert exists but not triggered yet")
    else:
        print("⚠ No alerts found")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)
    
    print("\n📋 Summary:")
    print("✓ Patient 1 cancelled booking")
    print("✓ Slot should be returned to calendar")
    print("✓ Patient 2 should receive notification (if alert active)")


def test_simple_cancellation():
    """Простой тест отмены бронирования"""
    print("=" * 80)
    print("SIMPLE TEST: Cancel any booking")
    print("=" * 80)
    
    print("\n1. Login as patient...")
    token = login_patient(PATIENT1_EMAIL, PATIENT1_PASS)
    if not token:
        print("❌ Login failed")
        return
    
    print("✓ Logged in")
    
    print("\n2. Get bookings...")
    bookings = get_patient_bookings(token)
    if not bookings:
        print("❌ No bookings found")
        return
    
    active_bookings = [b for b in bookings if b['status'] in ['confirmed', 'pending']]
    
    if not active_bookings:
        print("❌ No active bookings to cancel")
        return
    
    booking = active_bookings[0]
    print(f"✓ Found booking: {booking['booking_code']}")
    print(f"  Status: {booking['status']}")
    print(f"  Date: {booking['appointment_date']} {booking['appointment_time']}")
    
    print(f"\n3. Cancel booking...")
    response = cancel_booking(token, booking['id'])
    
    if response.status_code == 200:
        print("✅ Booking cancelled successfully!")
        print(f"   Response: {response.json()}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   Response: {response.text}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--simple':
        test_simple_cancellation()
    else:
        test_booking_cancellation_flow()
    
    print("\n💡 Tips:")
    print("  - Run with --simple flag for simple cancellation test")
    print("  - Make sure you have active bookings to test with")
    print("  - Check server logs for alert notifications")
