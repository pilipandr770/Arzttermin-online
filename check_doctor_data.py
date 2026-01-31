"""
Check doctor's extended profile data in database
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.doctor import Doctor

def check_doctor_data():
    app = create_app()
    
    with app.app_context():
        # Get all doctors named "Test Doctor"
        doctors = Doctor.query.filter_by(first_name="Test", last_name="Doctor").all()
        
        print(f"Found {len(doctors)} doctors named 'Test Doctor'")
        print("=" * 60)
        
        for doctor in doctors:
            print(f"\nDoctor ID: {doctor.id}")
            print(f"Name: {doctor.first_name} {doctor.last_name}")
            print(f"Email: {doctor.email}")
            print(f"Practice: {doctor.practice.name if doctor.practice else 'No practice'}")
            print(f"Title: {doctor.title}")
            print(f"Photo URL: {doctor.photo_url}")
            print(f"Bio: {doctor.bio[:50] if doctor.bio else 'None'}...")
            print(f"Experience Years: {doctor.experience_years}")
            print(f"Has Calendar: {doctor.calendar is not None}")
            
            if doctor.practice:
                practice = doctor.practice
                print(f"\nPractice Extended Data:")
                print(f"  Rating: {practice.rating_avg} ({practice.rating_count} reviews)")
                print(f"  Gallery Photos: {len(practice.gallery_photos_list) if practice.gallery_photos else 0}")
                print(f"  Features: {len(practice.features_list) if practice.features else 0}")
                print(f"  Insurances: {len(practice.accepted_insurances_list) if practice.accepted_insurances else 0}")
            
            print("-" * 60)

if __name__ == "__main__":
    check_doctor_data()
