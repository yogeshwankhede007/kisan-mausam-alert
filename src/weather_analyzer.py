"""
LLM-powered weather analysis and multilingual alert generation.
Defaults to a locally running Ollama instance (100% free, no API key needed).
Can be pointed at Google Gemini free tier or any OpenAI-compatible endpoint
by changing LLM_BASE_URL / LLM_API_KEY / LLM_MODEL in your .env file.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from openai import OpenAI          # used as a generic HTTP client
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

logger = logging.getLogger(__name__)

# Client is created lazily so --test-forecast / --list-districts work without Ollama running
_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
    return _client

# ── Language name map for prompt clarity ───────────────────────────────────
_LANG_DISPLAY = {
    "english": "English",
    "hindi": "Hindi (Devanagari script)",
    "marathi": "Marathi (Devanagari script)",
    "kannada": "Kannada (Kannada script)",
    "telugu": "Telugu (Telugu script)",
    "punjabi": "Punjabi (Gurmukhi script)",
    "gujarati": "Gujarati (Gujarati script)",
    "bengali": "Bengali (Bengali script)",
    "odia": "Odia (Odia script)",
    "tamil": "Tamil (Tamil script)",
    "malayalam": "Malayalam (Malayalam script)",
}

# ── System prompt for the AI ─────────────────────────────────────────────────
_SYSTEM_PROMPT = """
You are an expert agricultural meteorologist working for the India Meteorological Department.
Your job is to analyse 7-day weather forecast data for an Indian district and generate:
  1. A structured JSON weather risk summary (internal use).
  2. A short, practical SMS alert in the farmer's local language.

Your audience is Indian farmers — they may have low literacy; keep language simple and direct.
Focus on: heavy rain, heatwaves, cold waves, thunderstorms, fog, drought, high winds.
Advice must cover: what to do with crops, irrigation management, livestock/cattle safety,
harvesting timing, pesticide spraying windows, and personal safety.
Never use technical jargon. Be warm, respectful, and specific.
"""


def _day_summary(day: Dict[str, Any]) -> str:
    """Convert one day's forecast dict to a compact text summary for the prompt."""
    return (
        f"  {day['date']} ({day['weather_label']}): "
        f"max {day['temp_max_c']}°C / min {day['temp_min_c']}°C, "
        f"rain {day['precipitation_mm']:.1f}mm ({day['precipitation_probability_pct']}%), "
        f"wind {day['wind_max_kmh']:.0f}km/h gusts {day['wind_gust_kmh']:.0f}km/h, "
        f"UV {day['uv_index_max']:.1f}"
        + (f", RISKS: {', '.join(day['risks'])}" if day['risks'] else "")
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def analyse_and_generate_alert(
    district: str,
    state: str,
    forecast: Dict[str, Any],
    language: str,
    crop_types: List[str],
    has_cattle: bool,
    imd_cap_alerts: Optional[List[Dict[str, str]]] = None,
    season_context: str = "",
) -> Dict[str, Any]:
    """
    Call OpenAI to:
      - Identify key weather risks over the 7-day window
      - Generate a farmer-friendly SMS alert in the specified language

    Returns dict with keys:
      risk_summary    – list of identified risk events
      alert_english   – English version
      alert_local     – translated version in `language`
      critical_days   – list of dates with high-risk events
    """
    days_text = "\n".join(_day_summary(d) for d in forecast["days"])
    crops_text = ", ".join(crop_types) if crop_types else "mixed crops"
    cattle_text = "Yes" if has_cattle else "No"

    cap_text = ""
    if imd_cap_alerts:
        cap_items = "\n".join(
            f"  - {a['title']}: {a['summary'][:200]}" for a in imd_cap_alerts[:5]
        )
        cap_text = f"\nOfficial IMD CAP Alerts active today:\n{cap_items}"

    season_text = f"\nCrop season context: {season_context}" if season_context else ""

    user_prompt = f"""
District: {district.title()}, {state}
Farmer crops: {crops_text}
Farmer has cattle/livestock: {cattle_text}
Alert language: {_LANG_DISPLAY.get(language, language)}{season_text}

7-Day Forecast (today onwards):
{days_text}
{cap_text}

Please respond ONLY with a valid JSON object with the following exact keys:
{{
  "risk_summary": [
    {{
      "date": "YYYY-MM-DD",
      "risk_type": "HEAVY_RAIN|HEATWAVE|COLD_WAVE|THUNDERSTORM|SNOWFALL|DROUGHT|HIGH_WIND|NONE",
      "severity": "low|moderate|high|extreme",
      "description_english": "one sentence"
    }}
  ],
  "critical_days": ["YYYY-MM-DD", ...],
  "alert_english": "Full SMS text in English (max 320 chars). Must mention specific dates, what to do with crops/livestock.",
  "alert_local": "Same SMS but in {_LANG_DISPLAY.get(language, language)} script. Max 320 chars."
}}
"""

    response = _get_client().chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        # response_format JSON mode: supported by Ollama (qwen2.5, llama3.2, gemma3)
        # and by Gemini / OpenAI-compatible endpoints
        response_format={"type": "json_object"},
    )

    raw_content = response.choices[0].message.content or ""
    # Robust JSON extraction: strip any markdown fences a model might add
    json_text = _extract_json(raw_content)
    result = json.loads(json_text)
    logger.info(
        "LLM alert generated for %s (%s) via %s – critical days: %s",
        district,
        language,
        LLM_MODEL,
        result.get("critical_days", []),
    )
    return result


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=8))
def translate_alert(text_english: str, language: str) -> str:
    """
    Standalone translation helper – translate an existing English alert to
    a target Indian language using the configured local LLM.
    """
    if language == "english":
        return text_english

    lang_display = _LANG_DISPLAY.get(language, language)
    response = _get_client().chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    f"Translate the following Indian farmer weather alert into {lang_display}. "
                    "Keep it short, clear, and under 320 characters. "
                    "Use simple everyday vocabulary. Return only the translated text."
                ),
            },
            {"role": "user", "content": text_english},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


def _extract_json(text: str) -> str:
    """Extract JSON from model output, stripping markdown fences if present."""
    # Remove ```json ... ``` or ``` ... ``` wrappers some models add
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if fence:
        return fence.group(1).strip()
    # Find first { ... } block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return text[start : end + 1]
    return text
