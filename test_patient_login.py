"""
Тестовый скрипт для проверки авторизации пациента
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

# Тестовые данные пациента
PATIENT_EMAIL = "patient@example.com"
PATIENT_PASSWORD = "patient123"

def test_patient_login():
    """Проверяет логин пациента и получение JWT токена"""
    print("🔐 Тестирую авторизацию пациента...")
    print(f"Email: {PATIENT_EMAIL}")
    
    # Попытка входа
    response = requests.post(
        f"{BASE_URL}/api/auth/patient/login",
        json={
            "email": PATIENT_EMAIL,
            "password": PATIENT_PASSWORD
        },
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Авторизация успешна!")
        print(f"Access Token: {data.get('access_token', 'N/A')[:50]}...")
        print(f"Patient ID: {data.get('patient_id', 'N/A')}")
        print(f"Patient Name: {data.get('patient_name', 'N/A')}")
        return data.get('access_token')
    else:
        print(f"❌ Ошибка авторизации:")
        print(response.text)
        return None

def test_book_slot(token, slot_id):
    """Тестирует бронирование слота с полученным токеном"""
    if not token:
        print("⚠️ Нет токена для бронирования")
        return
    
    print(f"\n📅 Тестирую бронирование слота...")
    print(f"Slot ID: {slot_id}")
    
    response = requests.post(
        f"{BASE_URL}/api/patient/book",
        json={"slot_id": slot_id},
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Бронирование успешно!")
        print(f"Booking Code: {data.get('booking_code', 'N/A')}")
        print(f"Doctor: {data.get('doctor_name', 'N/A')}")
        print(f"Date: {data.get('date', 'N/A')} at {data.get('time', 'N/A')}")
    else:
        print(f"❌ Ошибка бронирования:")
        print(response.text)

def get_doctor_slots(doctor_id):
    """Получает слоты врача"""
    print(f"\n📋 Получаю слоты врача {doctor_id}...")
    
    response = requests.get(f"{BASE_URL}/api/search/doctors/{doctor_id}/slots")
    
    if response.status_code == 200:
        data = response.json()
        slots = data.get('slots', [])
        print(f"✅ Найдено слотов: {len(slots)}")
        
        # Показываем первые 3 доступных слота
        available_slots = [s for s in slots if s.get('status') == 'available']
        if available_slots:
            print("\nДоступные слоты:")
            for slot in available_slots[:3]:
                print(f"  • {slot['date']} {slot['start_time']} - ID: {slot['id']}")
            return available_slots[0]['id'] if available_slots else None
        else:
            print("⚠️ Нет доступных слотов")
            return None
    else:
        print(f"❌ Ошибка получения слотов: {response.status_code}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 ТЕСТ АВТОРИЗАЦИИ И БРОНИРОВАНИЯ ПАЦИЕНТА")
    print("=" * 60)
    
    # 1. Логин
    token = test_patient_login()
    
    # 2. Получить слоты тестового врача
    # Используем известный ID врача из базы
    DOCTOR_ID = "8e31966d-eed1-4f64-b7b2-a47886ca1a7f"  # Test Doctor
    slot_id = get_doctor_slots(DOCTOR_ID)
    
    # 3. Попробовать забронировать
    if token and slot_id:
        test_book_slot(token, slot_id)
    
    print("\n" + "=" * 60)
    print("✅ Тест завершен")
    print("=" * 60)
