import json
from typing import Dict, Any
from backend.agents.llm_service import call_llm, clean_json_response

class EmergencyAnalysisAgent:
    """
    Emergency Analysis Agent
    Perceives unstructured distress text and extracts structured emergency triage parameters:
    - emergency_type (Accident, Medical, Fire, Crime, Rescue, Disaster)
    - severity (Critical, High, Medium, Low)
    - urgency (Immediate, High, Normal)
    - priority (P1-Critical, P2-High, P3-Medium, P4-Low)
    - reason (Autonomous justification)
    """

    SYSTEM_PROMPT = """
    You are the ResQAgent Emergency Analysis Agent, a senior 911/emergency triage expert.
    Analyze the incoming distress message and output ONLY valid JSON matching this exact structure:
    {
      "emergency_type": "Accident" | "Medical" | "Fire" | "Crime" | "Rescue" | "Other",
      "severity": "Critical" | "High" | "Medium" | "Low",
      "urgency": "Immediate" | "High" | "Normal",
      "priority": "P1-Critical" | "P2-High" | "P3-Medium" | "P4-Low",
      "reason": "Clear concise 1-2 sentence clinical justification"
    }
    """

    @classmethod
    def analyze(cls, description: str, declared_type: str = "", location: str = "") -> Dict[str, Any]:
        prompt = f"""
        Distress Description: "{description}"
        Declared Category: "{declared_type}"
        Reported Location: "{location}"
        
        Perform medical/hazard triage and return the structured JSON.
        """
        raw_output = call_llm(prompt, system_instruction=cls.SYSTEM_PROMPT)
        parsed = clean_json_response(raw_output) if raw_output else None
        
        if parsed and "severity" in parsed and "priority" in parsed:
            return parsed
        
        # Deterministic Cognitive Fallback Engine
        return cls._deterministic_triage(description, declared_type)

    @classmethod
    def _deterministic_triage(cls, text: str, declared_type: str) -> Dict[str, Any]:
        text_lower = text.lower()
        
        # Critical keywords
        critical_kw = ["unconscious", "not breathing", "heart attack", "cardiac", "stroke", 
                       "bleeding heavily", "severe", "fatal", "trapped", "explosion", "blaze", "critical", "dying"]
        # High keywords
        high_kw = ["accident", "collision", "crash", "fracture", "broken bone", "fire", 
                   "smoke", "robbery", "assault", "injured", "head injury", "blood", "ambulance"]
        # Medium keywords
        medium_kw = ["fever", "sprain", "chest pain", "minor cut", "theft", "dizzy", "burn"]

        # 1. Classify type
        emergency_type = declared_type if declared_type and declared_type != "Other" else "Medical"
        if any(w in text_lower for w in ["crash", "collision", "hit and run", "accident", "overturned", "car "]):
            emergency_type = "Accident"
        elif any(w in text_lower for w in ["fire", "flame", "smoke", "blaze", "burning"]):
            emergency_type = "Fire"
        elif any(w in text_lower for w in ["gun", "knife", "robbery", "assault", "burglar", "thief", "attack"]):
            emergency_type = "Crime"
        elif any(w in text_lower for w in ["drowning", "trapped", "cliff", "collapsed", "debris"]):
            emergency_type = "Rescue"

        # 2. Classify severity & priority
        if any(w in text_lower for w in critical_kw):
            severity = "Critical"
            urgency = "Immediate"
            priority = "P1-Critical"
            reason = "Critical trauma or life-threatening symptoms identified in distress call; requires immediate dispatch."
        elif any(w in text_lower for w in high_kw):
            severity = "High"
            urgency = "Immediate"
            priority = "P2-High"
            reason = "Severe incident reported with imminent physical harm or active hazard requiring rapid response."
        elif any(w in text_lower for w in medium_kw):
            severity = "Medium"
            urgency = "High"
            priority = "P3-Medium"
            reason = "Moderate emergency requiring professional attention; no immediate life-threat apparent."
        else:
            severity = "Low"
            urgency = "Normal"
            priority = "P4-Low"
            reason = "Non-urgent distress report or general inquiry; standard queue dispatch."

        return {
            "emergency_type": emergency_type,
            "severity": severity,
            "urgency": urgency,
            "priority": priority,
            "reason": reason
        }
