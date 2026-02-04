#!/usr/bin/env python
"""
Простой скрипт для создания первого администратора
"""
import sys
import uuid
import bcrypt
from getpass import getpass
from app import create_app, db

def create_admin():
    app = create_app()
    
    with app.app_context():
        print("=== Создание администратора ===\n")
        
        # Get admin details
        print("Введите данные администратора:")
        username = input("Username: ").strip()
        
        if not username:
            print("❌ Username не может быть пустым")
            return
        
        email = input("Email: ").strip()
        
        if not email:
            print("❌ Email не может быть пустым")
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
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        admin_id = str(uuid.uuid4())
        
        # Create admin with SQL
        try:
            db.session.execute(db.text("""
                INSERT INTO terminfinder.admins 
                (id, username, email, password_hash, role, permissions, is_active, two_factor_enabled, failed_login_attempts) 
                VALUES (:id, :username, :email, :password_hash, :role, :permissions, true, false, 0)
            """), {
                'id': admin_id,
                'username': username,
                'email': email,
                'password_hash': password_hash,
                'role': role,
                'permissions': []
            })
            
            db.session.commit()
            
            print(f"\n✅ Администратор успешно создан!")
            print(f"   Username: {username}")
            print(f"   Email: {email}")
            print(f"   Role: {role}")
            print(f"   ID: {admin_id}")
            print(f"\n🔐 Теперь вы можете войти по адресу: /admin/login")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Ошибка при создании администратора: {e}")
            sys.exit(1)

if __name__ == "__main__":
    create_admin()
