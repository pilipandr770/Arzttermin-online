"""
Скрипт для проверки и создания праксиса для врачей без праксиса
"""
from app import create_app, db
from app.models import Doctor, Practice
from datetime import datetime

app = create_app()

with app.app_context():
    print("\n" + "=" * 60)
    print("🔍 ПРОВЕРКА ВРАЧЕЙ БЕЗ ПРАКСИСА")
    print("=" * 60)
    
    # Находим всех врачей
    doctors = Doctor.query.all()
    print(f"\n📊 Всего врачей в базе: {len(doctors)}")
    
    doctors_without_practice = []
    
    for doctor in doctors:
        if not doctor.practice_id:
            doctors_without_practice.append(doctor)
            print(f"\n❌ Врач БЕЗ праксиса:")
            print(f"   ID: {doctor.id}")
            print(f"   Имя: {doctor.first_name} {doctor.last_name}")
            print(f"   Email: {doctor.email}")
            print(f"   Специальность: {doctor.speciality}")
    
    if not doctors_without_practice:
        print("\n✅ Все врачи имеют праксис!")
    else:
        print(f"\n⚠️ Найдено врачей без праксиса: {len(doctors_without_practice)}")
        
        # Спрашиваем, создать ли праксисы
        answer = input("\n❓ Создать праксисы для этих врачей автоматически? (y/n): ")
        
        if answer.lower() == 'y':
            print("\n🔨 Создаю праксисы...")
            
            for doctor in doctors_without_practice:
                # Создаем праксис
                practice = Practice(
                    name=f"Praxis Dr. {doctor.last_name}",
                    vat_number=doctor.tax_number if doctor.tax_number else '',
                    owner_email=doctor.email,
                    phone='',
                    address='{}',  # Пустой JSON объект
                    verified=True,
                    verified_at=datetime.utcnow()
                )
                db.session.add(practice)
                db.session.flush()
                
                # Привязываем к врачу
                doctor.practice_id = practice.id
                
                print(f"   ✅ Создан праксис для {doctor.first_name} {doctor.last_name}")
                print(f"      Practice ID: {practice.id}")
                print(f"      Practice Name: {practice.name}")
            
            db.session.commit()
            print("\n✅ Все праксисы созданы и сохранены!")
        else:
            print("\n⏭️ Пропущено")
    
    # Показываем финальную статистику
    print("\n" + "=" * 60)
    print("📊 ФИНАЛЬНАЯ СТАТИСТИКА")
    print("=" * 60)
    
    doctors = Doctor.query.all()
    practices = Practice.query.all()
    
    doctors_with_practice = sum(1 for d in doctors if d.practice_id)
    
    print(f"\n✅ Всего врачей: {len(doctors)}")
    print(f"✅ Врачей с праксисом: {doctors_with_practice}")
    print(f"✅ Всего праксисов: {len(practices)}")
    
    # Показываем все связки
    print("\n📋 Список врачей и их праксисов:")
    for doctor in doctors:
        if doctor.practice_id:
            practice = Practice.query.get(doctor.practice_id)
            print(f"\n   👨‍⚕️ {doctor.first_name} {doctor.last_name}")
            print(f"      📧 {doctor.email}")
            print(f"      🏥 {practice.name if practice else 'NOT FOUND'}")
            print(f"      🆔 Practice ID: {doctor.practice_id}")
        else:
            print(f"\n   ❌ {doctor.first_name} {doctor.last_name} - БЕЗ ПРАКСИСА")
    
    print("\n" + "=" * 60)
    print("✅ ГОТОВО!")
    print("=" * 60 + "\n")
