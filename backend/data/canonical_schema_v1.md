# Canonical Hospital Resource Forecasting Schema v1.0

**Purpose:** Standardized data format for federated multi-hospital resource demand forecasting

**Last Updated:** Phase 8

---

## Overview

This schema defines the standard structure for hospital resource data across all participating hospitals in the federated learning network. By normalizing data to this schema, hospitals with different data formats can collaboratively train models while maintaining data privacy.

---

## Field Categories

### 1. Static Features
**Purpose:** Hospital characteristics that remain constant over time

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `hospital_id` | string | Yes | Unique hospital identifier | "HOSP-001" |
| `hospital_name` | string | No | Hospital name | "City General Hospital" |
| `hospital_capacity` | integer | Yes | Total bed capacity | 500 |
| `hospital_type` | string | No | Specialization type | "general" |
| `location` | string | No | Geographic location | "New York, NY" |
| `num_operating_rooms` | integer | No | Number of ORs | 15 |
| `num_icu_beds` | integer | No | Number of ICU beds | 50 |

**Hospital Types:** general, pediatric, cardiac, trauma, surgical, teaching

---

### 2. Historical Features
**Purpose:** Time-series observations of past hospital resource usage

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `timestamp` | datetime | Yes | Observation date/time | "2024-01-15 08:00:00" |
| `bed_occupancy` | integer | Yes | Occupied beds | 350 |
| `er_visits` | integer | No | Emergency room visits | 45 |
| `icu_occupancy` | integer | No | Occupied ICU beds | 38 |
| `admissions` | integer | No | Patient admissions | 25 |
| `discharges` | integer | No | Patient discharges | 20 |
| `surgery_count` | integer | No | Surgeries performed | 12 |
| `staff_count` | integer | No | Staff on duty | 150 |
| `average_length_of_stay` | float | No | Avg LOS in days | 4.5 |

**Note:** `bed_occupancy` is the primary forecasting target

---

### 3. Known Future Features
**Purpose:** Features that are known in advance for future dates (calendar information)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `day_of_week` | integer | Yes | 0=Monday, 6=Sunday | 2 (Wednesday) |
| `month` | integer | Yes | 1=January, 12=December | 3 (March) |
| `day_of_month` | integer | No | Day of month (1-31) | 15 |
| `hour` | integer | No | Hour of day (0-23) | 14 |
| `is_holiday` | boolean | No | Public holiday flag | false |
| `is_weekend` | boolean | No | Weekend flag | false |
| `season` | string | No | Season (winter/spring/summer/fall) | "spring" |
| `is_flu_season` | boolean | No | Flu season flag (Oct-Mar) | false |

**Usage:** These features help the model understand temporal patterns and seasonal effects

---

### 4. Target Variables
**Purpose:** Variables to be predicted (forecast outputs)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `future_bed_occupancy` | integer | No | Forecasted bed occupancy | 365 |
| `future_er_visits` | integer | No | Forecasted ER visits | 50 |
| `future_icu_occupancy` | integer | No | Forecasted ICU occupancy | 40 |
| `future_admissions` | integer | No | Forecasted admissions | 30 |

**Note:** During training, use historical values. During inference, these are predicted.

---

## Validation Rules

1. **Non-negative counts:** All count fields (bed_occupancy, er_visits, etc.) must be >= 0
2. **Capacity constraints:** bed_occupancy ≤ hospital_capacity
3. **ICU constraints:** icu_occupancy ≤ num_icu_beds (if specified)
4. **Timestamp format:** Must be valid datetime in "YYYY-MM-DD HH:MM:SS" format
5. **Day/month ranges:** day_of_week (0-6), month (1-12), hour (0-23)

---

## Common Field Synonyms

To help with automatic mapping, we recognize these common variations:

**Timestamp:**
- date, datetime, time, date_time, observation_date, record_date

**Bed Occupancy:**
- beds_occupied, occupied_beds, bed_count, current_beds, total_beds_used

**ER Visits:**
- emergency_visits, er_count, emergency_room_visits, emergency_cases, ed_visits

**ICU Occupancy:**
- icu_beds, icu_count, intensive_care_beds, critical_care_beds

**Admissions:**
- patient_admissions, new_admissions, admitted_patients, intake

**Discharges:**
- patient_discharges, released_patients, discharged_count

---

## Usage in Federated Learning

### Phase 9 (Mapping Engine)
Hospitals upload CSVs → System suggests mapping from hospital columns to canonical fields

### Phase 10 (Normalization Engine)
Original data → Normalized to canonical schema → Used for model training

### Benefits
- **Interoperability:** Hospitals with different formats can collaborate
- **Privacy:** Only standardized, aggregated features shared (no raw patient data)
- **Consistency:** All models trained on same feature set
- **Extensibility:** Phase 11 adds treatment category extensions

---

## Future Extensions

**Phase 11:** Category-specific fields (ICU, Emergency, OPD, IPD, Surgery, Pediatrics, Cardiology)

**Example categories:**
- ICU: ventilator usage, sedation levels, monitoring equipment
- Emergency: triage levels, ambulance arrivals, trauma cases
- Surgery: operating room utilization, anesthesia types
- Pediatrics: age-specific metrics, vaccination schedules

---

## Example Data Row

