from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.models.responder import Responder

class ResponderSelectionAgent:
    """
    Responder Selection Agent
    Evaluates available field responders, ignores busy/offline/excluded units,
    scores suitability based on proximity and role specialization,
    and returns the highest-ranking candidate with reasoning.
    """

    @classmethod
    def select_best_responder(
        cls,
        db: Session,
        emergency_type: str,
        priority: str,
        exclude_responder_ids: List[int] = None
    ) -> Dict[str, Any]:
        if exclude_responder_ids is None:
            exclude_responder_ids = []

        # 1. Query candidate pool
        candidates = (
            db.query(Responder)
            .filter(Responder.availability == "AVAILABLE")
            .filter(~Responder.id.in_(exclude_responder_ids))
            .all()
        )

        if not candidates:
            return {
                "selected_responder": None,
                "ranked_candidates": [],
                "reason": "No available responders found matching criteria. Capacity exhausted."
            }

        # 2. Score candidates based on distance and specialization match
        # Mapping emergency types to optimal responder specializations
        spec_map = {
            "Accident": ["Medical", "Rescue"],
            "Medical": ["Medical"],
            "Fire": ["Rescue", "Fire"],
            "Crime": ["Police"],
            "Rescue": ["Rescue", "Medical"]
        }
        preferred_specs = spec_map.get(emergency_type, ["Medical", "General"])

        scored_candidates = []
        for r in candidates:
            spec_bonus = 1.5 if r.specialization in preferred_specs else 1.0
            # Lower distance = higher score (e.g., Score = (10 / distance) * spec_bonus)
            score = round((10.0 / max(r.distance, 0.1)) * spec_bonus, 2)
            scored_candidates.append({
                "responder": r,
                "score": score,
                "distance": r.distance,
                "specialization": r.specialization,
                "role": r.role
            })

        # Rank descending by score
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        winner = scored_candidates[0]["responder"]

        summary_reason = (
            f"Selected {winner.name} ({winner.role}) - closest available unit at "
            f"{winner.distance} km with matching specialization '{winner.specialization}'."
        )

        return {
            "selected_responder": winner,
            "ranked_candidates": [
                {
                    "id": c["responder"].id,
                    "name": c["responder"].name,
                    "distance_km": c["distance"],
                    "specialization": c["specialization"],
                    "suitability_score": c["score"]
                }
                for c in scored_candidates
            ],
            "reason": summary_reason
        }
