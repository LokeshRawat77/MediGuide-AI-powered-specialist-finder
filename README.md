# MediGuide — AI Specialist Finder

A Flask web app that suggests which type of specialist doctor to see based on described symptoms (English / Hindi / Hinglish). It does **not** diagnose.

## How it works
1. User describes symptoms (text or voice).
2. Safety layer 1: emergency keywords bypass the AI and show an emergency alert instantly.
3. Safety layer 2: Groq API returns structured JSON (specialist, urgency, reason, possible conditions, self-care, warning signs, questions for doctor) under a strict system prompt.
4. The UI shows a colour-coded result card with a disclaimer and a follow-up chat.

## Features
- 🤖 Multi-model selection (GPT OSS 120B, GPT OSS 20B, Qwen 3.8 27B)
- 🎤 Voice input (Web Speech API)
- 💬 Follow-up chat after each analysis
- 🌙 Dark / light theme
- 🕐 Session history & stats sidebar
- 🇮🇳 Hindi / Hinglish language support
- 🚨 Emergency keyword bypass (no API call)

## Run locally
```
python -m venv venv
venv\Scripts\activate        # Windows  (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env       # then add your GROQ_API_KEY
python app.py
```
Open http://127.0.0.1:5000

## Environment variables
| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Your Groq API key from https://console.groq.com |

## API routes
| Route | Method | Description |
|---|---|---|
| `/` | GET | Main UI |
| `/analyze` | POST | Symptom → specialist JSON |
| `/chat` | POST | Follow-up chat |

## Limitations
- Not medical advice.
- Emergency keyword list is not exhaustive.
- No patient data is stored.
- Voice input requires a browser that supports the Web Speech API (Chrome recommended).
