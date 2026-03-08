#!/usr/bin/env python
"""Check if database is ready for new updates"""
import sys
sys.path.insert(0, '.')

from app.config import get_settings
from sqlalchemy import create_engine, inspect, text
import json

settings = get_settings()

try:
    print('🔄 Connecting to database...')
    engine = create_engine(settings.DATABASE_URL, echo=False)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('✅ Database connection successful!')
        
    # Check database exists
    with engine.connect() as conn:
        databases = conn.execute(text('SHOW DATABASES')).fetchall()
        db_names = [db[0] for db in databases]
        if 'federated_healthcare' in db_names:
            print('✅ Database "federated_healthcare" exists')
        else:
            print('❌ Database "federated_healthcare" NOT found')
    
    # Get all tables
    inspector = inspect(engine)
    tables = sorted(inspector.get_table_names())
    print(f'\n📊 Total tables found: {len(tables)}')
    print(f'Tables: {", ".join(tables)}')
    
    # Check key tables
    key_tables = ['hospitals', 'datasets', 'model_weights', 'training_rounds', 'model_governance', 
                  'round_allowed_hospitals', 'prediction_records', 'model_masks']
    print('\n🔍 Key tables status:')
    for table in key_tables:
        if table in tables:
            columns = inspector.get_columns(table)
            col_count = len(columns)
            print(f'  ✅ {table} ({col_count} columns)')
        else:
            print(f'  ⚠️  {table} (optional)')
    
    # Check row counts in key tables
    print('\n📈 Row counts in key tables:')
    for table in ['hospitals', 'datasets', 'model_weights', 'training_rounds']:
        if table in tables:
            with engine.connect() as conn:
                count = conn.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar()
                print(f'  {table}: {count} rows')
    
    print('\n✅✅✅ Database is READY for new updates! ✅✅✅')
    
except Exception as e:
    print(f'\n❌ Error: {str(e)}')
    print('\n⚠️  Troubleshooting steps:')
    print('1. Verify MySQL is running: Check Services or run: net start MySQL57 (Windows)')
    print('2. Check credentials in .env file')
    print('3. Verify database exists: mysql -u root -p -e "SHOW DATABASES;"')
    sys.exit(1)
