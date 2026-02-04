#!/usr/bin/env python
"""
Script to create the first admin user
Usage: python create_admin.py
"""
import sys
import uuid
from getpass import getpass
from app import create_app, db
from app.models.admin import Admin

def create_admin():
    app = create_app()
    
    with app.app_context():
        print("=== Создание администратора ===\n")
        
        # Check if any admins exist
        existing_admins = Admin.query.count()
        if existing_admins > 0:
            print(f"⚠️  В системе уже есть {existing_admins} администратор(ов)")
            response = input("Продолжить создание нового администратора? (y/n): ")
            if response.lower() != 'y':
                print("Отменено")
                return
        
        # Get admin details
        print("\nВведите данные администратора:")
        username = input("Username: ").strip()
        
        if not username:
            print("❌ Username не может быть пустым")
            return
        
        # Check if username exists
        if Admin.query.filter_by(username=username).first():
            print(f"❌ Администратор с username '{username}' уже существует")
            return
        
        email = input("Email: ").strip()
        
        if not email:
            print("❌ Email не может быть пустым")
            return
        
        # Check if email exists
        if Admin.query.filter_by(email=email).first():
            print(f"❌ Администратор с email '{email}' уже существует")
            return
        
        password = getpass("Password: ")
        password_confirm = getpass("Подтвердите password: ")
        
        if password != password_confirm:
            print("❌ Пароли не совпадают")
            return
        
        if len(password) < 8:
            print("❌ Пароль должен содержать минимум 8 символов")
            return
        
        # Select role
        print("\nВыберите роль:")
        print("1. super_admin (полный доступ)")
        print("2. admin (управление пользователями)")
        print("3. moderator (только просмотр)")
        role_choice = input("Выбор (1-3) [1]: ").strip() or "1"
        
        role_map = {
            "1": "super_admin",
            "2": "admin",
            "3": "moderator"
        }
        
        role = role_map.get(role_choice, "super_admin")
        
        # Create admin
        try:
            admin = Admin(
                id=uuid.uuid4(),
                username=username,
                email=email,
                role=role
            )
            admin.set_password(password)
            
            db.session.add(admin)
            db.session.commit()
            
            print(f"\n✅ Администратор успешно создан!")
            print(f"   Username: {username}")
            print(f"   Email: {email}")
            print(f"   Role: {role}")
            print(f"   ID: {admin.id}")
            print(f"\n🔐 Теперь вы можете войти по адресу: /admin/login")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Ошибка при создании администратора: {e}")
            sys.exit(1)

if __name__ == "__main__":
    create_admin()
