"""
Fetches weather data from two sources:
  1. Open-Meteo (free, reliable 7-day forecast) — primary
  2. IMD CAP RSS    (official GOI warnings)       — official alerts overlay
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import feedparser
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import IMD_CAP_RSS_URL, OPEN_METEO_FORECAST_URL

logger = logging.getLogger(__name__)


# ── Open-Meteo daily variables requested ────────────────────────────────────
_DAILY_VARS = ",".join([
    "temperature_2m_max",
    "temperature_2m_min",
    "apparent_temperature_max",
    "apparent_temperature_min",
    "precipitation_sum",
    "precipitation_probability_max",
    "rain_sum",
    "snowfall_sum",
    "weather_code",
    "windspeed_10m_max",
    "windgusts_10m_max",
    "uv_index_max",
    "sunrise",
    "sunset",
])

# WMO weather interpretation codes → human-readable label
WMO_CODE_MAP: Dict[int, str] = {
    0: "Clear Sky",
    1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy Fog",
    51: "Light Drizzle", 53: "Moderate Drizzle", 55: "Heavy Drizzle",
    61: "Light Rain", 63: "Moderate Rain", 65: "Heavy Rain",
    71: "Light Snow", 73: "Moderate Snow", 75: "Heavy Snow", 77: "Snow Grains",
    80: "Light Rain Showers", 81: "Moderate Rain Showers", 82: "Violent Rain Showers",
    85: "Snow Showers", 86: "Heavy Snow Showers",
    95: "Thunderstorm", 96: "Thunderstorm with Hail", 99: "Thunderstorm Heavy Hail",
}

HEATWAVE_THRESHOLD_C = 40.0       # max temp that triggers heatwave advisory
COLD_WAVE_THRESHOLD_C = 10.0      # min temp that triggers cold-wave advisory
HEAVY_RAIN_THRESHOLD_MM = 64.5    # mm/day – IMD "heavy rain" definition
VERY_HEAVY_RAIN_MM = 115.5        # mm/day – "very heavy rain"
EXTREME_RAIN_MM = 204.4           # mm/day – "extremely heavy rain"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_openmeteo_forecast(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch 7-day daily forecast from Open-Meteo for a given latitude/longitude.
    Returns a dict with 'daily' key containing lists indexed by day (0=today).
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": _DAILY_VARS,
        "timezone": "Asia/Kolkata",
        "forecast_days": 7,
    }
    resp = requests.get(OPEN_METEO_FORECAST_URL, params=params, timeout=15)
    resp.raise_for_status()
    raw = resp.json()

    daily = raw.get("daily", {})
    days: List[Dict[str, Any]] = []
    num_days = len(daily.get("time", []))

    for i in range(num_days):
        wmo_code = daily.get("weather_code", [None] * num_days)[i]
        precip_mm = daily.get("precipitation_sum", [0.0] * num_days)[i] or 0.0
        temp_max = daily.get("temperature_2m_max", [None] * num_days)[i]
        temp_min = daily.get("temperature_2m_min", [None] * num_days)[i]

        # Classify risk
        risks: List[str] = []
        if precip_mm >= EXTREME_RAIN_MM:
            risks.append("EXTREME_RAIN")
        elif precip_mm >= VERY_HEAVY_RAIN_MM:
            risks.append("VERY_HEAVY_RAIN")
        elif precip_mm >= HEAVY_RAIN_THRESHOLD_MM:
            risks.append("HEAVY_RAIN")

        if temp_max is not None and temp_max >= HEATWAVE_THRESHOLD_C:
            risks.append("HEATWAVE")
        if temp_min is not None and temp_min <= COLD_WAVE_THRESHOLD_C:
            risks.append("COLD_WAVE")
        if wmo_code in (95, 96, 99):
            risks.append("THUNDERSTORM")
        if wmo_code in (71, 73, 75, 77, 85, 86):
            risks.append("SNOWFALL")

        days.append({
            "date": daily["time"][i],
            "temp_max_c": temp_max,
            "temp_min_c": temp_min,
            "feels_like_max_c": daily.get("apparent_temperature_max", [None] * num_days)[i],
            "feels_like_min_c": daily.get("apparent_temperature_min", [None] * num_days)[i],
            "precipitation_mm": precip_mm,
            "precipitation_probability_pct": daily.get("precipitation_probability_max", [0] * num_days)[i] or 0,
            "rain_mm": daily.get("rain_sum", [0.0] * num_days)[i] or 0.0,
            "snowfall_cm": daily.get("snowfall_sum", [0.0] * num_days)[i] or 0.0,
            "weather_code": wmo_code,
            "weather_label": WMO_CODE_MAP.get(wmo_code, "Unknown"),
            "wind_max_kmh": daily.get("windspeed_10m_max", [0.0] * num_days)[i] or 0.0,
            "wind_gust_kmh": daily.get("windgusts_10m_max", [0.0] * num_days)[i] or 0.0,
            "uv_index_max": daily.get("uv_index_max", [0.0] * num_days)[i] or 0.0,
            "sunrise": daily.get("sunrise", [None] * num_days)[i],
            "sunset": daily.get("sunset", [None] * num_days)[i],
            "risks": risks,
        })

    return {
        "latitude": raw.get("latitude", lat),
        "longitude": raw.get("longitude", lon),
        "timezone": raw.get("timezone", "Asia/Kolkata"),
        "days": days,
        "fetched_at": datetime.utcnow().isoformat(),
    }


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_imd_cap_alerts() -> List[Dict[str, str]]:
    """
    Fetch active alerts from the IMD CAP RSS feed.
    Returns list of dicts with keys: title, link, summary, published.
    """
    try:
        feed = feedparser.parse(IMD_CAP_RSS_URL)
        alerts = []
        for entry in feed.entries:
            alerts.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", ""),
                "published": entry.get("published", ""),
            })
        logger.info("IMD CAP RSS: fetched %d alerts", len(alerts))
        return alerts
    except Exception as exc:
        logger.warning("IMD CAP RSS fetch failed: %s", exc)
        return []


def fetch_imd_city_weather(city_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch current weather for an IMD city by its ID.
    Returns dict or None on failure.
    """
    url = f"https://city.imd.gov.in/citywx/city_weather.php?id={city_id}"
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        # The endpoint returns PHP-rendered HTML; parse key values
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "lxml")
        data: Dict[str, Any] = {"city_id": city_id, "raw_html": resp.text[:2000]}
        # Try extracting temperature text patterns
        text_block = soup.get_text(separator=" ", strip=True)
        data["page_text_preview"] = text_block[:500]
        return data
    except Exception as exc:
        logger.warning("IMD city weather fetch failed (id=%s): %s", city_id, exc)
        return None
