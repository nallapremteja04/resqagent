import math
import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from backend.models.responder import Responder

# Reference station coordinates for known responder bases
RESPONDER_COORDS = {
    "Sector 3 Rapid Post": (17.3895, 78.4890),
    "Central Hospital Base": (17.3940, 78.4960),
    "Downtown Clinic": (17.3815, 78.4825),
    "Station 7 Firehouse": (17.4080, 78.4710),
    "West Precinct Patrol": (17.3680, 78.4420)
}
CITY_CENTER_LAT = 17.3850
CITY_CENTER_LON = 78.4867

def parse_gps_coordinates(loc_str: Optional[str]) -> Optional[Tuple[float, float]]:
    """Extract latitude and longitude from location strings like '17.38504, 78.48667 (GPS Live)'."""
    if not loc_str:
        return None
    match = re.search(r"(-?\d{1,3}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)", str(loc_str))
    if match:
        try:
            lat = float(match.group(1))
            lon = float(match.group(2))
            if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                return (lat, lon)
        except ValueError:
            return None
    return None

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth in km."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


class ResponderSelectionAgent:
    """
    Responder Selection Agent
    Evaluates available field responders, ignores busy/offline/excluded units,
    scores suitability based on proximity (dynamically using GPS coordinates or preset distance)
    and role specialization, returning the highest-ranking candidate with reasoning.
    """

    @classmethod
    def select_best_responder(
        cls,
        db: Session,
        emergency_type: str,
        priority: str,
        exclude_responder_ids: List[int] = None,
        location: Optional[str] = None
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

        # 2. Check for incident GPS coordinates
        gps_coords = parse_gps_coordinates(location)

        # 3. Score candidates based on distance and specialization match
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

            if gps_coords:
                inc_lat, inc_lon = gps_coords
                resp_lat, resp_lon = RESPONDER_COORDS.get(
                    r.current_location,
                    (CITY_CENTER_LAT + (r.distance * 0.006), CITY_CENTER_LON + (r.distance * 0.006))
                )
                effective_distance = max(haversine_distance_km(inc_lat, inc_lon, resp_lat, resp_lon), 0.1)
            else:
                effective_distance = max(r.distance, 0.1)

            # Lower distance = higher score
            score = round((10.0 / effective_distance) * spec_bonus, 2)
            scored_candidates.append({
                "responder": r,
                "score": score,
                "distance": effective_distance,
                "specialization": r.specialization,
                "role": r.role
            })

        # Rank descending by score
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        winner = scored_candidates[0]["responder"]
        winner_dist = scored_candidates[0]["distance"]

        if gps_coords:
            summary_reason = (
                f"Selected {winner.name} ({winner.role}) - closest available unit at "
                f"{winner_dist} km (computed from GPS [{gps_coords[0]:.4f}, {gps_coords[1]:.4f}]) "
                f"with matching specialization '{winner.specialization}'."
            )
        else:
            summary_reason = (
                f"Selected {winner.name} ({winner.role}) - closest available unit at "
                f"{winner_dist} km with matching specialization '{winner.specialization}'."
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
