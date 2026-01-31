"""
Тестовый скрипт для регистрации врача с автоматическим созданием праксиса
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_doctor_registration():
    """Тестирует регистрацию врача без practice_id (должен создаться автоматически)"""
    
    print("\n" + "=" * 60)
    print("🧪 ТЕСТ: Регистрация врача БЕЗ practice_id")
    print("=" * 60)
    
    doctor_data = {
        "email": f"test.doctor{__import__('random').randint(1000, 9999)}@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "Doctor",
        "tax_number": "DE123456789",
        "speciality": "general_practitioner"
        # Намеренно НЕ передаем practice_id
    }
    
    print("\n📤 Отправляю запрос на регистрацию...")
    print(f"Email: {doctor_data['email']}")
    print(f"Имя: {doctor_data['first_name']} {doctor_data['last_name']}")
    print(f"Специальность: {doctor_data['speciality']}")
    print("⚠️ practice_id НЕ указан (должен создаться автоматически)")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/doctor/register",
        json=doctor_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\n📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Регистрация успешна!")
        print(f"   Doctor ID: {data.get('doctor_id')}")
        print(f"   Practice ID: {data.get('practice_id')}")
        print(f"   Practice Name: {data.get('practice_name')}")
        print(f"   Calendar Created: {data.get('calendar_created')}")
        print(f"   Slots Created: {data.get('slots_created')}")
        
        return {
            'doctor_id': data.get('doctor_id'),
            'practice_id': data.get('practice_id'),
            'email': doctor_data['email'],
            'password': doctor_data['password']
        }
    else:
        print(f"\n❌ Ошибка регистрации:")
        print(response.text)
        return None


def test_doctor_login_and_profile(credentials):
    """Тестирует логин и доступ к профилю праксиса"""
    
    print("\n" + "=" * 60)
    print("🔐 ТЕСТ: Логин и доступ к профилю праксиса")
    print("=" * 60)
    
    # 1. Логин
    print("\n🔑 Шаг 1: Логин врача...")
    login_response = requests.post(
        f"{BASE_URL}/api/auth/doctor/login",
        json={
            "email": credentials['email'],
            "password": credentials['password']
        },
        headers={"Content-Type": "application/json"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Ошибка логина: {login_response.text}")
        return
    
    login_data = login_response.json()
    access_token = login_data.get('access_token')
    print(f"✅ Логин успешен! Token: {access_token[:30]}...")
    
    # 2. Получение профиля праксиса
    print("\n📋 Шаг 2: Получение профиля праксиса...")
    profile_response = requests.get(
        f"{BASE_URL}/api/practice/profile",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    )
    
    print(f"Status Code: {profile_response.status_code}")
    
    if profile_response.status_code == 200:
        profile_data = profile_response.json()
        print("\n✅ Профиль праксиса получен успешно!")
        print(f"   ID: {profile_data.get('id')}")
        print(f"   Name: {profile_data.get('name')}")
        print(f"   Phone: {profile_data.get('phone') or 'Не указан'}")
        print(f"   Website: {profile_data.get('website') or 'Не указан'}")
        print(f"   Verified: {profile_data.get('verified')}")
        
        # 3. Обновление профиля
        print("\n✏️ Шаг 3: Обновление профиля праксиса...")
        update_response = requests.put(
            f"{BASE_URL}/api/practice/profile/extended",
            json={
                "name": f"Praxis Dr. {credentials['email'].split('@')[0]}",
                "phone": "+49 30 12345678",
                "website": "https://example-praxis.de",
                "description": "Тестовая праксис"
            },
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"Status Code: {update_response.status_code}")
        
        if update_response.status_code == 200:
            print("✅ Профиль праксиса успешно обновлен!")
            update_data = update_response.json()
            print(f"   Message: {update_data.get('message')}")
        else:
            print(f"❌ Ошибка обновления: {update_response.text}")
    else:
        print(f"❌ Ошибка получения профиля: {profile_response.text}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ АВТОМАТИЧЕСКОГО СОЗДАНИЯ ПРАКСИСА")
    print("=" * 60)
    
    # Тест 1: Регистрация
    credentials = test_doctor_registration()
    
    if credentials:
        # Тест 2: Логин и профиль
        test_doctor_login_and_profile(credentials)
    
    print("\n" + "=" * 60)
    print("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
    print("=" * 60)
    print("\n💡 Теперь вы можете:")
    print("   1. Войти в систему с этими данными")
    print("   2. Редактировать профиль праксиса")
    print("   3. Праксис создан автоматически!")
    print("")
