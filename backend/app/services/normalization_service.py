"""
Data normalization service
Transforms hospital CSV data to canonical schema format
"""
import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List
from sqlalchemy.orm import Session
from app.services.mapping_service import MappingService
from app.services.category_service import CategoryService   # ✅ ADDED IMPORT
from app.models.dataset import Dataset
from app.config import get_settings

settings = get_settings()


class NormalizationService:
    """Service for normalizing data to canonical schema"""

    def __init__(self):
        self.mapping_service = MappingService()
        self.category_service = CategoryService()   # ✅ ADDED CATEGORY SERVICE

    def normalize_csv(
        self,
        dataset_id: int,
        db: Session
    ) -> Dict:
        """
        Normalize CSV data to canonical schema format
        """
        # Get dataset and mapping
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")

        mapping_data = self.mapping_service.get_dataset_mapping(dataset_id, db)

        if not mapping_data['mappings']:
            raise ValueError("No mappings found for dataset. Please map columns first.")

        # Load original CSV - normalize path for Windows/Unix compatibility
        file_path = os.path.normpath(dataset.file_path)
        df = pd.read_csv(file_path)

        # Create mapping dictionary
        column_mapping = {
            m['original_column']: m['canonical_field']
            for m in mapping_data['mappings']
        }

        # Rename columns
        df_normalized = df.rename(columns=column_mapping)

        # Apply type conversions and validations
        df_normalized = self._apply_type_conversions(df_normalized)

        # Apply data cleaning
        df_normalized = self._clean_data(df_normalized)

        # ✅ NEW — DETECT CATEGORIES AFTER CLEANING
        detected_categories = self._detect_categories(df_normalized)

        category_validations = {}
        for category in detected_categories:
            category_validations[category] = {'is_valid': True, 'errors': [], 'warnings': []}
            
            if len(df_normalized) > 0:
                # Extract fields belonging to this category
                category_field_specs = self.category_service.get_category_fields(category)
                
                # Map canonical field names to prefixed names for validation
                category_data = {}
                for field_name in category_field_specs.keys():
                    prefixed_name = self.category_service.get_prefixed_field_name(category, field_name)
                    # Check if canonical field exists in dataframe
                    if field_name in df_normalized.columns:
                        try:
                            category_data[prefixed_name] = df_normalized[field_name].iloc[0]
                        except (IndexError, KeyError):
                            pass
                
                if category_data:
                    validation = self.category_service.validate_category_data(category, category_data)
                    category_validations[category] = validation

        # Validate against core schema
        validation_result = self._validate_normalized_data(df_normalized)

        # Save normalized CSV
        normalized_dir = os.path.join(
            settings.UPLOAD_DIR,
            str(dataset.hospital_id),
            'normalized'
        )
        os.makedirs(normalized_dir, exist_ok=True)

        original_filename = os.path.basename(dataset.file_path)
        normalized_filename = f"normalized_{original_filename}"
        normalized_path = os.path.join(normalized_dir, normalized_filename)

        df_normalized.to_csv(normalized_path, index=False)

        # Update dataset record
        dataset.is_normalized = True
        dataset.normalized_path = normalized_path
        db.commit()

        # ✅ UPDATED RETURN WITH CATEGORY RESULTS
        return {
            'status': 'normalization_complete',
            'dataset_id': dataset_id,
            'original_path': dataset.file_path,
            'normalized_path': normalized_path,
            'original_rows': len(df),
            'normalized_rows': len(df_normalized),
            'original_columns': len(df.columns),
            'normalized_columns': len(df_normalized.columns),
            'detected_categories': detected_categories,      # NEW
            'category_validations': category_validations,    # NEW
            'validation': validation_result,
            'normalized_at': datetime.now().isoformat()
        }

    def _apply_type_conversions(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # Timestamp conversion
        if 'timestamp' in df.columns:
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            except:
                pass

        # Integer conversions
        integer_fields = [
            'bed_occupancy', 'er_visits', 'icu_occupancy', 'admissions',
            'discharges', 'surgery_count', 'staff_count', 'hospital_capacity',
            'num_operating_rooms', 'num_icu_beds', 'day_of_week', 'month',
            'day_of_month', 'hour'
        ]

        for field in integer_fields:
            if field in df.columns:
                try:
                    df[field] = pd.to_numeric(df[field], errors='coerce').fillna(0).astype(int)
                except:
                    pass

        # Float conversions
        float_fields = ['average_length_of_stay']

        for field in float_fields:
            if field in df.columns:
                try:
                    df[field] = pd.to_numeric(df[field], errors='coerce')
                except:
                    pass

        # Boolean conversions
        boolean_fields = ['is_holiday', 'is_weekend', 'is_flu_season']

        for field in boolean_fields:
            if field in df.columns:
                try:
                    df[field] = df[field].astype(bool)
                except:
                    pass

        # Convert numeric fields to float32 one at a time
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        for col in numeric_cols:
            try:
                df[col] = df[col].astype("float32")
            except:
                pass

        return df

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        required_fields = ['timestamp', 'bed_occupancy']
        required_present = [f for f in required_fields if f in df.columns]

        if required_present:
            df = df.dropna(subset=required_present)

        # Ensure non-negative counts
        count_fields = [
            'bed_occupancy', 'er_visits', 'icu_occupancy', 'admissions',
            'discharges', 'surgery_count', 'staff_count'
        ]

        for field in count_fields:
            if field in df.columns:
                df[field] = df[field].clip(lower=0)

        # Valid ranges
        if 'day_of_week' in df.columns:
            df['day_of_week'] = df['day_of_week'].clip(0, 6)

        if 'month' in df.columns:
            df['month'] = df['month'].clip(1, 12)

        if 'hour' in df.columns:
            df['hour'] = df['hour'].clip(0, 23)

        # Capacity constraints - assign one column at a time
        if 'bed_occupancy' in df.columns and 'hospital_capacity' in df.columns:
            result = df.apply(
                lambda row: min(row['bed_occupancy'], row['hospital_capacity'])
                if pd.notna(row['hospital_capacity']) else row['bed_occupancy'],
                axis=1
            )
            df['bed_occupancy'] = result

        if 'icu_occupancy' in df.columns and 'num_icu_beds' in df.columns:
            result = df.apply(
                lambda row: min(row['icu_occupancy'], row['num_icu_beds'])
                if pd.notna(row['num_icu_beds']) else row['icu_occupancy'],
                axis=1
            )
            df['icu_occupancy'] = result

        return df

    def _validate_normalized_data(self, df: pd.DataFrame) -> Dict:
        errors = []
        warnings = []

        required_fields = ['timestamp', 'bed_occupancy']
        missing = [f for f in required_fields if f not in df.columns]

        if missing:
            errors.append(f"Missing required fields: {', '.join(missing)}")

        if 'timestamp' in df.columns:
            null_ts = df['timestamp'].isnull().sum()
            if null_ts > 0:
                warnings.append(f"{null_ts} rows with null timestamps")

        if 'bed_occupancy' in df.columns:
            null_bo = df['bed_occupancy'].isnull().sum()
            if null_bo > 0:
                warnings.append(f"{null_bo} rows with null bed_occupancy")

        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'validated_fields': list(df.columns),
            'total_rows': len(df)
        }

    # ✅ NEW — DETECT CATEGORIES
    def _detect_categories(self, df: pd.DataFrame) -> List[str]:
        """
        Detect which categories are present in the data
        """
        detected_categories = []
        all_categories = self.category_service.get_all_category_names()

        for category in all_categories:
            category_fields = self.category_service.get_category_field_list(category)

            if any(field in df.columns for field in category_fields):
                detected_categories.append(category)

        return detected_categories

    def get_normalized_preview(
        self,
        dataset_id: int,
        db: Session,
        num_rows: int = 10
    ) -> Dict:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

        if not dataset or not dataset.is_normalized:
            raise ValueError("Dataset not normalized")

        df = pd.read_csv(dataset.normalized_path, nrows=num_rows)

        preview_data = df.to_dict(orient='records')

        return {
            'dataset_id': dataset_id,
            'num_rows': len(preview_data),
            'columns': list(df.columns),
            'data': preview_data
        }
