"""
Bulk-load farmers from a JSON file.

JSON format:
[
  {
    "name": "Ramesh Patil",
    "phone": "+919876543210",
    "language": "marathi",
    "state": "Maharashtra",
    "district": "pune",
    "crops": ["wheat", "onion"],
    "has_cattle": true,
    "channel": "whatsapp"
  },
  ...
]

Usage:
  python scripts/bulk_add_farmers.py --file farmers_list.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.database import add_farmer, init_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Bulk-add farmers from JSON file")
    parser.add_argument("--file", required=True, help="Path to JSON file")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    with open(path, encoding="utf-8") as fh:
        farmers_data = json.load(fh)

    init_db()
    added = 0
    skipped = 0

    for entry in farmers_data:
        try:
            farmer = add_farmer(
                name=entry["name"],
                phone=entry["phone"],
                language=entry.get("language", "hindi"),
                state=entry["state"],
                district=entry["district"].lower(),
                crop_types=entry.get("crops", []),
                has_cattle=entry.get("has_cattle", False),
                notification_channel=entry.get("channel", "sms"),
            )
            print(f"  ✓ Added: {farmer.name} ({farmer.phone})")
            added += 1
        except ValueError as exc:
            print(f"  ✗ Skipped ({entry.get('phone', '?')}): {exc}")
            skipped += 1
        except KeyError as exc:
            print(f"  ✗ Missing field {exc} in entry: {entry}")
            skipped += 1

    print(f"\nDone. Added: {added}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
