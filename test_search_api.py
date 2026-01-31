"""
Test script to check if the search API returns extended profile data
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_search_api():
    """Test the search API to see what data is returned"""
    print("Testing /api/search/doctors/available endpoint...")
    print("=" * 60)
    
    # Make request to search API
    url = f"{BASE_URL}/api/search/doctors/available"
    params = {
        'speciality': 'general_practitioner',
        'date_from': '2026-01-30',
        'date_to': '2026-02-06'
    }
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ API request successful")
            print(f"✓ Found {len(data.get('doctors', []))} doctors")
            print()
            
            if data.get('doctors'):
                # Print all doctors to find the one with extended data
                print("All doctors in results:")
                print("-" * 60)
                for idx, doc in enumerate(data['doctors'], 1):
                    print(f"{idx}. {doc.get('full_name')} - Title: {doc.get('title')}, Experience: {doc.get('experience_years')}, Photo: {'Yes' if doc.get('photo_url') else 'No'}")
                print()
                
                # Check all doctors for extended data
                doctor_with_data = None
                for doc in data['doctors']:
                    if doc.get('photo_url') or doc.get('experience_years'):
                        doctor_with_data = doc
                        break
                
                if not doctor_with_data:
                    doctor_with_data = data['doctors'][0]
                    print("⚠ No doctor found with extended data. Showing first doctor instead.")
                    print()
                
                doctor = doctor_with_data
                
                # Print first doctor's extended data
                doctor = data['doctors'][0]
                print("First Doctor Extended Data:")
                print("-" * 60)
                print(f"Name: {doctor.get('full_name')}")
                print(f"Title: {doctor.get('title')}")
                print(f"Experience Years: {doctor.get('experience_years')}")
                print(f"Photo URL: {doctor.get('photo_url')}")
                bio = doctor.get('bio') or ''
                print(f"Bio: {bio[:100] if bio else 'No bio'}...")
                print(f"Languages: {doctor.get('languages')}")
                print()
                
                # Check practice data
                practice = doctor.get('practice', {})
                print("Practice Extended Data:")
                print("-" * 60)
                print(f"Name: {practice.get('name')}")
                print(f"Rating Avg: {practice.get('rating_avg')}")
                print(f"Rating Count: {practice.get('rating_count')}")
                print(f"Gallery Photos: {len(practice.get('gallery_photos', []))} photos")
                print(f"Features: {practice.get('features')}")
                print(f"Accepted Insurances: {len(practice.get('accepted_insurances', []))} insurances")
                print()
                
                # Pretty print full JSON
                print("Full JSON Response (first doctor):")
                print("-" * 60)
                print(json.dumps(doctor, indent=2, ensure_ascii=False))
            else:
                print("⚠ No doctors found")
                print("This might be because:")
                print("1. No doctors have available slots in the date range")
                print("2. Database has no doctors with general_practitioner speciality")
                print()
                print("Try accessing extended profile form at:")
                print(f"{BASE_URL}/practice/profile/extended")
                
        else:
            print(f"✗ API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to the server")
        print("Make sure the Flask app is running on http://127.0.0.1:5000")
    except Exception as e:
        print(f"✗ Error: {str(e)}")

if __name__ == "__main__":
    test_search_api()
