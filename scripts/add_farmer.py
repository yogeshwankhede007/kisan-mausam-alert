"""
CLI script to register a farmer in the database.

Usage:
  python scripts/add_farmer.py \
    --name "Ramesh Kumar" \
    --phone "+919876543210" \
    --language hindi \
    --state "Maharashtra" \
    --district pune \
    --crops "wheat,onion,sugarcane" \
    --cattle \
    --channel whatsapp
"""

import argparse
import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.database import add_farmer, init_db
from config.settings import SUPPORTED_LANGUAGES
from data.district_coords import DISTRICT_COORDS


def main() -> None:
    parser = argparse.ArgumentParser(description="Add a farmer to the alert database")
    parser.add_argument("--name", required=True, help="Farmer's full name")
    parser.add_argument(
        "--phone",
        required=True,
        help="Mobile number in E.164 format, e.g. +919876543210",
    )
    parser.add_argument(
        "--language",
        required=True,
        choices=SUPPORTED_LANGUAGES,
        help="Preferred language for alerts",
    )
    parser.add_argument("--state", required=True, help="State name (e.g. Maharashtra)")
    parser.add_argument(
        "--district",
        required=True,
        help="District key (run main.py --list-districts to see options)",
    )
    parser.add_argument(
        "--crops",
        default="",
        help="Comma-separated crop types, e.g. rice,wheat,cotton",
    )
    parser.add_argument(
        "--cattle",
        action="store_true",
        default=False,
        help="Farmer has cattle / livestock",
    )
    parser.add_argument(
        "--channel",
        choices=["sms", "whatsapp", "both"],
        default="sms",
        help="Notification channel",
    )
    args = parser.parse_args()

    district = args.district.strip().lower()
    if district not in DISTRICT_COORDS:
        print(
            f"Warning: district '{district}' not in district_coords.py – "
            "forecast will be skipped for this farmer until coordinates are added."
        )

    crop_list = [c.strip() for c in args.crops.split(",") if c.strip()]

    init_db()
    try:
        farmer = add_farmer(
            name=args.name,
            phone=args.phone,
            language=args.language,
            state=args.state,
            district=district,
            crop_types=crop_list,
            has_cattle=args.cattle,
            notification_channel=args.channel,
        )
        print(f"✓ Farmer registered: id={farmer.id} name='{farmer.name}' phone={farmer.phone}")
    except ValueError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
