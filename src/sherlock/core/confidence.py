from dataclasses import dataclass
from typing import Any


@dataclass
class ConfidenceScore:
    primitive: str
    confidence: float
    evidence: dict[str, Any]
    recommendation: str

class ConfidenceScorer:
    """
    Never claim certainty when uncertain
    Show users WHY you made decisions
    """

    def __init__(self, config_loader):
        self.config = config_loader

    def score_detection(self, contract_path, detected_primitive, evidence) -> ConfidenceScore:
        # If detection failed
        if detected_primitive == "unknown" or not evidence:
            return ConfidenceScore(
                primitive="unknown",
                confidence=0.0,
                evidence={},
                recommendation="VERY LOW: Cannot reliably detect primitive, manual analysis required"
            )

        # In Phase 1, SemanticDetector already calculates a numeric score based on config weights.
        # Here we translate that generic score into specific recommendations and format the evidence.

        confidence = 0.0
        # If the detector output passed confidence, we use it.
        # But here we might want to re-verify or format it.
        # Assuming we get the raw confidence from the detector.

        # NOTE: In our architecture, SemanticDetector returns a Detection object with confidence.
        # This class might be redundant if SemanticDetector does the heavy lifting,
        # BUT the recipe asks for a specialized ConfidenceScorer to standardise recommendations.

        # We will assume 'evidence' passed here is the dict from SemanticDetector
        # We can re-evaluate or just categorize based on the score.

        # For this implementation, we will trust the SemanticDetector's math
        # but add the semantic recommendation layer.

        # We'll calculate a "display" confidence.
        # If evidence includes both storage and function matches, boost it.

        storage_hits = len(evidence.get('storage_matches', []))
        function_hits = len(evidence.get('function_matches', []))

        # Base confidence from the detector (passed in via separate arg or re-calc?)
        # Let's assume the caller passes the score they got.
        # Wait, the method signature in the recipe implies we re-calculate or create it.
        # Let's rely on the Config to get the criteria again if we were doing a full re-calc.

        # Simplified approach: Use specific logic for recommendations

        calc_confidence = 0.0
        if storage_hits > 0 and function_hits > 0:
            calc_confidence = 0.8 + (min(storage_hits + function_hits, 5) * 0.04) # Max 1.0
        elif function_hits > 0:
            calc_confidence = 0.5 + (min(function_hits, 5) * 0.05)
        else:
            calc_confidence = 0.3

        final_confidence = min(calc_confidence, 1.0)

        return ConfidenceScore(
            primitive=detected_primitive,
            confidence=final_confidence,
            evidence=evidence,
            recommendation=self._get_recommendation(final_confidence)
        )

    def _get_recommendation(self, confidence):
        if confidence >= 0.9:
            return "HIGH: Proceed with automated handler generation"
        elif confidence >= 0.7:
            return "MEDIUM: Generate handler but flag for manual review"
        elif confidence >= 0.5:
            return "LOW: Suggest most similar primitive, require manual confirmation"
        else:
            return "VERY LOW: Cannot reliably detect primitive, manual analysis required"
