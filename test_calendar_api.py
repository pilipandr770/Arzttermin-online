import requests
import time

# Ждём запуска сервера
time.sleep(3)

# Тестируем API calendar slots для врача
login_data = {'email': 'doctor@test.com', 'password': 'password123'}
response = requests.post('http://localhost:5000/api/auth/doctor/login', json=login_data)
if response.status_code == 200:
    token = response.json()['access_token']
    print('Doctor login successful')

    # Тестируем calendar slots на дату с забронированным слотом
    headers = {'Authorization': f'Bearer {token}'}
    slots_response = requests.get('http://localhost:5000/api/doctors/calendar/slots?date=2026-01-28', headers=headers)
    print(f'Calendar slots status: {slots_response.status_code}')
    if slots_response.status_code == 200:
        data = slots_response.json()
        slots = data.get('slots', [])
        print(f'Total slots returned: {len(slots)}')

        # Проверим статусы
        status_counts = {}
        booked_slots = []
        for slot in slots:
            status = slot['status']
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1

            if status == 'booked':
                booked_slots.append(slot)

        print('Status counts:', status_counts)

        if booked_slots:
            print('Booked slots:')
            for slot in booked_slots:
                start_time = slot['start_time'][:16]  # YYYY-MM-DDTHH:MM
                print(f'  {start_time} - {slot["status"]}')
        else:
            print('No booked slots found in response')
    else:
        print(f'Error: {slots_response.text}')
else:
    print(f'Login failed: {response.text}')