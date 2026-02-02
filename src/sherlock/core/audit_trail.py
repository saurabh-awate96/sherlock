import json
import uuid
from datetime import datetime

from .db import Database


class AuditTrail:
    """
    Log every decision for post-mortem analysis
    If something breaks, you can trace why
    """

    def __init__(self, output_dir, db_path="sherlock/sherlock_output/sherlock.db"):
        self.output_dir = output_dir
        self.run_id = str(uuid.uuid4())
        self.db = Database(db_path)
        self.trail = []

        # Log run start
        self.db.log_run(self.run_id, output_dir)

    def log_detection(self, contract_path, detection_result):
        # Add to memory trail
        self.trail.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'primitive_detection',
            'contract': contract_path,
            'result': {
                'primitive': detection_result.primitive,
                'confidence': detection_result.confidence,
                'evidence': detection_result.evidence
            }
        })

        # Persist to DB
        return self.db.log_detection(
            self.run_id,
            contract_path,
            detection_result.primitive,
            detection_result.confidence,
            detection_result.evidence
        )

    def update_verification(self, detection_id, verification_data):
        self.db.update_verification(detection_id, verification_data)

    def log_generation(self, primitive, template_used, success):
        self.trail.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'handler_generation',
            'primitive': primitive,
            'template': template_used,
            'success': success
        })

    def log_compilation_attempt(self, attempt_number, error=None):
        self.trail.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'compilation_attempt',
            'attempt': attempt_number,
            'error': error
        })

    def save(self):
        filename = f"{self.run_id}_trail.json"
        output_path = f"{self.output_dir}/{filename}"

        # Ensure dir exists
        import os
        os.makedirs(self.output_dir, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(self.trail, f, indent=2)

        print(f"📋 Audit trail saved: {output_path}")
        return output_path
