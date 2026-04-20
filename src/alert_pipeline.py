"""
Core alert pipeline – orchestrates data fetching, OpenAI analysis,
and notification dispatch for all registered farmers.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional

from data.district_coords import DISTRICT_COORDS
from src.crop_fetcher import get_current_season_info, get_district_crops
from src.database import Farmer, get_active_districts, get_active_farmers, log_alert
from src.imd_fetcher import fetch_imd_cap_alerts, fetch_openmeteo_forecast
from src.notifier import dispatch_alert
from src.weather_analyzer import analyse_and_generate_alert, generate_advisory_addons, translate_alert

logger = logging.getLogger(__name__)


def run_daily_alerts(dry_run: bool = False) -> Dict[str, Any]:
    """
    Main daily job:
      1. Get active districts from the DB.
      2. Fetch 7-day forecast (Open-Meteo) + IMD CAP alerts.
      3. For each district, call OpenAI once per unique language group.
      4. Dispatch alerts to each farmer.

    dry_run=True prints messages to stdout instead of sending.
    Returns summary stats.
    """
    stats: Dict[str, Any] = {
        "districts_processed": 0,
        "farmers_notified": 0,
        "farmers_failed": 0,
        "alerts_sent": 0,
    }

    # Fetch global IMD CAP alerts once (applies to all)
    cap_alerts = fetch_imd_cap_alerts()
    logger.info("IMD CAP alerts loaded: %d items", len(cap_alerts))

    active_districts = get_active_districts()
    if not active_districts:
        logger.warning("No active farmers in database. Exiting.")
        return stats

    # Group farmers by district to minimise API calls
    district_farmers: Dict[str, List[Farmer]] = defaultdict(list)
    for d in active_districts:
        district_farmers[d] = get_active_farmers(district=d)

    for district, farmers in district_farmers.items():
        coords = DISTRICT_COORDS.get(district)
        if not coords:
            logger.warning("No coordinates for district '%s' – skipping.", district)
            continue

        # ── Fetch forecast once per district ──────────────────────────────
        try:
            forecast = fetch_openmeteo_forecast(coords["lat"], coords["lon"])
        except Exception as exc:
            logger.error("Forecast fetch failed for %s: %s", district, exc)
            continue

        state = coords["state"]
        stats["districts_processed"] += 1

        # ── Auto-detect crops for this district from data.gov.in + seasonal calendar ─
        district_crops = get_district_crops(district, state)
        season_info = get_current_season_info()
        logger.info(
            "[%s] season=%s crops=%s",
            district,
            season_info["season"],
            district_crops,
        )

        # ── Group farmers in this district by language ────────────────────
        language_groups: Dict[str, List[Farmer]] = defaultdict(list)
        for farmer in farmers:
            language_groups[farmer.language].append(farmer)

        for language, lang_farmers in language_groups.items():
            # Use the first farmer's crop list as representative for this call
            # (if crop mixes vary widely, call OpenAI per farmer — costs more)
            representative = lang_farmers[0]
            # Registered crops take priority; fall back to district-level crop detection
            registered_crops = list({c for f in lang_farmers for c in f.crops})
            all_crops = registered_crops if registered_crops else district_crops
            any_cattle = any(f.has_cattle for f in lang_farmers)

            try:
                result = analyse_and_generate_alert(
                    district=district,
                    state=state,
                    forecast=forecast,
                    language=language,
                    crop_types=all_crops,
                    has_cattle=any_cattle,
                    imd_cap_alerts=cap_alerts,
                    season_context=season_info["context"],
                )
                alert_message = result.get("alert_local") or result.get("alert_english", "")
            except Exception as exc:
                logger.error(
                    "LLM analysis failed for %s / %s: %s", district, language, exc
                )
                # Fallback: use a plain English alert if available
                try:
                    result = analyse_and_generate_alert(
                        district=district,
                        state=state,
                        forecast=forecast,
                        language="english",
                        crop_types=all_crops,
                        has_cattle=any_cattle,
                        imd_cap_alerts=cap_alerts,
                        season_context=season_info["context"],
                    )
                    alert_message = result.get("alert_english", "")
                except Exception:
                    alert_message = _build_fallback_message(district, forecast)

            if not alert_message:
                continue

            # ── Advisory addons: planting, harvest, livestock ─────────
            addon_parts: list = []
            try:
                addons = generate_advisory_addons(
                    district=district,
                    state=state,
                    forecast=forecast,
                    language=language,
                    crop_types=all_crops,
                    has_cattle=any_cattle,
                    season=season_info["season"],
                    season_context=season_info["context"],
                )
                addon_parts = [v for v in (
                    addons.get("planting_advisory"),
                    addons.get("harvest_advisory"),
                    addons.get("livestock_advisory"),
                ) if v]
            except Exception as exc:
                logger.warning("Advisory addons skipped for %s/%s: %s", district, language, exc)

            # ── Dispatch to each farmer in this language group ──────────
            for farmer in lang_farmers:
                # Personalise the message slightly if crops differ a lot
                final_msg = alert_message
                if farmer.crops and len(farmer.crops) != len(all_crops):
                    try:
                        farmer_result = analyse_and_generate_alert(
                            district=district,
                            state=state,
                            forecast=forecast,
                            language=language,
                            crop_types=farmer.crops,
                            has_cattle=farmer.has_cattle,
                            imd_cap_alerts=cap_alerts,
                        )
                        final_msg = farmer_result.get("alert_local") or final_msg
                    except Exception:
                        pass  # use group message

                if dry_run:
                    print(f"\n[DRY-RUN] To: {farmer.phone} ({farmer.name})")
                    print(f"Channel: {farmer.notification_channel}")
                    print(f"Language: {language}")
                    print(f"Message:\n{final_msg}\n")
                    if addon_parts and farmer.notification_channel == "whatsapp":
                        print(f"Advisory addons:\n" + "\n\n".join(addon_parts) + "\n")
                    stats["farmers_notified"] += 1
                    stats["alerts_sent"] += 1
                    log_alert(farmer, farmer.notification_channel, language, final_msg, "sent")
                    continue

                # Append advisory addons for WhatsApp (rich channel, no char limit)
                # SMS keeps the core 320-char alert only
                dispatch_msg = final_msg
                if addon_parts and farmer.notification_channel == "whatsapp":
                    dispatch_msg = final_msg + "\n\n" + "\n\n".join(addon_parts)

                dispatch_result = dispatch_alert(
                    to_phone=farmer.phone,
                    message=dispatch_msg,
                    channel=farmer.notification_channel,
                )

                if dispatch_result["errors"]:
                    stats["farmers_failed"] += 1
                    log_alert(
                        farmer,
                        farmer.notification_channel,
                        language,
                        dispatch_msg,
                        "failed",
                        str(dispatch_result["errors"]),
                    )
                else:
                    stats["farmers_notified"] += 1
                    stats["alerts_sent"] += 1
                    log_alert(farmer, farmer.notification_channel, language, dispatch_msg, "sent")

    logger.info("Daily alert run complete. Stats: %s", stats)
    return stats


def _build_fallback_message(district: str, forecast: Dict[str, Any]) -> str:
    """
    Minimal plain-English fallback when OpenAI is unavailable.
    Surfaces only high-risk days.
    """
    lines = [f"Weather Alert – {district.title()} (7 days):"]
    for day in forecast["days"]:
        if day["risks"]:
            lines.append(f"  {day['date']}: {', '.join(day['risks'])} "
                         f"({day['temp_max_c']}°C, rain {day['precipitation_mm']}mm)")
    if len(lines) == 1:
        lines.append("  No major weather risks in the next 7 days.")
    lines.append("Stay safe. – IMD Weather Alert")
    return "\n".join(lines)
