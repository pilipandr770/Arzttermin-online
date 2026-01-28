import urllib.request
import json

# Тестируем обновленный API
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
            req = urllib.request.Request('http://127.0.0.1:5000/api/doctors/calendar/slots?start_date=2026-01-28&end_date=2026-01-28',
                                       headers={'Authorization': f'Bearer {token}'})
            response = urllib.request.urlopen(req)
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                slots = data.get('slots', [])
                print(f'Total slots returned: {len(slots)}')

                # Найдем забронированный слот
                booked_slot = None
                for slot in slots:
                    if slot['status'] == 'booked':
                        booked_slot = slot
                        break

                if booked_slot:
                    print('Booked slot details:')
                    start_time = booked_slot['start_time'][:16]
                    print(f'  Time: {start_time}')
                    print(f'  Status: {booked_slot["status"]}')
                    if 'booking' in booked_slot:
                        booking = booked_slot['booking']
                        print(f'  Patient: {booking["patient_name"]}')
                        print(f'  Phone: {booking["patient_phone"]}')
                        print(f'  Email: {booking["patient_email"]}')
                    else:
                        print('  No booking info')
                else:
                    print('No booked slots found')
            else:
                print(f'Error getting slots: {response.status}')
        else:
            print(f'Login failed: {response.status}')
    except Exception as e:
        print(f'Error: {e}')

test_api()