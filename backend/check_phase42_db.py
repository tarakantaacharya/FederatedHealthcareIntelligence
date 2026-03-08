#!/usr/bin/env python
"""Quick check and fix for Phase 42 database columns"""
import sys
import traceback

try:
    from sqlalchemy import inspect, text
    from app.database import engine
    
    print("Connecting to database...")
    
    with engine.begin() as conn:
        inspector = inspect(engine)
        
        # Check model_weights table
        print("\nChecking model_weights table...")
        mw_columns = {col['name'] for col in inspector.get_columns('model_weights')}
        print(f"  Found {len(mw_columns)} columns")
        
        mw_needed = {'actual_hyperparameters', 'hyperparameter_compliant'}
        mw_missing = mw_needed - mw_columns
        
        if mw_missing:
            print(f"  ❌ Missing: {mw_missing}")
            for col in mw_missing:
                if col == 'actual_hyperparameters':
                    try:
                        conn.execute(text("ALTER TABLE model_weights ADD COLUMN actual_hyperparameters JSON NULL"))
                        print(f"    ✅ Added {col}")
                    except Exception as e:
                        print(f"    ⚠️  {col}: {e}")
                elif col == 'hyperparameter_compliant':
                    try:
                        conn.execute(text("ALTER TABLE model_weights ADD COLUMN hyperparameter_compliant BOOLEAN NOT NULL DEFAULT FALSE"))
                        print(f"    ✅ Added {col}")
                    except Exception as e:
                        print(f"    ⚠️  {col}: {e}")
        else:
            print("  ✅ All columns exist")
        
        # Check training_rounds table
        print("\nChecking training_rounds table...")
        tr_columns = {col['name'] for col in inspector.get_columns('training_rounds')}
        print(f"  Found {len(tr_columns)} columns")
        
        tr_needed = {'tft_hidden_size', 'tft_attention_heads', 'tft_dropout', 'tft_regularization_factor'}
        tr_missing = tr_needed - tr_columns
        
        if tr_missing:
            print(f"  ❌ Missing: {tr_missing}")
            for col in tr_missing:
                try:
                    if col in ['tft_hidden_size', 'tft_attention_heads']:
                        conn.execute(text(f"ALTER TABLE training_rounds ADD COLUMN {col} INT NULL"))
                    else:
                        conn.execute(text(f"ALTER TABLE training_rounds ADD COLUMN {col} FLOAT NULL"))
                    print(f"    ✅ Added {col}")
                except Exception as e:
                    print(f"    ⚠️  {col}: {e}")
        else:
            print("  ✅ All columns exist")
    
    print("\n✅ Database schema check complete!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    traceback.print_exc()
    sys.exit(1)
