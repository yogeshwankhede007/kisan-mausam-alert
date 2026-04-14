"""
Central configuration – loaded once at import time.
All secrets come from the .env file (never hard-coded here).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# ── LLM (provider-agnostic, defaults to local Ollama — 100% free) ────────
# Ollama   : LLM_BASE_URL=http://localhost:11434/v1  LLM_API_KEY=ollama  LLM_MODEL=qwen2.5:7b
# Gemini   : LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
#            LLM_API_KEY=<your_key>  LLM_MODEL=gemini-2.0-flash  (free tier: 15 RPM)
# OpenAI   : LLM_BASE_URL=https://api.openai.com/v1  LLM_API_KEY=sk-...  LLM_MODEL=gpt-4o-mini
LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
LLM_API_KEY: str = os.getenv("LLM_API_KEY", "ollama")   # any string works for Ollama
LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen2.5:7b")   # best free multilingual model

# ── Twilio ───────────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_SMS_FROM: str = os.getenv("TWILIO_SMS_FROM", "")            # direct number (optional if using MessagingService)
TWILIO_WHATSAPP_FROM: str = os.getenv("TWILIO_WHATSAPP_FROM", "")
TWILIO_MESSAGING_SERVICE_SID: str = os.getenv("TWILIO_MESSAGING_SERVICE_SID", "")  # preferred

# ── Email ────────────────────────────────────────────────────────────────
SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM: str = os.getenv("EMAIL_FROM", "")

# ── Scheduler ────────────────────────────────────────────────────────────
ALERT_HOUR: int = int(os.getenv("ALERT_HOUR", "11"))
ALERT_MINUTE: int = int(os.getenv("ALERT_MINUTE", "0"))
TIMEZONE: str = "Asia/Kolkata"          # IST

# ── Database ─────────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/farmers.db")

# ── IMD endpoints ────────────────────────────────────────────────────────
IMD_CAP_RSS_URL: str = "https://cap-sources.s3.amazonaws.com/in-imd-en/rss.xml"
IMD_CITY_WEATHER_URL: str = "https://city.imd.gov.in/citywx/city_weather.php"
IMD_DISTRICT_WARNING_URL: str = (
    "https://mausam.imd.gov.in/responsive/districtWiseWarningGIS.php"
)
IMD_AGROMET_BASE_URL: str = (
    "https://mausam.imd.gov.in/responsive/agromet_adv_ser_state_current.php"
)

# ── Open-Meteo (free, no API key needed) ─────────────────────────────────
OPEN_METEO_FORECAST_URL: str = "https://api.open-meteo.com/v1/forecast"
# ── data.gov.in (crop data — optional, free API key) ─────────────────────
# Register free at https://data.gov.in/user/register  then go to My Account → API Key
DATA_GOV_IN_API_KEY: str = os.getenv("DATA_GOV_IN_API_KEY", "")
# ── Supported languages ──────────────────────────────────────────────────
SUPPORTED_LANGUAGES: list[str] = [
    "english",
    "hindi",
    "marathi",
    "kannada",
    "telugu",
    "punjabi",
    "gujarati",
    "bengali",
    "odia",
    "tamil",
    "malayalam",
]

# ── Logging ──────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR: Path = Path(__file__).resolve().parents[1] / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
