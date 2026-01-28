#!/usr/bin/env python3
"""
Test script for TerminFinder MVP
"""
import subprocess
import time
import requests
import sys
import os

def test_api():
    """Test the patient search API"""
    print("🚀 Starting TerminFinder MVP tests...")

    # Start the Flask app in background
    print("📡 Starting Flask application...")
    app_process = subprocess.Popen(
        [sys.executable, 'run.py'],
        cwd=os.path.dirname(__file__),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for app to start
    time.sleep(3)

    try:
        # Test patient login
        print("🔐 Testing patient login...")
        login_url = 'http://localhost:5000/api/auth/patient/login'
        login_data = {'phone': '+491234567890'}

        response = requests.post(login_url, json=login_data, headers={'Content-Type': 'application/json'}, timeout=5)
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False

        data = response.json()
        access_token = data.get('access_token')
        if not access_token:
            print("❌ No access token received")
            return False

        print("✅ Login successful")

        # Test doctor search
        print("🔍 Testing doctor search...")
        search_url = 'http://localhost:5000/api/patient/api/search/doctors'
        headers = {'Authorization': f'Bearer {access_token}'}

        response = requests.get(search_url, headers=headers, timeout=5)
        if response.status_code != 200:
            print(f"❌ Search failed: {response.status_code} - {response.text}")
            return False

        doctors = response.json()
        doctors_list = doctors.get('doctors', [])
        print(f"✅ Found {len(doctors_list)} doctors")

        if doctors_list:
            doctor = doctors_list[0]
            name = doctor.get('name', 'Unknown')
            speciality = doctor.get('speciality', 'Unknown')
            available_slots = doctor.get('available_slots', [])
            print(f"📋 Sample doctor: {name} ({speciality}) - {len(available_slots)} slots")

        # Test speciality filter
        print("🎯 Testing speciality filter...")
        response = requests.get(search_url + '?speciality=dentist', headers=headers, timeout=5)
        if response.status_code == 200:
            dentists_data = response.json()
            dentists = dentists_data.get('doctors', [])
            print(f"✅ Found {len(dentists)} dentists")
        else:
            print(f"❌ Speciality filter failed: {response.status_code} - {response.text}")

        # Test slot booking
        print("📅 Testing slot booking...")
        if doctors_list and doctors_list[0]['available_slots']:
            slot_id = doctors_list[0]['available_slots'][0]['id']
            booking_url = 'http://localhost:5000/patient/api/book'
            booking_data = {'slot_id': slot_id}
            
            response = requests.post(booking_url, json=booking_data, headers=headers, timeout=5)
            if response.status_code == 200:
                booking_result = response.json()
                print(f"✅ Booking successful: {booking_result.get('message', 'OK')}")
            else:
                print(f"❌ Booking failed: {response.status_code} - {response.text}")
        else:
            print("❌ No available slots for booking test")

        print("🎉 All tests passed!")
        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        # Stop the Flask app
        print("🛑 Stopping Flask application...")
        app_process.terminate()
        app_process.wait()

if __name__ == '__main__':
    success = test_api()
    sys.exit(0 if success else 1)