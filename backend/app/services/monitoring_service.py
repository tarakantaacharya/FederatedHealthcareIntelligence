"""
Monitoring Service (Phase 37)
Prometheus metrics and health checks
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from typing import Dict, Optional
import time
import logging
import os

# Safe import of psutil with graceful fallback
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)

if not PSUTIL_AVAILABLE:
    logger.warning("psutil not installed. System metrics will be unavailable.")

# Define Prometheus metrics
training_requests = Counter(
    'federated_training_requests_total',
    'Total number of training requests',
    ['hospital_id', 'status']
)

training_duration = Histogram(
    'federated_training_duration_seconds',
    'Duration of training operations',
    ['hospital_id']
)

model_accuracy = Gauge(
    'federated_model_accuracy',
    'Model accuracy metric',
    ['hospital_id', 'round_number']
)

aggregation_duration = Histogram(
    'federated_aggregation_duration_seconds',
    'Duration of aggregation operations',
    ['round_number']
)

active_hospitals = Gauge(
    'federated_active_hospitals',
    'Number of active hospitals in current round'
)

dataset_size = Histogram(
    'federated_dataset_size_rows',
    'Size of uploaded datasets',
    ['hospital_id']
)

privacy_budget = Gauge(
    'federated_privacy_budget_remaining',
    'Remaining privacy budget (epsilon)',
    ['hospital_id']
)

# System metrics
cpu_usage = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
memory_usage = Gauge('system_memory_usage_percent', 'Memory usage percentage')
disk_usage = Gauge('system_disk_usage_percent', 'Disk usage percentage')


class MonitoringService:
    """Service for metrics collection and monitoring"""
    
    @staticmethod
    def record_training_request(hospital_id: int, status: str = 'success'):
        """
        Record a training request
        
        Args:
            hospital_id: Hospital ID
            status: 'success' or 'failure'
        """
        training_requests.labels(hospital_id=str(hospital_id), status=status).inc()
    
    @staticmethod
    def record_training_duration(hospital_id: int, duration: float):
        """
        Record training duration
        
        Args:
            hospital_id: Hospital ID
            duration: Duration in seconds
        """
        training_duration.labels(hospital_id=str(hospital_id)).observe(duration)
    
    @staticmethod
    def update_model_accuracy(hospital_id: int, round_number: int, accuracy: float):
        """
        Update model accuracy gauge
        
        Args:
            hospital_id: Hospital ID
            round_number: Training round number
            accuracy: Model accuracy value
        """
        model_accuracy.labels(
            hospital_id=str(hospital_id),
            round_number=str(round_number)
        ).set(accuracy)
    
    @staticmethod
    def record_aggregation_duration(round_number: int, duration: float):
        """
        Record aggregation duration
        
        Args:
            round_number: Training round number
            duration: Duration in seconds
        """
        aggregation_duration.labels(round_number=str(round_number)).observe(duration)
    
    @staticmethod
    def update_active_hospitals(count: int):
        """Update active hospitals count"""
        active_hospitals.set(count)
    
    @staticmethod
    def record_dataset_size(hospital_id: int, num_rows: int):
        """
        Record dataset size
        
        Args:
            hospital_id: Hospital ID
            num_rows: Number of rows in dataset
        """
        dataset_size.labels(hospital_id=str(hospital_id)).observe(num_rows)
    
    @staticmethod
    def update_privacy_budget(hospital_id: int, remaining_epsilon: float):
        """
        Update privacy budget gauge
        
        Args:
            hospital_id: Hospital ID
            remaining_epsilon: Remaining epsilon value
        """
        privacy_budget.labels(hospital_id=str(hospital_id)).set(remaining_epsilon)
    
    @staticmethod
    def update_system_metrics():
        """Update system resource metrics"""
        if not PSUTIL_AVAILABLE:
            logger.warning("psutil not available, skipping system metrics update")
            return
        
        try:
            cpu_usage.set(psutil.cpu_percent(interval=1))
            memory_usage.set(psutil.virtual_memory().percent)
            disk_usage.set(psutil.disk_usage('/').percent)
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
    
    @staticmethod
    def get_metrics() -> bytes:
        """
        Get Prometheus metrics in text format
        
        Returns:
            Metrics in Prometheus text format
        """
        MonitoringService.update_system_metrics()
        return generate_latest(REGISTRY)
    
    @staticmethod
    def health_check() -> Dict:
        """
        Comprehensive health check
        
        Returns:
            Health status dictionary
        """
        health = {
            'status': 'healthy',
            'timestamp': time.time(),
            'checks': {}
        }
        
        # Database check
        try:
            from app.database import SessionLocal
            db = SessionLocal()
            db.execute("SELECT 1")
            db.close()
            health['checks']['database'] = 'ok'
        except Exception as e:
            health['checks']['database'] = f'error: {str(e)}'
            health['status'] = 'unhealthy'
        
        # Storage check
        try:
            from app.config import get_settings
            settings = get_settings()
            if os.path.exists(settings.UPLOAD_DIR):
                health['checks']['storage'] = 'ok'
            else:
                health['checks']['storage'] = 'missing'
                health['status'] = 'degraded'
        except Exception as e:
            health['checks']['storage'] = f'error: {str(e)}'
        
        # System resources check
        if PSUTIL_AVAILABLE:
            try:
                cpu = psutil.cpu_percent(interval=1)
                mem = psutil.virtual_memory().percent
                
                health['checks']['cpu'] = f'{cpu}%'
                health['checks']['memory'] = f'{mem}%'
                
                if cpu > 90 or mem > 90:
                    health['status'] = 'degraded'
            except Exception as e:
                health['checks']['system'] = f'error: {str(e)}'
        else:
            health['checks']['system'] = 'psutil not available'
        
        return health
