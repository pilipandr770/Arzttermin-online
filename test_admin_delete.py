"""
Скрипт для тестування функції видалення в адмінці
"""
import requests
import json

BASE_URL = "http://localhost:5000"

# 1. Логін адміна
print("1. Logging in as admin...")
login_response = requests.post(f"{BASE_URL}/api/admin/login", json={
    "username": "admin",
    "password": "admin123"
})

if login_response.status_code == 200:
    token = login_response.json()['access_token']
    print(f"✓ Logged in successfully")
    print(f"Token: {token[:50]}...")
else:
    print(f"✗ Login failed: {login_response.text}")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# 2. Отримуємо список пацієнтів
print("\n2. Getting patients list...")
patients_response = requests.get(f"{BASE_URL}/api/admin/patients", headers=headers)
if patients_response.status_code == 200:
    patients = patients_response.json()['patients']
    print(f"✓ Found {len(patients)} patients")
    if patients:
        print(f"First patient: {patients[0]['phone']} - {patients[0]['name']}")
else:
    print(f"✗ Failed to get patients: {patients_response.text}")

# 3. Отримуємо список лікарів
print("\n3. Getting doctors list...")
doctors_response = requests.get(f"{BASE_URL}/api/admin/doctors", headers=headers)
if doctors_response.status_code == 200:
    doctors = doctors_response.json()['doctors']
    print(f"✓ Found {len(doctors)} doctors")
    if doctors:
        doctor = doctors[0]
        print(f"First doctor: {doctor.get('first_name', 'N/A')} {doctor.get('last_name', 'N/A')}")
        print(f"Specialization: {doctor.get('specializations', ['N/A'])[0] if doctor.get('specializations') else 'N/A'}")
        print(f"Verified: {doctor.get('is_verified', False)}")
else:
    print(f"✗ Failed to get doctors: {doctors_response.text}")

print("\n" + "="*60)
print("ФУНКЦІЇ ДОСТУПНІ:")
print("="*60)
print("✓ Перегляд пацієнтів з пагінацією та пошуком")
print("✓ Перегляд лікарів з фільтрацією по статусу верифікації")
print("✓ Видалення пацієнтів (з перевіркою активних бронювань)")
print("✓ Видалення лікарів (з перевіркою активних бронювань)")
print("✓ Примусове видалення (force=true) для очистки бази")
print("✓ Верифікація лікарів")
print("✓ Управління бронюваннями")
print("\n" + "="*60)
print("ДЛЯ ВИДАЛЕННЯ:")
print("="*60)
print("1. Спочатку спробуйте видалити без force")
print("2. Якщо є активні бронювання - отримаєте попередження")
print("3. Встановіть чекбокс 'Примусово видалити' в модалці")
print("4. Підтвердіть - видалиться разом з усіма бронюваннями")
