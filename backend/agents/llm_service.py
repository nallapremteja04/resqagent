import os
import json
import re
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

AI_API_KEY = os.getenv("AI_API_KEY", "")

def call_llm(prompt: str, system_instruction: str = "", temperature: float = 0.2) -> str:
    """
    Calls Gemini API if AI_API_KEY is configured and valid;
    otherwise returns None to trigger deterministic fallback.
    """
    if not AI_API_KEY or AI_API_KEY in ["your_api_key_here", "test_key", ""]:
        return None

    try:
        import urllib.request
        # Direct REST API call to Google Gemini to avoid heavy SDK dependencies
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={AI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": f"{system_instruction}\n\n{prompt}"}]
            }],
            "generationConfig": {
                "temperature": temperature,
                "response_mime_type": "application/json"
            }
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=8) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            candidate = res_json.get("candidates", [{}])[0]
            text = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
            return text
    except Exception as e:
        print(f"[LLM Service Warning] API call failed ({e}). Utilizing deterministic cognitive engine fallback.")
        return None

def clean_json_response(raw_text: str) -> Optional[Dict[str, Any]]:
    """Extracts JSON object from text."""
    if not raw_text:
        return None
    try:
        # Check for code blocks
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
        if match:
            return json.loads(match.group(1))
        return json.loads(raw_text.strip())
    except Exception:
        return None
