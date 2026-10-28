import json
import os
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("GROQ_API_KEY")
API_URL = "https://api.groq.com/openai/v1/chat/completions"

AVAILABLE_MODELS = {
    "openai/gpt-oss-120b": "GPT OSS 120B ⭐ Best",
    "openai/gpt-oss-20b": "GPT OSS 20B ⚡ Fast",
    "qwen/qwen3.8-27b": "Qwen 3.8 27B 🌐 Multilingual",
}

EMERGENCY_KEYWORDS = [
    "chest pain", "heart attack", "can't breathe", "cannot breathe", "not breathing",
    "difficulty breathing", "unconscious", "unresponsive", "seizure", "stroke",
    "heavy bleeding", "suicide", "overdose", "poisoning", "severe burn", "choking",
    "seene mein dard", "saans nahi", "saans lene mein", "behosh", "daura",
    "सीने में दर्द", "सांस नहीं", "बेहोश", "दौरा",
]

SYSTEM_PROMPT = """You are MediGuide, an advanced AI healthcare navigation assistant. Help users find the RIGHT TYPE of specialist doctor based on their symptoms.

STRICT RULES:
1. Analyze symptoms CAREFULLY — give SPECIFIC, TAILORED responses. Never be generic.
2. Reply in the SAME language the user wrote in (English, Hindi, or Hinglish).
3. Return ONLY valid JSON with EXACTLY these keys:
   - "specialist": most suitable specialist (e.g. "Cardiologist", "Neurologist", "Dermatologist")
   - "specialist_icon": a single relevant emoji for the specialist
   - "alternative_specialist": second option or null
   - "urgency": one of "low", "medium", "high", "emergency"
   - "reason": 2-3 sentences explaining WHY this specialist for THESE specific symptoms
   - "possible_conditions": list of 2-3 possible (NOT definitive) conditions
   - "self_care": list of 3-5 specific home-care tips (no medicine names or doses)
   - "warning_signs": list of 3-4 specific red flags to seek care immediately
   - "questions_for_doctor": list of 3 important questions to ask the doctor
   - "confidence": "high", "medium", or "low"
   - "follow_up": one clarifying question to better understand symptoms
4. Emergency symptoms → urgency = "emergency"
5. Be SPECIFIC: "Gastroenterologist" > "General Physician" for stomach issues
6. Keep language compassionate and simple."""

DISCLAIMER = "⚕️ General guidance only — NOT medical advice. Always consult a qualified doctor."


def emergency_response():
    return {
        "specialist": "Emergency Care",
        "specialist_icon": "🚨",
        "alternative_specialist": None,
        "urgency": "emergency",
        "reason": "Your symptoms may indicate a life-threatening condition. Do not wait — seek help immediately.",
        "possible_conditions": ["Requires immediate emergency evaluation"],
        "self_care": ["Call 112 or 108 immediately", "Do not drive yourself", "Stay calm and lie down", "Loosen tight clothing"],
        "warning_signs": ["Loss of consciousness", "Inability to breathe", "Chest pain radiating to arm or jaw", "Sudden confusion"],
        "questions_for_doctor": ["What is causing these symptoms?", "What treatment do I need now?", "Should I be admitted?"],
        "confidence": "high",
        "follow_up": None,
        "disclaimer": DISCLAIMER,
    }


@app.route("/")
def index():
    return render_template("index.html", models=AVAILABLE_MODELS)


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    symptoms = data.get("symptoms", "").strip()
    history = data.get("history", [])
    model = data.get("model", "openai/gpt-oss-120b")

    if model not in AVAILABLE_MODELS:
        model = "openai/gpt-oss-120b"
    if len(symptoms) < 5:
        return jsonify({"error": "Please describe your symptoms in a few words."}), 400
    if len(symptoms) > 1500:
        return jsonify({"error": "Please keep the description under 1500 characters."}), 400
    if any(k in symptoms.lower() for k in EMERGENCY_KEYWORDS):
        return jsonify(emergency_response())
    if not API_KEY:
        return jsonify({"error": "Server is missing GROQ_API_KEY."}), 500

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history[-8:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": symptoms})

    try:
        r = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={"model": model, "messages": messages, "temperature": 0.4,
                  "max_tokens": 1200, "response_format": {"type": "json_object"}},
            timeout=30,
        )
        r.raise_for_status()
        result = json.loads(r.json()["choices"][0]["message"]["content"])
    except requests.HTTPError:
        return jsonify({"error": f"API error {r.status_code}. Check your API key."}), 502
    except (KeyError, IndexError, json.JSONDecodeError):
        return jsonify({"error": "AI did not respond properly. Please try again."}), 502
    except requests.RequestException:
        return jsonify({"error": "Could not reach AI service. Check your internet."}), 502

    if result.get("urgency") not in ("low", "medium", "high", "emergency"):
        result["urgency"] = "medium"
    result["disclaimer"] = DISCLAIMER
    result["model_used"] = AVAILABLE_MODELS.get(model, model)
    return jsonify(result)


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    history = data.get("history", [])
    model = data.get("model", "openai/gpt-oss-120b")

    if not message:
        return jsonify({"error": "Empty message."}), 400
    if not API_KEY:
        return jsonify({"error": "Server is missing GROQ_API_KEY."}), 500

    messages = [{"role": "system", "content": (
        "You are MediGuide, a compassionate healthcare navigation assistant. "
        "Answer follow-up questions clearly in 2-4 sentences. Never diagnose. "
        "Always recommend consulting a doctor. Reply in the user's language."
    )}]
    for h in history[-10:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    try:
        r = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={"model": model, "messages": messages, "temperature": 0.5, "max_tokens": 300},
            timeout=20,
        )
        r.raise_for_status()
        reply = r.json()["choices"][0]["message"]["content"]
    except Exception:
        return jsonify({"error": "Could not get a response. Please try again."}), 502

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
