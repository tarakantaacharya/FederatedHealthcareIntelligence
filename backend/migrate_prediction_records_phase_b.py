#!/usr/bin/env python
"""Add Phase B columns to prediction_records table if missing."""
import sys
import os
from sqlalchemy import create_engine, text
from app.config import get_settings

settings = get_settings()


def migrate_prediction_records() -> None:
    print("Adding Phase B columns to prediction_records...")
    engine = create_engine(settings.DATABASE_URL, echo=False)

    with engine.begin() as conn:
        result = conn.execute(text("PRAGMA table_info(prediction_records)"))
        existing_columns = {row[1] for row in result}
        print(f"Existing columns: {sorted(existing_columns)}")

        columns_to_add = [
            ("prediction_timestamp", "DATETIME"),
            ("prediction_value", "REAL"),
            ("input_snapshot", "TEXT"),
            ("summary_text", "TEXT"),
        ]

        for column_name, column_type in columns_to_add:
            if column_name in existing_columns:
                print(f"- Column {column_name} already exists, skipping")
                continue
            print(f"+ Adding column {column_name} ({column_type})")
            conn.execute(text(f"ALTER TABLE prediction_records ADD COLUMN {column_name} {column_type}"))

        print("\nFinal schema:")
        result = conn.execute(text("PRAGMA table_info(prediction_records)"))
        for row in result:
            print(f"  {row[1]}: {row[2]}")

    print("Migration complete.")


if __name__ == "__main__":
    migrate_prediction_records()
