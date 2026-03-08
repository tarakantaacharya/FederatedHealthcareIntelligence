"""
Secure Multi-Party Computation routes (Phase 14)
MPC-enabled secure aggregation
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.utils.auth import require_role
from app.services.mpc_service import MPCService

router = APIRouter()


@router.post("/generate-keys")
async def generate_mpc_keys(
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Generate MPC key pair for hospital
    
    Returns public and private keys for secure aggregation protocol.
    Private key should be stored securely by hospital.
    Public key is shared with central server for mask coordination.
    """
    mpc_service = MPCService(num_hospitals=1)
    
    hospital = current_user["db_object"]
    private_key, public_key = mpc_service.generate_key_pair(
        hospital.hospital_id
    )
    
    return {
        'hospital_id': hospital.hospital_id,
        'public_key': public_key.decode('utf-8'),
        'message': 'Store private key securely. Share public key with central server.'
    }


@router.get("/info")
async def get_mpc_info(
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get MPC protocol information
    
    Returns description of secure aggregation protocol:
    - Pairwise secret generation
    - Additive masking
    - Secure summation
    - Dropout tolerance
    """
    return {
        'protocol': 'Secure Multi-Party Computation (MPC)',
        'features': [
            'Pairwise key exchange between hospitals',
            'Additive secret masking of model weights',
            'Masks cancel during aggregation',
            'Server cannot see individual hospital weights',
            'Dropout-tolerant aggregation',
            'Only aggregate is revealed'
        ],
        'security_guarantee': 'Server learns only the aggregated model, not individual contributions',
        'dropout_tolerance': 'Protocol handles missing hospitals during aggregation'
    }
