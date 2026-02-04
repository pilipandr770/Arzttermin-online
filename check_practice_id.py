"""
Check doctors without practice_id
"""
from app import create_app, db
from app.models import Doctor, Practice

app = create_app()

with app.app_context():
    # Check doctors without practice
    doctors_no_practice = Doctor.query.filter(Doctor.practice_id == None).all()
    
    print(f"📊 Total doctors: {Doctor.query.count()}")
    print(f"⚠️  Doctors without practice: {len(doctors_no_practice)}")
    print(f"✅ Doctors with practice: {Doctor.query.filter(Doctor.practice_id != None).count()}")
    
    if doctors_no_practice:
        print("\n❌ Doctors without practice_id:")
        for doctor in doctors_no_practice:
            print(f"  - {doctor.first_name} {doctor.last_name} ({doctor.email})")
        
        # Check if there are any practices
        practices = Practice.query.all()
        print(f"\n🏥 Total practices: {len(practices)}")
        
        if practices:
            print("\nAvailable practices:")
            for practice in practices:
                print(f"  - {practice.name} (ID: {practice.id})")
    else:
        print("\n✅ All doctors have practice_id assigned!")
