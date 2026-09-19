"""
Probe script to empirically determine the correct date-range parameter names
for the Massive (formerly Benzinga) news API.

For each candidate parameter set, we request an OLD date range (e.g. Jan 2024)
and check whether the returned articles' publish dates actually fall in that
range. If they do, the param names work. If we keep getting today's articles
back, the params are being ignored.
"""

import json
import requests
from benzinga_collector import BenzingaNewsCollector

collector = BenzingaNewsCollector()
BASE_URL = collector.base_url
API_KEY = collector.api_key

OLD_FROM = "2024-01-01"
OLD_TO = "2024-01-31"

# Candidate parameter name / value format combinations to try
CANDIDATES = [
    {"dateFrom": OLD_FROM, "dateTo": OLD_TO},
    {"date_from": OLD_FROM, "date_to": OLD_TO},
    {"from": OLD_FROM, "to": OLD_TO},
    {"publishedFrom": OLD_FROM, "publishedTo": OLD_TO},
    {"published_from": OLD_FROM, "published_to": OLD_TO},
    {"startDate": OLD_FROM, "endDate": OLD_TO},
    {"start_date": OLD_FROM, "end_date": OLD_TO},
    {"date": OLD_FROM},
    {"updatedSince": OLD_FROM},
    {"updated_since": OLD_FROM},
    {"publishedSince": OLD_FROM},
    {"since": OLD_FROM},
    {"createdSince": OLD_FROM},
]


def probe(extra_params):
    params = {
        "apiKey": API_KEY,
        "pageSize": 3,
        "page": 0,
        "displayOutput": "full",
        **extra_params,
    }
    try:
        r = requests.get(BASE_URL, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return f"ERROR: {e}", []

    if isinstance(data, dict) and "results" in data:
        articles = data["results"]
    elif isinstance(data, list):
        articles = data
    else:
        return f"Unexpected response shape: {type(data)}", []

    dates = [a.get("published") or a.get("created") for a in articles]
    return "OK", dates


def main():
    print("=" * 80)
    print(f"Probing {BASE_URL}")
    print(f"Requesting old range: {OLD_FROM} to {OLD_TO}")
    print("=" * 80)

    for candidate in CANDIDATES:
        status, dates = probe(candidate)
        print(f"\nParams: {candidate}")
        print(f"  Status: {status}")
        print(f"  Returned dates: {dates}")

        if status == "OK" and dates:
            # Check if any date actually falls within/near the requested range
            in_range = any(d and d.startswith("2024-01") for d in dates)
            if in_range:
                print("  ✅ LOOKS LIKE THIS WORKS! Dates match requested range.")
            else:
                print("  ❌ Dates do NOT match requested range (params likely ignored).")

    print("\n" + "=" * 80)
    print("Done. Look for any '✅ LOOKS LIKE THIS WORKS!' lines above.")
    print("If none found, the API may not support historical date filtering")
    print("at all for this endpoint/plan, or requires a different auth/param scheme.")
    print("=" * 80)


if __name__ == "__main__":
    main()
