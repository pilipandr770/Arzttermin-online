#!/usr/bin/env python3
"""
Тест для проверки доступа существующего врача к профилю практики
"""

import requests
import json

BASE_URL = 'http://localhost:5000'

print("============================================================")
print("🧪 ТЕСТИРОВАНИЕ ДОСТУПА СУЩЕСТВУЮЩЕГО ВРАЧА")
print("============================================================")

# Логин
print('\n🔑 Логин врача doctor211@test.com...')
response = requests.post(f'{BASE_URL}/api/auth/doctor/login', json={
    'email': 'doctor211@test.com',
    'password': 'Doctor123!'
})

if response.status_code == 200:
    token = response.json()['token']
    print(f'✅ Логин успешен!')
    
    # Получение профиля практики
    print('\n📋 Получение профиля праксиса...')
    headers = {'Authorization': f'Bearer {token}'}
    profile_response = requests.get(f'{BASE_URL}/api/practice/profile', headers=headers)
    
    print(f'Status Code: {profile_response.status_code}')
    if profile_response.status_code == 200:
        data = profile_response.json()
        print(f'✅ Профиль получен!')
        print(f'   Practice ID: {data["id"]}')
        print(f'   Practice Name: {data["name"]}')
        print(f'   Verified: {data["verified"]}')
    else:
        print(f'❌ Ошибка: {profile_response.text}')
else:
    print(f'❌ Ошибка логина: {response.text}')

print("\n============================================================")
print("✅ ТЕСТ ЗАВЕРШЕН")
print("============================================================")
