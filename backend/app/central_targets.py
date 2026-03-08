"""
Central Governance: Approved Target Columns for Federated Learning Rounds
-----------------------------------------------------------
This whitelist defines the ONLY target columns allowed for training rounds.
No defaults. No dynamic inference. No hospital overrides.

Enforced at:
- Round creation (routes/rounds.py)
- Training initialization (services/training_service.py)
"""

ALLOWED_TARGET_COLUMNS = [
    "bed_occupancy",
    "icu_admissions",
    "er_visits",
    "avg_length_of_stay",
    "icu_ventilator_usage",
    "readmission_rate",
    "mortality_rate",
    "staff_utilization",
    "surgery_volume",
    "infection_rate",
    "ambulance_arrivals",
    "outpatient_volume",
    "lab_test_volume",
    "pharmacy_dispense_rate",
    "critical_case_ratio"
]


def is_valid_target(target_column: str) -> bool:
    """
    Validate if target column is approved by central governance
    
    Args:
        target_column: Column name to validate
    
    Returns:
        True if target is in allowed list, False otherwise
    """
    return target_column in ALLOWED_TARGET_COLUMNS


def get_allowed_targets() -> list:
    """
    Get list of allowed target columns
    
    Returns:
        List of approved target column names
    """
    return ALLOWED_TARGET_COLUMNS.copy()
