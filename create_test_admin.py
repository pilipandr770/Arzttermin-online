#!/usr/bin/env python
"""
Створення тестового адміна з відомим паролем
"""
import bcrypt
import uuid
from datetime import datetime
from app import create_app, db

app = create_app()

with app.app_context():
    # Admin credentials
    admin_id = str(uuid.uuid4())
    username = "admin"
    email = "admin@terminfinder.com"
    password = "admin123"

    # Hash password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Delete if exists
    db.session.execute(db.text("""
        DELETE FROM terminfinder.admins 
        WHERE username = :username OR email = :email
    """), {"username": username, "email": email})

    # Insert new admin
    db.session.execute(db.text("""
        INSERT INTO terminfinder.admins (
            id, username, email, password_hash, role, permissions, 
            is_active, two_factor_enabled, failed_login_attempts,
            created_at, updated_at
        ) VALUES (
            :id, :username, :email, :password_hash, :role, :permissions, 
            :is_active, :two_factor, :failed_attempts, :created_at, :updated_at
        )
    """), {
        "id": admin_id,
        "username": username,
        "email": email,
        "password_hash": password_hash,
        "role": 'super_admin',
        "permissions": ['manage_users', 'manage_doctors', 'manage_bookings', 'view_analytics', 'manage_settings'],
        "is_active": True,
        "two_factor": False,
        "failed_attempts": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

    db.session.commit()

    print("✅ Тестовий адмін створено успішно!")
    print(f"Username: {username}")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print(f"ID: {admin_id}")
