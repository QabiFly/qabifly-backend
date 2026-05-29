import random
from django.db import transaction


# Indian Railway Station Codes — Real codes
# Format: @{STATION_CODE}{5-digit-number}
STATION_CODES = {
    # Uttar Pradesh
    "ROI": "Reoti",
    "BUI": "Ballia",
    "BSB": "Varanasi",
    "LKO": "Lucknow",
    "CNB": "Kanpur",
    "ALD": "Prayagraj",
    "AGC": "Agra",
    "MFP": "Muzaffarpur",
    "GKP": "Gorakhpur",
    "FD":  "Faizabad",
    "GD":  "Gonda",
    "BE":  "Bareilly",
    "SV":  "Sultanpur",
    "JNU": "Jaunpur",
    "MZP": "Mirzapur",
    "BTT": "Bhatni",
    "CPR": "Chhapra",
    "SEV": "Siwan",
    # Bihar
    "PNBE": "Patna",
    "GAYA": "Gaya",
    "MFP":  "Muzaffarpur",
    "BGP":  "Bhagalpur",
    # Maharashtra
    "CSTM": "Mumbai CST",
    "PUNE": "Pune",
    "NGP":  "Nagpur",
    # Delhi
    "NDLS": "New Delhi",
    "DLI":  "Old Delhi",
    # Other Major
    "MAS":  "Chennai",
    "SBC":  "Bengaluru",
    "HWH":  "Kolkata",
    "AMD":  "Ahmedabad",
    "JP":   "Jaipur",
}


def generate_virtual_number(station_code: str) -> str:
    """
    Generate unique virtual number.
    Format: @{STATION_CODE}{5-digit-number}
    Example: @ROI00786
    """
    from apps.users.models import User

    code = station_code.upper()

    # 5 digit random number generate karo — unique check ke saath
    max_attempts = 100
    for _ in range(max_attempts):
        number    = random.randint(10000, 99999)
        virtual_n = f"@{code}{number}"

        # Uniqueness check
        if not User.objects.filter(virtual_number=virtual_n).exists():
            return virtual_n

    raise ValueError(f"Could not generate unique number for {code}")


def get_station_code_for_village(village: str, district: str) -> str:
    """
    Village/district ke liye nearest station code dhundo.
    Fallback: district name se match karo.
    """
    # Direct match try karo
    district_upper = district.upper()
    village_upper  = village.upper()

    for code, location in STATION_CODES.items():
        if (location.upper() in district_upper or
                district_upper in location.upper() or
                location.upper() in village_upper):
            return code

    # Default — BUI (Ballia) for Reoti area
    return "BUI"


def get_all_station_codes() -> list:
    """Frontend ke liye sab station codes return karo."""
    return [
        {"code": code, "location": location}
        for code, location in STATION_CODES.items()
    ]