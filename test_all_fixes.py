#!/usr/bin/env python3
"""
Проверка всех исправлений:
1. datetime bug исправлен
2. Все врачи имеют праксисы
3. Существующие врачи могут получить профиль праксиса
"""

import requests
import json

BASE_URL = 'http://localhost:5000'

print("=" * 60)
print("🧪 ПРОВЕРКА ВСЕХ ИСПРАВЛЕНИЙ")
print("=" * 60)

# Тест 1: Регистрация нового врача (проверка datetime bug)
print("\n✅ Тест 1: Регистрация нового врача")
print("-" * 60)

import random
test_email = f"test.doctor{random.randint(1000, 9999)}@example.com"

response = requests.post(f'{BASE_URL}/api/auth/doctor/register', json={
    'email': test_email,
    'password': 'TestPass123!',
    'first_name': 'New',
    'last_name': 'Doctor',
    'speciality': 'general_practitioner',
    'tax_number': 'TAX12345'
})

if response.status_code == 200:
    data = response.json()
    print(f"✅ Регистрация прошла успешно!")
    print(f"   Doctor ID: {data.get('doctor_id')}")
    print(f"   Practice ID: {data.get('practice_id')}")
    new_doctor_email = test_email
    new_doctor_password = 'TestPass123!'
else:
    print(f"❌ Ошибка регистрации: {response.status_code}")
    print(f"   {response.text}")
    new_doctor_email = None

# Тест 2: Логин и доступ к профилю нового врача
if new_doctor_email:
    print("\n✅ Тест 2: Доступ к профилю нового врача")
    print("-" * 60)
    
    login_response = requests.post(f'{BASE_URL}/api/auth/doctor/login', json={
        'email': new_doctor_email,
        'password': new_doctor_password
    })
    
    if login_response.status_code == 200:
        token = login_response.json().get('access_token') or login_response.json().get('token')
        print("✅ Логин успешен!")
        
        headers = {'Authorization': f'Bearer {token}'}
        profile_response = requests.get(f'{BASE_URL}/api/practice/profile', headers=headers)
        
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            print(f"✅ Профиль праксиса получен!")
            print(f"   Practice Name: {profile_data.get('name')}")
            print(f"   Verified: {profile_data.get('verified')}")
        else:
            print(f"❌ Ошибка получения профиля: {profile_response.status_code}")
    else:
        print(f"❌ Ошибка логина: {login_response.status_code}")

# Тест 3: Проверка существующего врача с созданным праксисом
print("\n✅ Тест 3: Доступ существующего врача к профилю")
print("-" * 60)

# Попробуем с тестовым врачом (testdoctor@example.com)
login_response = requests.post(f'{BASE_URL}/api/auth/doctor/login', json={
    'email': 'testdoctor@example.com',
    'password': 'Doctor123!'
})

if login_response.status_code == 200:
    token = login_response.json().get('access_token') or login_response.json().get('token')
    print("✅ Логин testdoctor@example.com успешен!")
    
    headers = {'Authorization': f'Bearer {token}'}
    profile_response = requests.get(f'{BASE_URL}/api/practice/profile', headers=headers)
    
    if profile_response.status_code == 200:
        profile_data = profile_response.json()
        print(f"✅ Профиль праксиса получен!")
        print(f"   Practice Name: {profile_data.get('name')}")
    else:
        print(f"❌ Ошибка получения профиля: {profile_response.status_code}")
        print(f"   {profile_response.text}")
else:
    print(f"❌ Логин не удался: {login_response.status_code}")

print("\n" + "=" * 60)
print("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
print("=" * 60)
