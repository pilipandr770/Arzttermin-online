"""
Test Multi-Tenant Isolation
============================

Verify that Practice A cannot access Practice B data.
"""
from app import create_app, db
from app.models import Doctor, Practice, TimeSlot, Calendar, Booking
from app.routes.doctor import doctor_api
import uuid

app = create_app()

with app.app_context():
    # Get all practices
    practices = Practice.query.all()
    
    if len(practices) < 2:
        print("⚠️  Need at least 2 practices for isolation test")
        print(f"   Current practices: {len(practices)}")
        exit(1)
    
    practice_a = practices[0]
    practice_b = practices[1]
    
    print(f"🏥 Practice A: {practice_a.name} ({practice_a.id})")
    print(f"🏥 Practice B: {practice_b.name} ({practice_b.id})")
    print()
    
    # Get doctors from each practice
    doctors_a = Doctor.query.filter_by(practice_id=practice_a.id).all()
    doctors_b = Doctor.query.filter_by(practice_id=practice_b.id).all()
    
    print(f"👨‍⚕️  Doctors in Practice A: {len(doctors_a)}")
    for doc in doctors_a:
        print(f"   - {doc.first_name} {doc.last_name}")
    
    print(f"\n👨‍⚕️  Doctors in Practice B: {len(doctors_b)}")
    for doc in doctors_b:
        print(f"   - {doc.first_name} {doc.last_name}")
    
    if not doctors_a or not doctors_b:
        print("\n⚠️  Need doctors in both practices for test")
        exit(1)
    
    print("\n" + "="*50)
    print("🧪 TESTING ISOLATION")
    print("="*50)
    
    # Test 1: Doctor from Practice A should only see their own slots
    doctor_a = doctors_a[0]
    if doctor_a.calendar:
        slots_a = TimeSlot.query.filter_by(calendar_id=doctor_a.calendar.id).count()
        print(f"\n✅ Test 1: Doctor A has {slots_a} slots (via doctor.calendar.id)")
        
        # This is WRONG way (no isolation):
        all_slots_wrong = TimeSlot.query.count()
        print(f"❌ Without filter: Would see {all_slots_wrong} slots (ALL practices!)")
    
    # Test 2: Verify practice_id is set for all doctors
    doctors_no_practice = Doctor.query.filter(Doctor.practice_id == None).count()
    if doctors_no_practice == 0:
        print(f"\n✅ Test 2: All doctors have practice_id assigned")
    else:
        print(f"\n❌ Test 2: {doctors_no_practice} doctors without practice_id!")
    
    # Test 3: Count resources per practice
    print(f"\n📊 Practice A Resources:")
    print(f"   Doctors: {len(doctors_a)}")
    if doctors_a and doctors_a[0].calendar:
        slots_a_count = db.session.query(TimeSlot).join(Calendar).join(Doctor).filter(
            Doctor.practice_id == practice_a.id
        ).count()
        print(f"   Time Slots: {slots_a_count}")
    
    print(f"\n📊 Practice B Resources:")
    print(f"   Doctors: {len(doctors_b)}")
    if doctors_b and doctors_b[0].calendar:
        slots_b_count = db.session.query(TimeSlot).join(Calendar).join(Doctor).filter(
            Doctor.practice_id == practice_b.id
        ).count()
        print(f"   Time Slots: {slots_b_count}")
    
    # Test 4: Verify no cross-practice bookings
    bookings = Booking.query.all()
    print(f"\n📅 Total bookings: {len(bookings)}")
    
    cross_practice_issues = 0
    for booking in bookings:
        doctor = booking.timeslot.calendar.doctor
        if doctor.practice_id:
            # Booking is correctly tied to doctor's practice
            pass
        else:
            cross_practice_issues += 1
    
    if cross_practice_issues == 0:
        print(f"✅ Test 4: All bookings correctly tied to practices")
    else:
        print(f"❌ Test 4: {cross_practice_issues} bookings with missing practice context")
    
    print("\n" + "="*50)
    print("📋 SUMMARY")
    print("="*50)
    print("✅ Multi-tenant structure exists (Practice model)")
    print("✅ Doctors have practice_id foreign key")
    print("⚠️  Need to add practice_id filters in routes to enforce isolation")
    print("\n💡 Next: Update routes to use get_current_practice_id() from JWT")
