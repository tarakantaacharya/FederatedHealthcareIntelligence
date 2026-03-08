"""
Blockchain service (Phase 18)
Minimal private audit chain without external dependencies
"""
import json
import os
import hashlib
from datetime import datetime
from typing import Dict, Optional, List
from app.config import get_settings
from sqlalchemy.orm import Session

from app.models.blockchain import Blockchain
from app.models.hospital import Hospital
from app.models.model_weights import ModelWeights

settings = get_settings()


class BlockchainService:
    """Service for local audit chain"""

    def __init__(self):
        backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        model_dir = settings.MODEL_DIR
        if not os.path.isabs(model_dir):
            model_dir = os.path.join(backend_root, model_dir)

        configured_chain_path = os.path.join(
            model_dir,
            "blockchain",
            "audit_chain.jsonl"
        )
        legacy_chain_path = os.path.join(
            backend_root,
            "storage",
            "models",
            "blockchain",
            "audit_chain.jsonl",
        )

        # Prefer configured path; if missing, fallback to legacy storage path.
        self.chain_path = configured_chain_path if os.path.exists(configured_chain_path) else legacy_chain_path

    def _ensure_chain_dir(self) -> None:
        os.makedirs(os.path.dirname(self.chain_path), exist_ok=True)

    def _read_chain(self) -> List[Dict]:
        if not os.path.exists(self.chain_path):
            return []

        chain = []
        with open(self.chain_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    chain.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return chain

    @staticmethod
    def _compute_block_hash(prev_block_hash: str, model_hash: str, timestamp: str) -> str:
        payload = f"{prev_block_hash}{model_hash}{timestamp}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def append_model_hash(self, round_id: int, model_hash: str) -> Optional[str]:
        if not model_hash:
            return None

        chain = self._read_chain()
        prev_block_hash = chain[-1]["block_hash"] if chain else "0" * 64
        timestamp = datetime.utcnow().isoformat() + "Z"
        block_hash = self._compute_block_hash(prev_block_hash, model_hash, timestamp)

        block = {
            "round_id": round_id,
            "model_hash": model_hash,
            "block_hash": block_hash,
            "timestamp": timestamp,
            "prev_block_hash": prev_block_hash
        }

        self._ensure_chain_dir()
        with open(self.chain_path, "a") as f:
            f.write(json.dumps(block) + "\n")

        return block_hash

    def log_audit_event(
        self,
        event_type: str,
        details: str,
        hospital_id: str,
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Log model hash to local audit chain.

        Compatible with previous interface; only records model hashes.
        """
        metadata = metadata or {}
        round_id = metadata.get("round_number")
        model_hash = metadata.get("model_hash")

        if round_id is None or not model_hash:
            return None

        return self.append_model_hash(int(round_id), model_hash)

    def get_audit_events(self, start_index: int = 0, count: int = 10) -> list:
        chain = self._read_chain()
        return chain[start_index:start_index + count]

    def get_logs(self, start_index: int = 0, count: int = 100) -> Dict:
        """Get full blockchain logs (admin view)"""
        chain = self._read_chain()
        logs = chain[start_index:start_index + count]
        return {
            "start_index": start_index,
            "count": len(logs),
            "logs": logs,
            "is_valid": self.verify_chain(chain)
        }

    def _get_db_logs(self, db: Session) -> List[Dict]:
        """Build blockchain logs from DB with hospital context."""
        chain_rows = db.query(Blockchain).order_by(Blockchain.id.asc()).all()
        if not chain_rows:
            return []

        model_hashes = list({row.model_hash for row in chain_rows if row.model_hash})
        models = []
        if model_hashes:
            models = db.query(ModelWeights).filter(ModelWeights.model_hash.in_(model_hashes)).all()

        hospitals = db.query(Hospital).all()
        hospitals_by_id = {hospital.id: hospital for hospital in hospitals}

        models_by_hash: Dict[str, ModelWeights] = {}
        for model in models:
            if model.model_hash and model.model_hash not in models_by_hash:
                models_by_hash[model.model_hash] = model

        logs: List[Dict] = []
        for row in chain_rows:
            model = models_by_hash.get(row.model_hash)
            hospital = hospitals_by_id.get(model.hospital_id) if model and model.hospital_id else None
            logs.append({
                "round_id": row.round_id,
                "model_hash": row.model_hash,
                "block_hash": row.block_hash,
                "timestamp": row.timestamp,
                "prev_block_hash": row.prev_block_hash,
                "hospital_id": hospital.hospital_id if hospital else None,
                "hospital_name": hospital.hospital_name if hospital else ("GLOBAL" if model and model.is_global else None),
            })

        return logs

    def get_logs_with_db(self, db: Session, start_index: int = 0, count: int = 100) -> Dict:
        """Get full blockchain logs preferring DB, with file fallback."""
        logs = self._get_db_logs(db)

        if not logs:
            return self.get_logs(start_index=start_index, count=count)

        sliced = logs[start_index:start_index + count]
        return {
            "start_index": start_index,
            "count": len(sliced),
            "logs": sliced,
            "is_valid": self.verify_chain(logs),
        }

    def get_hospital_chain(
        self,
        hospital_id: str,
        start_index: int = 0,
        count: int = 100,
        db: Optional[Session] = None,
    ) -> Dict:
        """Get hospital-specific blockchain events (hospital view)
        
        For now, returns all blocks since the chain structure doesn't yet 
        include hospital_id discrimination. In future, would filter by:
        - That hospital's model uploads
        - That hospital's mask submissions
        - That hospital's training events
        """
        if db is not None:
            db_logs = self._get_db_logs(db)

            hospital_obj = db.query(Hospital).filter(Hospital.hospital_id == hospital_id).first()
            hospital_models = []
            hospital_hashes = set()
            hospital_rounds = set()
            if hospital_obj:
                hospital_models = db.query(ModelWeights).filter(ModelWeights.hospital_id == hospital_obj.id).all()
                hospital_hashes = {model.model_hash for model in hospital_models if model.model_hash}
                hospital_rounds = {model.round_number for model in hospital_models if model.round_number is not None}

            # If DB chain rows exist, filter from DB-enriched logs.
            filtered_logs = [
                entry for entry in db_logs
                if entry.get("hospital_id") == hospital_id
            ]

            # Fallback for legacy data with no explicit hospital mapping:
            # include chain entries by matching this hospital's model hashes/rounds.
            if not filtered_logs:
                filtered_logs = [
                    entry for entry in db_logs
                    if (
                        entry.get("model_hash") in hospital_hashes
                        or entry.get("round_id") in hospital_rounds
                    )
                ]

            # If DB blockchain is empty, fall back to file chain and infer hospital mapping.
            if not db_logs:
                file_chain = self._read_chain()
                filtered_logs = [
                    entry for entry in file_chain
                    if (
                        entry.get("model_hash") in hospital_hashes
                        or entry.get("round_id") in hospital_rounds
                    )
                ]
                logs = filtered_logs[start_index:start_index + count]
                return {
                    "start_index": start_index,
                    "count": len(logs),
                    "logs": logs,
                    "is_valid": self.verify_chain(file_chain),
                    "hospital_id": hospital_id,
                }

            logs = filtered_logs[start_index:start_index + count]
            return {
                "start_index": start_index,
                "count": len(logs),
                "logs": logs,
                "is_valid": self.verify_chain(db_logs),
                "hospital_id": hospital_id,
            }

        chain = self._read_chain()
        logs = chain[start_index:start_index + count]
        return {
            "start_index": start_index,
            "count": len(logs),
            "logs": logs,
            "is_valid": self.verify_chain(chain),
            "hospital_id": hospital_id
        }

    def verify_chain(self, chain: Optional[List[Dict]] = None) -> bool:
        chain = chain if chain is not None else self._read_chain()

        prev_block_hash = "0" * 64
        for block in chain:
            if block.get("prev_block_hash") != prev_block_hash:
                return False
            expected = self._compute_block_hash(
                block.get("prev_block_hash", ""),
                block.get("model_hash", ""),
                block.get("timestamp", "")
            )
            if block.get("block_hash") != expected:
                return False
            prev_block_hash = block.get("block_hash")

        return True

    def check_participation_allowed(self, hospital_address: str) -> bool:
        return True

    def allow_hospital_participation(self, hospital_address: str) -> Optional[str]:
        return None

    def revoke_hospital_participation(self, hospital_address: str) -> Optional[str]:
        return None
