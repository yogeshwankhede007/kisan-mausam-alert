"""
Scheduler – runs run_daily_alerts() every day at ALERT_HOUR:ALERT_MINUTE IST.
Can also be triggered immediately via CLI flag.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime

import pytz
import schedule

from config.settings import ALERT_HOUR, ALERT_MINUTE, TIMEZONE
from src.alert_pipeline import run_daily_alerts

logger = logging.getLogger(__name__)

_tz = pytz.timezone(TIMEZONE)


def _job(dry_run: bool = False) -> None:
    now_ist = datetime.now(_tz).strftime("%Y-%m-%d %H:%M IST")
    logger.info("=== Daily weather alert job started at %s ===", now_ist)
    try:
        stats = run_daily_alerts(dry_run=dry_run)
        logger.info("Job finished. Stats: %s", stats)
    except Exception as exc:
        logger.exception("Job failed with unexpected error: %s", exc)


def start_scheduler(dry_run: bool = False) -> None:
    """
    Start the blocking scheduler loop.
    Runs the alert job every day at ALERT_HOUR:ALERT_MINUTE IST.
    """
    time_str = f"{ALERT_HOUR:02d}:{ALERT_MINUTE:02d}"
    logger.info("Scheduler started – daily job at %s %s", time_str, TIMEZONE)

    schedule.every().day.at(time_str).do(_job, dry_run=dry_run)

    while True:
        schedule.run_pending()
        time.sleep(30)  # check every 30 seconds


def run_now(dry_run: bool = False) -> None:
    """Trigger the alert job immediately (no scheduling loop)."""
    _job(dry_run=dry_run)
