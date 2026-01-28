import urllib.request
import json
import base64

# Тестируем API calendar slots для врача с urllib
def test_api():
    try:
        # Login
        login_data = json.dumps({'email': 'doctor@test.com', 'password': 'password123'}).encode('utf-8')
        req = urllib.request.Request('http://127.0.0.1:5000/api/auth/doctor/login',
                                   data=login_data,
                                   headers={'Content-Type': 'application/json'})
        response = urllib.request.urlopen(req)
        if response.status == 200:
            data = json.loads(response.read().decode('utf-8'))
            token = data['access_token']
            print('Doctor login successful')

            # Get calendar slots
            req = urllib.request.Request('http://127.0.0.1:5000/api/doctors/calendar/slots?date=2026-01-28',
                                       headers={'Authorization': f'Bearer {token}'})
            response = urllib.request.urlopen(req)
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
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
                print(f'Error getting slots: {response.status}')
        else:
            print(f'Login failed: {response.status}')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    test_api()