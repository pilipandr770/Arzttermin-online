"""
Script to apply migration on production database
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
database_url = os.getenv('DATABASE_URL')

if not database_url:
    print("ERROR: DATABASE_URL not found in environment variables")
    exit(1)

print(f"Connecting to database...")

try:
    # Connect to database with SSL
    conn = psycopg2.connect(database_url, sslmode='require')
    cursor = conn.cursor()
    
    print("Connected! Applying migration...")
    
    # Read migration file
    with open('migrations/update_patient_alerts.sql', 'r') as f:
        migration_sql = f.read()
    
    # Execute migration
    cursor.execute(migration_sql)
    conn.commit()
    
    print("✅ Migration applied successfully!")
    
    # Verify changes
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'terminfinder' 
        AND table_name = 'patient_alerts'
        ORDER BY ordinal_position;
    """)
    
    print("\nCurrent patient_alerts table structure:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error applying migration: {e}")
    exit(1)
