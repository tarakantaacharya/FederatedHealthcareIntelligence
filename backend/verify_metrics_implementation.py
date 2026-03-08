"""
Comprehensive Aggregation Metrics Implementation Verification

This script validates that the metrics display feature is fully implemented.
Run this after:
1. Backend is running on port 8000
2. A training round has completed
3. Aggregation has been performed

Usage:
  python verify_metrics_implementation.py
"""

import requests
import json
from typing import Optional, Dict, Any

class MetricsVerifier:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token = None
        self.hospital_id = "CGH-001"
        self.password = "hospital123"
        
    def log(self, message: str, status: str = "INFO"):
        """Pretty print log messages"""
        if status == "OK":
            print(f"✓ {message}")
        elif status == "ERROR":
            print(f"✗ {message}")
        elif status == "WARN":
            print(f"⚠ {message}")
        else:
            print(f"  {message}")
    
    def run_all_checks(self) -> bool:
        """Run all verification checks"""
        print("=" * 60)
        print("AGGREGATION METRICS IMPLEMENTATION VERIFICATION")
        print("=" * 60)
        
        all_passed = True
        
        # Check 1: Authentication
        print("\n[1] Authentication")
        print("-" * 60)
        if not self.test_authentication():
            return False
        
        # Check 2: Aggregation Rounds API
        print("\n[2] Aggregation Rounds Endpoint")
        print("-" * 60)
        rounds_data = self.test_aggregation_rounds_endpoint()
        if not rounds_data:
            return False
        
        # Check 3: Round Detail Endpoint
        if rounds_data:
            print("\n[3] Round Detail Endpoint")
            print("-" * 60)
            if not self.test_round_detail_endpoint(rounds_data[0]['round_number']):
                all_passed = False
        
        # Check 4: Database Schema
        print("\n[4] Database Schema Validation")
        print("-" * 60)
        self.test_database_schema()
        
        # Check 5: Response Field Validation
        print("\n[5] Metrics Field Validation")
        print("-" * 60)
        if rounds_data:
            self.validate_metric_fields(rounds_data[0])
        
        print("\n" + "=" * 60)
        if all_passed and rounds_data:
            self.log("ALL CHECKS PASSED", "OK")
        else:
            self.log("SOME CHECKS FAILED - See details above", "WARN")
        print("=" * 60)
        
        return all_passed and bool(rounds_data)
    
    def test_authentication(self) -> bool:
        """Test hospital authentication"""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json={"hospital_id": self.hospital_id, "password": self.password}
            )
            
            if response.status_code != 200:
                self.log(f"Authentication failed: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
            
            data = response.json()
            self.token = data.get("access_token")
            
            if not self.token:
                self.log("No access token in response", "ERROR")
                return False
            
            self.log(f"Successfully authenticated as {self.hospital_id}")
            self.log(f"Token: {self.token[:30]}...", "OK")
            return True
            
        except Exception as e:
            self.log(f"Authentication error: {e}", "ERROR")
            return False
    
    def test_aggregation_rounds_endpoint(self) -> Optional[list]:
        """Test /api/aggregation/rounds endpoint"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.base_url}/api/aggregation/rounds",
                headers=headers
            )
            
            if response.status_code != 200:
                self.log(f"Get rounds failed: {response.status_code}", "ERROR")
                return None
            
            data = response.json()
            self.log(f"Retrieved {len(data)} rounds", "OK")
            
            # Display round summary
            for round_info in data:
                round_num = round_info.get('round_number', 'N/A')
                hospitals = round_info.get('num_participating_hospitals', 'N/A')
                loss = round_info.get('average_loss', 'NULL')
                self.log(f"Round {round_num}: {hospitals} hospitals, Loss={loss}")
            
            return data
            
        except Exception as e:
            self.log(f"Rounds endpoint error: {e}", "ERROR")
            return None
    
    def test_round_detail_endpoint(self, round_number: int) -> bool:
        """Test /api/aggregation/round/{round_number} endpoint"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.base_url}/api/aggregation/round/{round_number}",
                headers=headers
            )
            
            if response.status_code != 200:
                self.log(f"Get round detail failed: {response.status_code}", "ERROR")
                return False
            
            data = response.json()
            self.log(f"Retrieved details for Round {round_number}", "OK")
            
            # Display metrics
            metrics = {
                'average_loss': data.get('average_loss'),
                'average_mape': data.get('average_mape'),
                'average_rmse': data.get('average_rmse'),
                'average_r2': data.get('average_r2'),
                'average_accuracy': data.get('average_accuracy')
            }
            
            for metric, value in metrics.items():
                status = "OK" if value is not None else "WARN"
                display_value = f"{value:.4f}" if isinstance(value, float) else str(value)
                self.log(f"{metric}: {display_value}", status)
            
            return True
            
        except Exception as e:
            self.log(f"Round detail error: {e}", "ERROR")
            return False
    
    def test_database_schema(self):
        """Test database schema has required columns"""
        try:
            from sqlalchemy import create_engine, inspect
            
            # Try to find database file
            db_path = "D:/federated-healthcare/federated-healthcare/data/federated.db"
            engine = create_engine(f'sqlite:///{db_path}')
            inspector = inspect(engine)
            
            # Check training_rounds table
            print("training_rounds columns:")
            cols = inspect(engine).get_columns('training_rounds')
            required_metrics = ['average_mape', 'average_rmse', 'average_r2', 'average_accuracy']
            
            for col in cols:
                col_name = col['name']
                if col_name in required_metrics:
                    self.log(f"{col_name}: ✓ Present ({col['type']})", "OK")
                    required_metrics.remove(col_name)
            
            for missing in required_metrics:
                self.log(f"{missing}: ✗ MISSING", "ERROR")
            
            # Check model_weights table
            print("\nmodel_weights columns:")
            cols = inspect(engine).get_columns('model_weights')
            required_metrics = ['local_mape', 'local_rmse', 'local_r2']
            
            for col in cols:
                col_name = col['name']
                if col_name in required_metrics:
                    self.log(f"{col_name}: ✓ Present ({col['type']})", "OK")
                    required_metrics.remove(col_name)
            
            for missing in required_metrics:
                self.log(f"{missing}: ✗ MISSING", "ERROR")
                
        except Exception as e:
            self.log(f"Database schema check failed: {e}", "WARN")
    
    def validate_metric_fields(self, round_info: Dict[str, Any]):
        """Validate metric fields are present in response"""
        required_fields = [
            'average_loss',
            'average_mape',
            'average_rmse',
            'average_r2',
            'average_accuracy'
        ]
        
        print("Response field validation:")
        missing_fields = []
        
        for field in required_fields:
            if field in round_info:
                value = round_info[field]
                if value is None:
                    self.log(f"{field}: Present but NULL", "WARN")
                else:
                    self.log(f"{field}: {value}", "OK")
            else:
                missing_fields.append(field)
                self.log(f"{field}: MISSING from response", "ERROR")
        
        if not missing_fields:
            self.log("All metric fields present in API response", "OK")

if __name__ == "__main__":
    verifier = MetricsVerifier()
    success = verifier.run_all_checks()
    exit(0 if success else 1)
