"""
Audit logging service (Phase 20)
Comprehensive security event logging
"""
import os
import json
from datetime import datetime
from typing import Dict, Optional
from enum import Enum


class AuditEventType(str, Enum):
    """Audit event types"""
    LOGIN = 'login'
    LOGOUT = 'logout'
    REGISTER = 'register'
    DATASET_UPLOAD = 'dataset_upload'
    TRAINING_START = 'training_start'
    TRAINING_COMPLETE = 'training_complete'
    WEIGHT_UPLOAD = 'weight_upload'
    AGGREGATION = 'aggregation'
    MODEL_DOWNLOAD = 'model_download'
    KEY_ROTATION = 'key_rotation'
    PERMISSION_CHANGE = 'permission_change'
    SECURITY_VIOLATION = 'security_violation'


class AuditService:
    """Service for audit logging"""
    
    AUDIT_LOG_PATH = "/app/storage/audit/audit.log"
    
    @staticmethod
    def log_event(
        event_type: AuditEventType,
        user_id: Optional[str],
        hospital_id: Optional[str],
        details: Dict,
        ip_address: Optional[str] = None,
        success: bool = True
    ):
        """
        Log audit event
        
        Args:
            event_type: Type of event
            user_id: User identifier
            hospital_id: Hospital identifier
            details: Event details dictionary
            ip_address: Client IP address
            success: Whether event was successful
        """
        # Create audit record
        audit_record = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type.value,
            'user_id': user_id,
            'hospital_id': hospital_id,
            'ip_address': ip_address,
            'success': success,
            'details': details
        }
        
        # Ensure audit directory exists
        os.makedirs(os.path.dirname(AuditService.AUDIT_LOG_PATH), exist_ok=True)
        
        # Write to audit log
        with open(AuditService.AUDIT_LOG_PATH, 'a') as f:
            f.write(json.dumps(audit_record) + '\n')
        
        # Also write to daily log for rotation
        daily_log_path = AuditService.AUDIT_LOG_PATH.replace(
            '.log',
            f"_{datetime.now().strftime('%Y%m%d')}.log"
        )
        
        with open(daily_log_path, 'a') as f:
            f.write(json.dumps(audit_record) + '\n')
    
    @staticmethod
    def read_audit_logs(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[AuditEventType] = None,
        hospital_id: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """
        Read audit logs with filters
        
        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            event_type: Filter by event type
            hospital_id: Filter by hospital
            limit: Maximum records to return
        
        Returns:
            List of audit records
        """
        if not os.path.exists(AuditService.AUDIT_LOG_PATH):
            return []
        
        records = []
        
        with open(AuditService.AUDIT_LOG_PATH, 'r') as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    
                    # Apply filters
                    if start_date:
                        record_date = datetime.fromisoformat(record['timestamp'])
                        if record_date < start_date:
                            continue
                    
                    if end_date:
                        record_date = datetime.fromisoformat(record['timestamp'])
                        if record_date > end_date:
                            continue
                    
                    if event_type and record['event_type'] != event_type.value:
                        continue
                    
                    if hospital_id and record['hospital_id'] != hospital_id:
                        continue
                    
                    records.append(record)
                    
                    if len(records) >= limit:
                        break
                        
                except json.JSONDecodeError:
                    continue
        
        return records
