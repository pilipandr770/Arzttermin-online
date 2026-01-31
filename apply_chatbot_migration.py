"""
Apply chatbot_instructions migration to remote database
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv('DATABASE_URL')
db_schema = os.getenv('DB_SCHEMA', 'public')

if not database_url:
    print("❌ ERROR: DATABASE_URL not found in .env")
    exit(1)

print(f'🔌 Connecting to database...')
print(f'📂 Schema: {db_schema}')

try:
    conn = psycopg2.connect(database_url, sslmode='require')
    cursor = conn.cursor()
    
    print('✅ Connected!')
    
    # Check if column exists
    cursor.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = %s 
        AND table_name = 'practices' 
        AND column_name = 'chatbot_instructions'
    """, (db_schema,))
    
    if cursor.fetchone():
        print('✅ Column chatbot_instructions already exists!')
    else:
        print('❌ Column does not exist. Adding...')
        cursor.execute(f"""
            ALTER TABLE {db_schema}.practices 
            ADD COLUMN chatbot_instructions TEXT NULL
        """)
        conn.commit()
        print('✅ Column chatbot_instructions added successfully!')
    
    # Verify
    cursor.execute(f"""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_schema = %s 
        AND table_name = 'practices'
        AND column_name = 'chatbot_instructions'
    """, (db_schema,))
    
    result = cursor.fetchone()
    if result:
        print(f'\n📋 Column details:')
        print(f'   Name: {result[0]}')
        print(f'   Type: {result[1]}')
        print(f'   Nullable: {result[2]}')
    
    cursor.close()
    conn.close()
    
    print('\n✅ Migration completed successfully!')
    print('🔄 Restart the Flask server to apply changes')
    
except Exception as e:
    print(f'❌ Error: {e}')
    exit(1)
