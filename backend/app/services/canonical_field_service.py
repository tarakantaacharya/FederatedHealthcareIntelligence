"""
Canonical field service
"""
from sqlalchemy.orm import Session
from app.models.canonical_field import CanonicalField
from typing import List, Dict, Tuple


class CanonicalFieldService:
    """Service for canonical field management"""

    DEFAULT_FIELDS_DATA = [
        {"field_name": "bed_occupancy", "description": "Total number of occupied beds in the hospital", "data_type": "integer", "category": "resource", "unit": "beds"},
        {"field_name": "bed_occupancy_rate", "description": "Bed occupancy percentage", "data_type": "float", "category": "resource", "unit": "percentage"},
        {"field_name": "available_beds", "description": "Number of available beds", "data_type": "integer", "category": "resource", "unit": "beds"},
        {"field_name": "icu_admissions", "description": "Number of patients admitted to ICU", "data_type": "integer", "category": "utilization", "unit": "count"},
        {"field_name": "icu_occupancy", "description": "Number of occupied ICU beds", "data_type": "integer", "category": "resource", "unit": "beds"},
        {"field_name": "icu_ventilator_usage", "description": "Number of active ventilator units in use", "data_type": "integer", "category": "resource", "unit": "units"},
        {"field_name": "er_visits", "description": "Emergency room visit count", "data_type": "integer", "category": "utilization", "unit": "visits"},
        {"field_name": "admissions", "description": "Total inpatient admissions", "data_type": "integer", "category": "utilization", "unit": "count"},
        {"field_name": "discharges", "description": "Total patient discharges", "data_type": "integer", "category": "utilization", "unit": "count"},
        {"field_name": "avg_length_of_stay", "description": "Average patient length of stay in days", "data_type": "float", "category": "outcome", "unit": "days"},
        {"field_name": "length_of_stay", "description": "Length of stay in days", "data_type": "float", "category": "outcome", "unit": "days"},
        {"field_name": "readmission_rate", "description": "Percentage of patients readmitted within 30 days", "data_type": "float", "category": "outcome", "unit": "percentage"},
        {"field_name": "mortality_rate", "description": "Hospital mortality rate as percentage", "data_type": "float", "category": "outcome", "unit": "percentage"},
        {"field_name": "infection_rate", "description": "Hospital-acquired infection rate", "data_type": "float", "category": "outcome", "unit": "percentage"},
        {"field_name": "hospital_acquired_infection_rate", "description": "Hospital-acquired infection rate", "data_type": "float", "category": "outcome", "unit": "percentage"},
        {"field_name": "surgery_volume", "description": "Number of surgical procedures performed", "data_type": "integer", "category": "utilization", "unit": "surgeries"},
        {"field_name": "outpatient_volume", "description": "Number of outpatient visits", "data_type": "integer", "category": "utilization", "unit": "visits"},
        {"field_name": "lab_test_volume", "description": "Number of laboratory tests performed", "data_type": "integer", "category": "utilization", "unit": "tests"},
        {"field_name": "pharmacy_dispense_rate", "description": "Number of prescriptions dispensed", "data_type": "integer", "category": "utilization", "unit": "prescriptions"},
        {"field_name": "critical_case_ratio", "description": "Ratio of critical cases to total cases", "data_type": "float", "category": "outcome", "unit": "ratio"},
        {"field_name": "staff_utilization", "description": "Percentage of staff utilization", "data_type": "float", "category": "resource", "unit": "percentage"},
        {"field_name": "staff_count", "description": "Number of active clinical staff", "data_type": "integer", "category": "resource", "unit": "count"},
        {"field_name": "nurse_count", "description": "Number of active nurses", "data_type": "integer", "category": "resource", "unit": "count"},
        {"field_name": "doctor_count", "description": "Number of active doctors", "data_type": "integer", "category": "resource", "unit": "count"},
        {"field_name": "ambulance_arrivals", "description": "Number of ambulance arrivals", "data_type": "integer", "category": "utilization", "unit": "arrivals"},
        {"field_name": "waiting_time_minutes", "description": "Average waiting time in minutes", "data_type": "float", "category": "utilization", "unit": "minutes"},
        {"field_name": "emergency_wait_time_avg", "description": "Average emergency wait time in minutes", "data_type": "float", "category": "utilization", "unit": "minutes"},
        {"field_name": "patient_satisfaction", "description": "Patient satisfaction score", "data_type": "float", "category": "outcome", "unit": "score"},
        {"field_name": "patient_count", "description": "Total patient count", "data_type": "integer", "category": "utilization", "unit": "count"},
        {"field_name": "flu_cases", "description": "Number of influenza cases", "data_type": "integer", "category": "outcome", "unit": "count"},
        {"field_name": "covid_cases", "description": "Number of COVID-19 cases", "data_type": "integer", "category": "outcome", "unit": "count"},
        {"field_name": "sepsis_cases", "description": "Number of sepsis cases", "data_type": "integer", "category": "outcome", "unit": "count"},
        {"field_name": "ventilator_usage", "description": "Ventilator usage count", "data_type": "integer", "category": "resource", "unit": "units"},
        {"field_name": "oxygen_consumption", "description": "Oxygen consumption volume", "data_type": "float", "category": "resource", "unit": "liters"},
        {"field_name": "resource_utilization", "description": "Overall resource utilization score", "data_type": "float", "category": "resource", "unit": "percentage"},
        {"field_name": "hospital_capacity", "description": "Total hospital capacity", "data_type": "integer", "category": "resource", "unit": "beds"},
        {"field_name": "num_icu_beds", "description": "Total ICU bed count", "data_type": "integer", "category": "resource", "unit": "beds"},
        {"field_name": "num_general_beds", "description": "Total general bed count", "data_type": "integer", "category": "resource", "unit": "beds"},
        {"field_name": "num_operating_rooms", "description": "Number of operating rooms", "data_type": "integer", "category": "resource", "unit": "rooms"},
        {"field_name": "hospital_id", "description": "Unique hospital identifier", "data_type": "string", "category": "identity", "unit": "id"},
        {"field_name": "hospital_name", "description": "Hospital name", "data_type": "string", "category": "identity", "unit": "name"},
        {"field_name": "department", "description": "Hospital department", "data_type": "string", "category": "identity", "unit": "name"},
        {"field_name": "diagnosis", "description": "Primary diagnosis code or label", "data_type": "string", "category": "clinical", "unit": "code"},
        {"field_name": "admission_date", "description": "Admission date", "data_type": "datetime", "category": "time", "unit": "datetime"},
        {"field_name": "discharge_date", "description": "Discharge date", "data_type": "datetime", "category": "time", "unit": "datetime"},
        {"field_name": "timestamp", "description": "Observation timestamp", "data_type": "datetime", "category": "time", "unit": "datetime"},
        {"field_name": "year", "description": "Calendar year", "data_type": "integer", "category": "time", "unit": "year"},
        {"field_name": "month", "description": "Calendar month", "data_type": "integer", "category": "time", "unit": "month"},
        {"field_name": "day", "description": "Day of month", "data_type": "integer", "category": "time", "unit": "day"},
        {"field_name": "day_of_week", "description": "Day of week", "data_type": "integer", "category": "time", "unit": "day"},
        {"field_name": "hour", "description": "Hour of day", "data_type": "integer", "category": "time", "unit": "hour"},
        {"field_name": "is_weekend", "description": "Weekend indicator", "data_type": "boolean", "category": "time", "unit": "flag"},
        {"field_name": "is_holiday", "description": "Holiday indicator", "data_type": "boolean", "category": "time", "unit": "flag"},
        {"field_name": "season", "description": "Season label or index", "data_type": "string", "category": "time", "unit": "season"},
    ]

    @staticmethod
    def get_all_active_fields(db: Session) -> List[CanonicalField]:
        """Get all active canonical fields"""
        return db.query(CanonicalField).filter(
            CanonicalField.is_active == True
        ).order_by(CanonicalField.field_name).all()

    @staticmethod
    def get_field_by_name(db: Session, field_name: str) -> CanonicalField:
        """Get canonical field by name"""
        return db.query(CanonicalField).filter(
            CanonicalField.field_name == field_name,
            CanonicalField.is_active == True
        ).first()

    @staticmethod
    def is_valid_target(db: Session, target_column: str) -> Tuple[bool, str]:
        """
        Check if target column is a valid canonical field
        
        Returns:
            Tuple of (is_valid: bool, reason: str)
        """
        field = CanonicalFieldService.get_field_by_name(db, target_column)
        if field:
            return True, f"Valid target column: {target_column}"
        return False, f"Target column '{target_column}' is not registered in canonical schema"

    @staticmethod
    def populate_defaults(db: Session):
        """Populate default canonical fields (idempotent upsert)"""
        existing_fields = {
            field.field_name: field
            for field in db.query(CanonicalField).all()
        }

        added_count = 0
        for field_data in CanonicalFieldService.DEFAULT_FIELDS_DATA:
            field_name = field_data["field_name"]
            if field_name in existing_fields:
                continue
            db.add(CanonicalField(**field_data))
            added_count += 1

        if added_count > 0:
            db.commit()
