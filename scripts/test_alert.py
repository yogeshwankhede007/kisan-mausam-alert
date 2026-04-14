"""
End-to-end test script — no SMS/WhatsApp is sent.
Demonstrates the full pipeline for a sample farmer.

Usage:
  python scripts/test_alert.py --district pune --language hindi
  python scripts/test_alert.py --district warangal --language telugu
  python scripts/test_alert.py --district bengaluru --language kannada
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import _setup_logging
from config.settings import SUPPORTED_LANGUAGES
from data.district_coords import DISTRICT_COORDS
from src.imd_fetcher import fetch_imd_cap_alerts, fetch_openmeteo_forecast
from src.weather_analyzer import analyse_and_generate_alert


def main() -> None:
    _setup_logging()

    parser = argparse.ArgumentParser(description="Test alert generation (no SMS sent)")
    parser.add_argument("--district", default="pune", help="District key")
    parser.add_argument("--language", default="hindi", choices=SUPPORTED_LANGUAGES)
    parser.add_argument("--crops", default="wheat,onion,sugarcane")
    parser.add_argument("--cattle", action="store_true", default=True)
    args = parser.parse_args()

    district = args.district.lower()
    info = DISTRICT_COORDS.get(district)
    if not info:
        print(f"District '{district}' not configured. Use main.py --list-districts.")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"District : {district.title()}, {info['state']}")
    print(f"Language : {args.language}")
    print(f"Crops    : {args.crops}")
    print(f"Cattle   : {args.cattle}")
    print(f"{'='*60}\n")

    print("1. Fetching 7-day forecast from Open-Meteo…")
    forecast = fetch_openmeteo_forecast(info["lat"], info["lon"])
    for day in forecast["days"]:
        risks_str = ", ".join(day["risks"]) if day["risks"] else "none"
        print(
            f"   {day['date']}  {day['weather_label']:<20}  "
            f"{day['temp_max_c']}°/{day['temp_min_c']}°C  "
            f"rain={day['precipitation_mm']}mm  risks={risks_str}"
        )

    print("\n2. Fetching IMD CAP alerts…")
    cap = fetch_imd_cap_alerts()
    print(f"   {len(cap)} active IMD CAP alerts")
    for a in cap[:3]:
        print(f"   - {a['title'][:80]}")

    from config.settings import LLM_MODEL, LLM_BASE_URL
    print(f"\n3. Calling LLM ({LLM_MODEL} via {LLM_BASE_URL}) for analysis & multilingual alert…")
    crops = [c.strip() for c in args.crops.split(",") if c.strip()]
    result = analyse_and_generate_alert(
        district=district,
        state=info["state"],
        forecast=forecast,
        language=args.language,
        crop_types=crops,
        has_cattle=args.cattle,
        imd_cap_alerts=cap,
    )

    print("\n── Risk Summary ──────────────────────────────────────────")
    for risk in result.get("risk_summary", []):
        print(
            f"  {risk['date']}  [{risk['severity'].upper():8s}]  "
            f"{risk['risk_type']:18s}  {risk['description_english']}"
        )

    critical = result.get("critical_days", [])
    print(f"\n── Critical Days: {critical}")

    print("\n── Alert (English) ───────────────────────────────────────")
    print(result.get("alert_english", "(none)"))

    print(f"\n── Alert ({args.language.title()}) {'─'*(40-len(args.language))}")
    print(result.get("alert_local", "(none)"))
    print()


if __name__ == "__main__":
    main()
