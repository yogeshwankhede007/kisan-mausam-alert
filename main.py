"""
Entry point for the Weather Alert Automation system.

Usage:
  python main.py                    # Start scheduler (runs at 11 AM IST daily)
  python main.py --now              # Send alerts immediately
  python main.py --now --dry-run    # Preview without sending (no SMS/API calls)
  python main.py --test-forecast DISTRICT  # Print 7-day forecast for a district
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import colorlog

from config.settings import LOG_DIR, LOG_LEVEL
from src.database import init_db


def _setup_logging() -> None:
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)

    # File handler
    log_file = LOG_DIR / "weather_alert.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(console)
    root.addHandler(file_handler)


def main() -> None:
    _setup_logging()
    logger = logging.getLogger("main")

    parser = argparse.ArgumentParser(
        description="Indian Farmer Weather Alert System (IMD + OpenAI)"
    )
    parser.add_argument(
        "--now",
        action="store_true",
        help="Run the alert job immediately instead of waiting for the scheduled time",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print alerts to stdout without sending SMS/WhatsApp",
    )
    parser.add_argument(
        "--test-forecast",
        metavar="DISTRICT",
        help="Print Open-Meteo 7-day forecast for a district and exit",
    )
    parser.add_argument(
        "--list-districts",
        action="store_true",
        help="List all configured districts and exit",
    )
    args = parser.parse_args()

    # Initialise database tables
    logger.info("Initialising database…")
    init_db()

    if args.list_districts:
        from data.district_coords import DISTRICT_COORDS
        print("\nConfigured districts:")
        for key, info in sorted(DISTRICT_COORDS.items()):
            print(f"  {key:20s} — {info['state']}")
        sys.exit(0)

    if args.test_forecast:
        _run_test_forecast(args.test_forecast.lower())
        sys.exit(0)

    if args.now:
        logger.info("Running alert job immediately (dry_run=%s)…", args.dry_run)
        from src.scheduler import run_now
        run_now(dry_run=args.dry_run)
    else:
        from config.settings import ALERT_HOUR, ALERT_MINUTE, TIMEZONE
        logger.info(
            "Starting scheduler — alerts will fire at %02d:%02d %s every day.",
            ALERT_HOUR,
            ALERT_MINUTE,
            TIMEZONE,
        )
        from src.scheduler import start_scheduler
        start_scheduler(dry_run=args.dry_run)


def _run_test_forecast(district: str) -> None:
    """Pretty-print 7-day forecast for a district."""
    from data.district_coords import DISTRICT_COORDS
    from src.imd_fetcher import fetch_openmeteo_forecast

    info = DISTRICT_COORDS.get(district)
    if not info:
        print(f"District '{district}' not found. Use --list-districts to see options.")
        sys.exit(1)

    print(f"\nFetching forecast for {district.title()}, {info['state']}…\n")
    forecast = fetch_openmeteo_forecast(info["lat"], info["lon"])

    print(f"{'Date':<13} {'Condition':<22} {'Max°C':>6} {'Min°C':>6} "
          f"{'Rain mm':>8} {'Rain%':>6} {'Wind km/h':>10} {'Risks'}")
    print("-" * 90)
    for day in forecast["days"]:
        risks_str = ", ".join(day["risks"]) if day["risks"] else "-"
        print(
            f"{day['date']:<13} {day['weather_label']:<22} "
            f"{day['temp_max_c']:>6.1f} {day['temp_min_c']:>6.1f} "
            f"{day['precipitation_mm']:>8.1f} {day['precipitation_probability_pct']:>5}% "
            f"{day['wind_max_kmh']:>9.0f}  {risks_str}"
        )
    print()


if __name__ == "__main__":
    main()
