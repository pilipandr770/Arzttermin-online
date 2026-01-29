"""
Script to update all routes to use new JWT format
Run with: python update_jwt.py
"""
import re
import os

# Files to update
files = [
    'app/routes/patient.py',
    'app/routes/doctor.py',
    'app/routes/practice.py',
    'app/routes/booking.py',
]

for filepath in files:
    if not os.path.exists(filepath):
        print(f"Skipping {filepath} - not found")
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace import
    content = re.sub(
        r'from flask_jwt_extended import ([^;\n]+)',
        r'from flask_jwt_extended import \1\nfrom app.utils.jwt_helpers import get_current_user',
        content,
        count=1
    )
    
    # Replace identity = get_jwt_identity() with identity = get_current_user()
    content = content.replace(
        'identity = get_jwt_identity()',
        'identity = get_current_user()'
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Updated {filepath}")

print("\n✅ All files updated!")
