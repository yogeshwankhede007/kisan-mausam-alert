"""
Major Indian agricultural district coordinates.
Format:  district_key -> {"lat": float, "lon": float, "state": str, "city_id": int|None}
city_id is the IMD city weather page ID (None if unknown).
"""

DISTRICT_COORDS: dict = {
    # ── Maharashtra ──────────────────────────────────────────────────────
    "pune": {"lat": 18.5204, "lon": 73.8567, "state": "Maharashtra", "city_id": 43063},
    "nashik": {"lat": 19.9975, "lon": 73.7898, "state": "Maharashtra", "city_id": 43016},
    "nagpur": {"lat": 21.1458, "lon": 79.0882, "state": "Maharashtra", "city_id": 42867},
    "aurangabad": {"lat": 19.8762, "lon": 75.3433, "state": "Maharashtra", "city_id": None},
    "solapur": {"lat": 17.6599, "lon": 75.9064, "state": "Maharashtra", "city_id": None},
    "kolhapur": {"lat": 16.7050, "lon": 74.2433, "state": "Maharashtra", "city_id": None},
    "amravati": {"lat": 20.9374, "lon": 77.7796, "state": "Maharashtra", "city_id": None},
    "latur": {"lat": 18.4088, "lon": 76.5604, "state": "Maharashtra", "city_id": None},
    "satara": {"lat": 17.6805, "lon": 74.0183, "state": "Maharashtra", "city_id": None},
    "ahmednagar": {"lat": 19.0948, "lon": 74.7480, "state": "Maharashtra", "city_id": None},

    # ── Karnataka ────────────────────────────────────────────────────────
    "bengaluru": {"lat": 12.9716, "lon": 77.5946, "state": "Karnataka", "city_id": 43295},
    "mysuru": {"lat": 12.2958, "lon": 76.6394, "state": "Karnataka", "city_id": None},
    "dharwad": {"lat": 15.4589, "lon": 75.0078, "state": "Karnataka", "city_id": None},
    "tumkur": {"lat": 13.3379, "lon": 77.1173, "state": "Karnataka", "city_id": None},
    "hubli": {"lat": 15.3647, "lon": 75.1240, "state": "Karnataka", "city_id": None},
    "bidar": {"lat": 17.9104, "lon": 77.5199, "state": "Karnataka", "city_id": None},
    "raichur": {"lat": 16.2120, "lon": 77.3439, "state": "Karnataka", "city_id": None},
    "hassan": {"lat": 13.0033, "lon": 76.1004, "state": "Karnataka", "city_id": None},
    "shimoga": {"lat": 13.9299, "lon": 75.5681, "state": "Karnataka", "city_id": None},
    "gulbarga": {"lat": 17.3297, "lon": 76.8343, "state": "Karnataka", "city_id": None},

    # ── Telangana / Andhra Pradesh ────────────────────────────────────────
    "hyderabad": {"lat": 17.3850, "lon": 78.4867, "state": "Telangana", "city_id": 43128},
    "warangal": {"lat": 17.9784, "lon": 79.5941, "state": "Telangana", "city_id": None},
    "nizamabad": {"lat": 18.6725, "lon": 78.0941, "state": "Telangana", "city_id": None},
    "karimnagar": {"lat": 18.4386, "lon": 79.1288, "state": "Telangana", "city_id": None},
    "nalgonda": {"lat": 17.0575, "lon": 79.2671, "state": "Telangana", "city_id": None},
    "vijayawada": {"lat": 16.5062, "lon": 80.6480, "state": "Andhra Pradesh", "city_id": None},
    "guntur": {"lat": 16.3067, "lon": 80.4365, "state": "Andhra Pradesh", "city_id": None},
    "kurnool": {"lat": 15.8281, "lon": 78.0373, "state": "Andhra Pradesh", "city_id": None},
    "anantapur": {"lat": 14.6819, "lon": 77.6006, "state": "Andhra Pradesh", "city_id": None},
    "nellore": {"lat": 14.4426, "lon": 79.9865, "state": "Andhra Pradesh", "city_id": None},

    # ── Uttar Pradesh (major farming belt) ──────────────────────────────
    "lucknow": {"lat": 26.8467, "lon": 80.9462, "state": "Uttar Pradesh", "city_id": 42420},
    "varanasi": {"lat": 25.3176, "lon": 82.9739, "state": "Uttar Pradesh", "city_id": None},
    "agra": {"lat": 27.1767, "lon": 78.0081, "state": "Uttar Pradesh", "city_id": None},
    "meerut": {"lat": 28.9845, "lon": 77.7064, "state": "Uttar Pradesh", "city_id": None},
    "allahabad": {"lat": 25.4358, "lon": 81.8463, "state": "Uttar Pradesh", "city_id": None},
    "gorakhpur": {"lat": 26.7606, "lon": 83.3732, "state": "Uttar Pradesh", "city_id": None},
    "kanpur": {"lat": 26.4499, "lon": 80.3319, "state": "Uttar Pradesh", "city_id": None},
    "mathura": {"lat": 27.4925, "lon": 77.6730, "state": "Uttar Pradesh", "city_id": None},

    # ── Punjab / Haryana ─────────────────────────────────────────────────
    "amritsar": {"lat": 31.6340, "lon": 74.8723, "state": "Punjab", "city_id": None},
    "ludhiana": {"lat": 30.9010, "lon": 75.8573, "state": "Punjab", "city_id": None},
    "patiala": {"lat": 30.3398, "lon": 76.3869, "state": "Punjab", "city_id": None},
    "hisar": {"lat": 29.1492, "lon": 75.7217, "state": "Haryana", "city_id": None},
    "rohtak": {"lat": 28.8955, "lon": 76.6066, "state": "Haryana", "city_id": None},
    "karnal": {"lat": 29.6857, "lon": 76.9905, "state": "Haryana", "city_id": None},

    # ── Madhya Pradesh ───────────────────────────────────────────────────
    "indore": {"lat": 22.7196, "lon": 75.8577, "state": "Madhya Pradesh", "city_id": None},
    "bhopal": {"lat": 23.2599, "lon": 77.4126, "state": "Madhya Pradesh", "city_id": 42809},
    "jabalpur": {"lat": 23.1815, "lon": 79.9864, "state": "Madhya Pradesh", "city_id": None},
    "vidisha": {"lat": 23.5252, "lon": 77.8085, "state": "Madhya Pradesh", "city_id": None},
    "hoshangabad": {"lat": 22.7478, "lon": 77.7246, "state": "Madhya Pradesh", "city_id": None},

    # ── Rajasthan ────────────────────────────────────────────────────────
    "jaipur": {"lat": 26.9124, "lon": 75.7873, "state": "Rajasthan", "city_id": 42369},
    "jodhpur": {"lat": 26.2389, "lon": 73.0243, "state": "Rajasthan", "city_id": None},
    "bikaner": {"lat": 28.0229, "lon": 73.3119, "state": "Rajasthan", "city_id": None},
    "ajmer": {"lat": 26.4499, "lon": 74.6399, "state": "Rajasthan", "city_id": None},
    "kota": {"lat": 25.2138, "lon": 75.8648, "state": "Rajasthan", "city_id": None},

    # ── Gujarat ──────────────────────────────────────────────────────────
    "ahmedabad": {"lat": 23.0225, "lon": 72.5714, "state": "Gujarat", "city_id": 42647},
    "surat": {"lat": 21.1702, "lon": 72.8311, "state": "Gujarat", "city_id": None},
    "vadodara": {"lat": 22.3072, "lon": 73.1812, "state": "Gujarat", "city_id": None},
    "rajkot": {"lat": 22.3039, "lon": 70.8022, "state": "Gujarat", "city_id": None},
    "anand": {"lat": 22.5645, "lon": 72.9289, "state": "Gujarat", "city_id": None},

    # ── West Bengal ──────────────────────────────────────────────────────
    "kolkata": {"lat": 22.5726, "lon": 88.3639, "state": "West Bengal", "city_id": 42807},
    "bardhaman": {"lat": 23.2324, "lon": 87.8615, "state": "West Bengal", "city_id": None},
    "murshidabad": {"lat": 24.1837, "lon": 88.2723, "state": "West Bengal", "city_id": None},
    "midnapore": {"lat": 22.4239, "lon": 87.3194, "state": "West Bengal", "city_id": None},

    # ── Bihar ────────────────────────────────────────────────────────────
    "patna": {"lat": 25.5941, "lon": 85.1376, "state": "Bihar", "city_id": None},
    "muzaffarpur": {"lat": 26.1209, "lon": 85.3647, "state": "Bihar", "city_id": None},
    "gaya": {"lat": 24.7914, "lon": 85.0002, "state": "Bihar", "city_id": None},

    # ── Odisha ───────────────────────────────────────────────────────────
    "bhubaneswar": {"lat": 20.2961, "lon": 85.8245, "state": "Odisha", "city_id": None},
    "cuttack": {"lat": 20.4625, "lon": 85.8828, "state": "Odisha", "city_id": None},
    "sambalpur": {"lat": 21.4669, "lon": 83.9756, "state": "Odisha", "city_id": None},
}
