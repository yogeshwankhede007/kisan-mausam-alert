"""
District-wise crop data fetcher.

Primary source : data.gov.in REST API (requires DATA_GOV_IN_API_KEY)
  - ODOP (One District One Product) dataset
  - District-wise crop area/production dataset

Fallback       : Built-in seasonal crop calendar (always works, no key needed)

The module returns, for a given district + today's date, the list of
crops currently in season — used to generate targeted weather advisories.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Dict, List, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import DATA_GOV_IN_API_KEY

logger = logging.getLogger(__name__)

# ── data.gov.in resource IDs ─────────────────────────────────────────────────
_ODOP_RESOURCE_ID = "33eba342-aba3-434f-8fa6-50fc3c8b1acf"   # One District One Product
_CROP_AREA_RESOURCE_ID = "66e33662-6f0b-4bd9-8771-5a33f8ff6cdd"  # Gujarat crop area (example)
_DATA_GOV_BASE = "https://api.data.gov.in/resource"

# ── Indian crop season calendar ──────────────────────────────────────────────
# Kharif : sown Jun-Jul, harvested Oct-Nov  (rice, cotton, soybean, jowar, bajra, maize, groundnut, turmeric, sugarcane)
# Rabi   : sown Nov-Dec, harvested Mar-Apr  (wheat, mustard, gram, peas, sunflower, potato, onion)
# Zaid   : sown Mar-Apr, harvested Jun-Jul  (watermelon, cucumber, moong, maize)

_SEASON_CROPS: Dict[str, List[str]] = {
    "kharif": ["rice", "cotton", "soybean", "jowar", "bajra", "maize", "groundnut",
               "turmeric", "sugarcane", "arhar", "urad", "moong", "sesame"],
    "rabi":   ["wheat", "mustard", "gram", "peas", "sunflower", "potato", "onion",
               "barley", "lentil", "coriander", "garlic"],
    "zaid":   ["watermelon", "cucumber", "moong", "maize", "bitter gourd", "pumpkin"],
}

def _current_season(today: Optional[date] = None) -> str:
    """Return the current Indian crop season name."""
    m = (today or date.today()).month
    if 6 <= m <= 10:
        return "kharif"
    elif m in (11, 12) or 1 <= m <= 4:
        return "rabi"
    else:
        return "zaid"


# ── District → primary crops map (from ODOP + common knowledge) ──────────────
# Covers ~80 major farming districts; used when API is unavailable.
_DISTRICT_PRIMARY_CROPS: Dict[str, List[str]] = {
    # Maharashtra
    "pune":        ["sugarcane", "onion", "wheat", "jowar", "grapes"],
    "nashik":      ["onion", "grapes", "tomato", "wheat"],
    "nagpur":      ["orange", "cotton", "soybean", "wheat"],
    "aurangabad":  ["cotton", "soybean", "sugarcane", "jowar"],
    "solapur":     ["sugarcane", "jowar", "cotton", "tomato"],
    "kolhapur":    ["sugarcane", "rice", "soybean", "turmeric"],
    "amravati":    ["cotton", "soybean", "jowar", "orange"],
    "latur":       ["soybean", "tur", "cotton", "jowar"],
    "satara":      ["sugarcane", "strawberry", "jowar", "potato"],
    "ahmednagar":  ["sugarcane", "onion", "wheat", "maize"],
    # Karnataka
    "bengaluru":   ["tomato", "rose", "ragi", "maize"],
    "mysuru":      ["sugarcane", "rice", "ragi", "coconut"],
    "dharwad":     ["cotton", "sunflower", "jowar", "groundnut"],
    "tumkur":      ["coconut", "mulberry", "groundnut", "ragi"],
    "hubli":       ["cotton", "sunflower", "jowar", "gram"],
    "bidar":       ["tur", "jowar", "sunflower", "gram"],
    "raichur":     ["rice", "cotton", "jowar", "sunflower"],
    "hassan":      ["coffee", "areca nut", "rice", "potato"],
    "shimoga":     ["rice", "maize", "arecanut", "sugarcane"],
    "gulbarga":    ["tur", "jowar", "sunflower", "gram"],
    # Telangana / Andhra Pradesh
    "hyderabad":   ["rice", "maize", "cotton", "vegetables"],
    "warangal":    ["cotton", "rice", "maize", "chilli"],
    "nizamabad":   ["rice", "turmeric", "maize", "cotton"],
    "karimnagar":  ["rice", "cotton", "maize", "turmeric"],
    "nalgonda":    ["rice", "cotton", "maize"],
    "vijayawada":  ["rice", "chilli", "tobacco", "cotton"],
    "guntur":      ["chilli", "cotton", "rice", "tobacco"],
    "kurnool":     ["cotton", "groundnut", "onion", "rice"],
    "anantapur":   ["groundnut", "tomato", "cotton", "banana"],
    "nellore":     ["rice", "prawn farming", "sugarcane"],
    # Uttar Pradesh
    "lucknow":     ["wheat", "rice", "sugarcane", "potato"],
    "varanasi":    ["wheat", "rice", "vegetable", "mustard"],
    "agra":        ["wheat", "mustard", "potato", "vegetables"],
    "meerut":      ["sugarcane", "wheat", "rice", "potato"],
    "allahabad":   ["wheat", "rice", "mustard", "potato"],
    "gorakhpur":   ["sugarcane", "wheat", "rice", "banana"],
    "kanpur":      ["wheat", "mustard", "potato", "rice"],
    "mathura":     ["wheat", "mustard", "brij vegetables", "potato"],
    # Punjab / Haryana
    "amritsar":    ["wheat", "rice", "potato", "vegetables"],
    "ludhiana":    ["wheat", "rice", "cotton", "potato"],
    "patiala":     ["wheat", "rice", "maize", "potato"],
    "hisar":       ["wheat", "cotton", "mustard", "sunflower"],
    "rohtak":      ["wheat", "rice", "sugarcane", "mustard"],
    "karnal":      ["wheat", "rice", "sugarcane", "potato"],
    # MP
    "indore":      ["soybean", "wheat", "onion", "garlic"],
    "bhopal":      ["soybean", "wheat", "gram", "mustard"],
    "jabalpur":    ["wheat", "gram", "rice", "soybean"],
    "vidisha":     ["soybean", "wheat", "gram", "mustard"],
    "hoshangabad": ["wheat", "soybean", "gram", "rice"],
    # Rajasthan
    "jaipur":      ["wheat", "mustard", "bajra", "vegetables"],
    "jodhpur":     ["bajra", "moth bean", "guar", "cumin"],
    "bikaner":     ["bajra", "guar", "moth bean", "mustard"],
    "ajmer":       ["wheat", "mustard", "bajra", "gram"],
    "kota":        ["mustard", "wheat", "soybean", "coriander"],
    # Gujarat
    "ahmedabad":   ["cotton", "groundnut", "wheat", "castor"],
    "surat":       ["sugarcane", "mango", "rice", "banana"],
    "vadodara":    ["cotton", "wheat", "tobacco", "rice"],
    "rajkot":      ["groundnut", "cotton", "wheat", "castor"],
    "anand":       ["tobacco", "cotton", "rice", "banana"],
    # West Bengal
    "kolkata":     ["rice", "jute", "potato", "vegetables"],
    "bardhaman":   ["rice", "wheat", "potato", "jute"],
    "murshidabad": ["rice", "jute", "mustard", "potato"],
    "midnapore":   ["rice", "potato", "vegetables", "jute"],
    # Bihar
    "patna":       ["rice", "wheat", "maize", "vegetables"],
    "muzaffarpur": ["mango", "litchi", "maize", "wheat"],
    "gaya":        ["wheat", "rice", "maize", "vegetables"],
    # Odisha
    "bhubaneswar": ["rice", "vegetables", "potato", "mustard"],
    "cuttack":     ["rice", "jute", "mustard", "vegetables"],
    "sambalpur":   ["rice", "cotton", "maize", "vegetables"],
}


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=8))
def _fetch_odop_for_district(district: str, state: str) -> Optional[List[str]]:
    """
    Query data.gov.in ODOP API for the primary product of a district.
    Returns a list of crop names or None on failure/no key.
    """
    if not DATA_GOV_IN_API_KEY:
        return None

    try:
        params = {
            "api-key": DATA_GOV_IN_API_KEY,
            "format": "json",
            "offset": 0,
            "limit": 5,
            "filters[district]": district.title(),
        }
        resp = requests.get(
            f"{_DATA_GOV_BASE}/{_ODOP_RESOURCE_ID}",
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        records = data.get("records", [])
        if not records:
            return None
        products = []
        for rec in records:
            # ODOP field names vary; try common ones
            for key in ("product_name", "Product", "product", "PRODUCT", "odop_product"):
                val = rec.get(key, "")
                if val:
                    products.append(str(val).strip().lower())
                    break
        logger.info("data.gov.in ODOP: %s → %s", district, products)
        return products or None
    except Exception as exc:
        logger.debug("ODOP API failed for %s: %s", district, exc)
        return None


def get_district_crops(
    district: str,
    state: str,
    today: Optional[date] = None,
) -> List[str]:
    """
    Return the list of crops currently in season for a district.

    Priority:
      1. data.gov.in ODOP API (if DATA_GOV_IN_API_KEY is set)
      2. Built-in district primary crops map
      3. Generic seasonal crops for current season
    """
    today = today or date.today()
    season = _current_season(today)

    # 1. Try live API
    api_crops = _fetch_odop_for_district(district, state)
    if api_crops:
        # Augment with current-season crops not already listed
        season_crops = _SEASON_CROPS.get(season, [])
        for c in season_crops:
            if c not in api_crops:
                api_crops.append(c)
        return api_crops[:8]

    # 2. Built-in district map
    known = _DISTRICT_PRIMARY_CROPS.get(district.lower())
    if known:
        # Filter to crops relevant to current season + always-relevant ones
        season_crops = set(_SEASON_CROPS.get(season, []))
        # Return district crops that are in-season first, then the rest
        in_season = [c for c in known if c in season_crops]
        off_season = [c for c in known if c not in season_crops]
        merged = in_season + off_season
        logger.info("Crop calendar: %s (%s) → %s", district, season, merged)
        return merged

    # 3. Generic seasonal fallback
    fallback = _SEASON_CROPS.get(season, [])[:6]
    logger.info("Crop calendar fallback: %s → %s", season, fallback)
    return fallback


def get_current_season_info(today: Optional[date] = None) -> Dict[str, str]:
    """Return current season name and advisory context."""
    today = today or date.today()
    season = _current_season(today)
    context = {
        "kharif": "Kharif season (Jun-Oct): sowing/growing phase for rice, cotton, soybean.",
        "rabi":   "Rabi season (Nov-Apr): key period for wheat, mustard, gram — harvest approaching.",
        "zaid":   "Zaid season (Mar-Jun): short-duration crops like moong, watermelon in fields.",
    }
    return {
        "season": season,
        "context": context.get(season, ""),
        "month": today.strftime("%B"),
    }
