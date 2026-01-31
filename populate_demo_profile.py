"""
Populate extended profile data for demonstration
This script will fill in extended profile data for one doctor to showcase the interactive cards
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.doctor import Doctor
from app.models.practice import Practice
import json

def populate_demo_data():
    app = create_app()
    
    with app.app_context():
        # Get first doctor with practice
        doctor = Doctor.query.filter(Doctor.practice_id.isnot(None)).first()
        
        if not doctor:
            print("No doctor found with practice")
            return
        
        practice = doctor.practice
        
        print(f"Updating profile for: {doctor.first_name} {doctor.last_name}")
        print(f"Practice: {practice.name}")
        print("=" * 60)
        
        # Update Doctor extended fields
        doctor.title = "Dr. med."
        doctor.bio = "Erfahrener Allgemeinmediziner mit Schwerpunkt auf präventive Medizin und Familienbetreuung. Besondere Expertise in chronischen Erkrankungen und Vorsorgeuntersuchungen."
        doctor.experience_years = 15
        doctor.photo_url = "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=400&h=400&fit=crop"
        doctor.qualifications = json.dumps([
            "Facharzt für Allgemeinmedizin",
            "Zusatzqualifikation Sportmedizin",
            "Notfallmedizin"
        ])
        doctor.treatment_focus = json.dumps([
            "Präventivmedizin",
            "Chronische Erkrankungen",
            "Sportmedizin",
            "Familienmedizin"
        ])
        doctor.consultation_types = json.dumps([
            "Vor-Ort-Termin",
            "Videosprechstunde",
            "Hausbesuch (nach Vereinbarung)"
        ])
        
        # Update Practice extended fields
        practice.description = "Moderne Allgemeinarztpraxis im Herzen von Berlin. Wir bieten umfassende medizinische Versorgung für die ganze Familie in angenehmer Atmosphäre."
        practice.gallery_photos = json.dumps([
            "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=800&h=600&fit=crop",
            "https://images.unsplash.com/photo-1519494140681-8b17d830a3ec?w=800&h=600&fit=crop",
            "https://images.unsplash.com/photo-1519494080410-f9aa76cb4283?w=800&h=600&fit=crop",
            "https://images.unsplash.com/photo-1581594549595-35f6edc7b762?w=800&h=600&fit=crop"
        ])
        practice.services = json.dumps([
            "Allgemeinmedizinische Versorgung",
            "Vorsorgeuntersuchungen",
            "Impfungen",
            "Labor und Diagnostik",
            "EKG und Belastungs-EKG",
            "Ultraschall",
            "Kleine Chirurgie",
            "Reisemedizinische Beratung"
        ])
        practice.equipment = json.dumps([
            "Moderne Ultraschallgeräte",
            "Digital-Röntgen",
            "EKG-Geräte",
            "Labor",
            "Spirometrie"
        ])
        practice.accepted_insurances = json.dumps([
            {"name": "AOK", "type": "public"},
            {"name": "TK (Techniker Krankenkasse)", "type": "public"},
            {"name": "Barmer", "type": "public"},
            {"name": "DAK", "type": "public"},
            {"name": "IKK", "type": "public"},
            {"name": "Debeka", "type": "private"},
            {"name": "Allianz", "type": "private"},
            {"name": "DKV", "type": "private"}
        ])
        practice.features = json.dumps([
            "wheelchair_accessible",
            "parking_available",
            "public_transport_nearby",
            "elevator_available",
            "online_booking",
            "video_consultation",
            "same_day_appointments",
            "english_speaking"
        ])
        practice.rating_avg = 4.7
        practice.rating_count = 156
        practice.emergency_phone = "+49 30 116117"
        practice.whatsapp_number = practice.phone
        
        db.session.commit()
        
        print("\n✓ Extended profile data updated successfully!")
        print("\nDoctor Extended Fields:")
        print(f"  - Title: {doctor.title}")
        print(f"  - Experience: {doctor.experience_years} years")
        print(f"  - Photo URL: {doctor.photo_url}")
        print(f"  - Bio length: {len(doctor.bio)} characters")
        print(f"  - Qualifications: {len(json.loads(doctor.qualifications))} items")
        print(f"  - Treatment Focus: {len(json.loads(doctor.treatment_focus))} items")
        print(f"  - Consultation Types: {len(json.loads(doctor.consultation_types))} types")
        
        print("\nPractice Extended Fields:")
        print(f"  - Description length: {len(practice.description)} characters")
        print(f"  - Gallery Photos: {len(json.loads(practice.gallery_photos))} photos")
        print(f"  - Services: {len(json.loads(practice.services))} services")
        print(f"  - Equipment: {len(json.loads(practice.equipment))} items")
        print(f"  - Insurances: {len(json.loads(practice.accepted_insurances))} insurances")
        print(f"  - Features: {len(json.loads(practice.features))} features")
        print(f"  - Rating: {practice.rating_avg} ({practice.rating_count} reviews)")
        print(f"  - Emergency Phone: {practice.emergency_phone}")
        
        print(f"\nNow reload the search page and you'll see the interactive card!")
        print(f"Doctor ID: {doctor.id}")
        print(f"Practice ID: {practice.id}")

if __name__ == "__main__":
    populate_demo_data()
