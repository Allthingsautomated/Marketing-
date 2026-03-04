"""
Google Places Type Search — replaces Yellow Pages.
Uses the Places API (New) with includedTypes for broader coverage,
surfacing businesses the text search misses.
"""
import requests
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GOOGLE_PLACES_API_KEY
from typing import List, Dict, Optional

NEW_PLACES_BASE = "https://places.googleapis.com/v1/places"
GEOCODE_BASE    = "https://maps.googleapis.com/maps/api/geocode/json"

FIELDS = ",".join([
    "places.displayName",
    "places.formattedAddress",
    "places.nationalPhoneNumber",
    "places.internationalPhoneNumber",
    "places.websiteUri",
    "places.rating",
    "places.userRatingCount",
    "places.businessStatus",
    "places.types",
    "places.location",
    "places.id",
])

# Maps general query keywords → Google place types
KEYWORD_TO_TYPES = {
    "restaurant": ["restaurant", "food", "cafe", "bar"],
    "salon":      ["hair_care", "beauty_salon", "spa"],
    "dentist":    ["dentist", "dental_clinic"],
    "doctor":     ["doctor", "hospital", "medical_clinic"],
    "gym":        ["gym", "fitness_center", "sports_club"],
    "plumber":    ["plumber", "home_improvement_store"],
    "electrician":["electrician"],
    "contractor": ["general_contractor", "roofing_contractor"],
    "lawyer":     ["lawyer", "legal_services"],
    "real estate":["real_estate_agency"],
    "realtor":    ["real_estate_agency"],
    "hotel":      ["lodging", "hotel"],
    "auto":       ["car_repair", "car_dealer", "auto_parts_store"],
    "car":        ["car_repair", "car_dealer", "car_wash"],
    "retail":     ["clothing_store", "shoe_store", "department_store"],
    "shop":       ["store", "shopping_mall"],
    "cafe":       ["cafe", "coffee_shop", "bakery"],
    "bar":        ["bar", "night_club"],
    "pharmacy":   ["pharmacy", "drugstore"],
    "vet":        ["veterinary_care"],
}


def search_businesses(query: str, location: str, max_results: int = 30) -> List[Dict]:
    """
    Search Google Places by business type for broader coverage.
    Falls back to a text search with 'near <location>' if no type match.
    """
    if not GOOGLE_PLACES_API_KEY:
        print("[Google Type Search] No API key — skipping.")
        return []

    coords = _geocode(location)
    if not coords:
        print("[Google Type Search] Geocoding failed — skipping type search.")
        return []

    types = _query_to_types(query)
    results = []

    if types:
        for place_type in types[:2]:  # max 2 types to stay fast
            batch = _search_by_type(place_type, coords, max_results // len(types[:2]) + 5)
            results.extend(batch)
            if len(results) >= max_results:
                break
            time.sleep(0.3)
    else:
        # Fallback: text search with different phrasing
        results = _fallback_text_search(query, location, coords, max_results)

    # Deduplicate by place id
    seen, unique = set(), []
    for r in results:
        pid = r.get("raw_data", {}).get("id", r["business_name"])
        if pid not in seen:
            seen.add(pid)
            unique.append(r)

    unique = unique[:max_results]
    print(f"[Google Type Search] Found {len(unique)} businesses")
    return unique


def _search_by_type(place_type: str, coords: Dict, max_results: int) -> List[Dict]:
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": FIELDS + ",nextPageToken",
    }
    body = {
        "includedTypes": [place_type],
        "maxResultCount": min(20, max_results),
        "locationRestriction": {
            "circle": {
                "center": {"latitude": coords["lat"], "longitude": coords["lng"]},
                "radius": 50000.0,
            }
        },
    }
    results = []
    try:
        resp = requests.post(
            f"{NEW_PLACES_BASE}:searchNearby", json=body, headers=headers, timeout=10
        )
        if resp.status_code != 200:
            err = resp.json().get("error", {}) if resp.text.strip() else {}
            print(f"[Google Type Search] Error {resp.status_code}: {err.get('message', '')}")
            return []
        for place in resp.json().get("places", []):
            results.append(_normalize(place, "google_type_search"))
    except Exception as e:
        print(f"[Google Type Search] Exception: {e}")
    return results


def _fallback_text_search(query: str, location: str, coords: Dict, max_results: int) -> List[Dict]:
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": FIELDS,
    }
    body = {
        "textQuery": f"best {query} near {location}",
        "maxResultCount": min(20, max_results),
        "locationBias": {
            "circle": {
                "center": {"latitude": coords["lat"], "longitude": coords["lng"]},
                "radius": 50000.0,
            }
        },
    }
    results = []
    try:
        resp = requests.post(
            f"{NEW_PLACES_BASE}:searchText", json=body, headers=headers, timeout=10
        )
        if resp.status_code == 200:
            for place in resp.json().get("places", []):
                results.append(_normalize(place, "google_type_search"))
    except Exception as e:
        print(f"[Google Type Search fallback] Exception: {e}")
    return results


def _geocode(location: str) -> Optional[Dict]:
    try:
        resp = requests.get(
            GEOCODE_BASE,
            params={"address": location, "key": GOOGLE_PLACES_API_KEY},
            timeout=10,
        )
        data = resp.json()
        if data.get("status") == "OK" and data.get("results"):
            loc = data["results"][0]["geometry"]["location"]
            return {"lat": loc["lat"], "lng": loc["lng"]}
    except Exception:
        pass
    return None


def _query_to_types(query: str) -> List[str]:
    q = query.lower()
    for keyword, types in KEYWORD_TO_TYPES.items():
        if keyword in q:
            return types
    return []


def _normalize(place: Dict, source: str) -> Dict:
    address = place.get("formattedAddress", "")
    parts   = [p.strip() for p in address.split(",")]
    street    = parts[0] if parts else ""
    city      = parts[1] if len(parts) > 1 else ""
    state_zip = parts[2].strip() if len(parts) > 2 else ""
    state     = state_zip.split(" ")[0] if state_zip else ""
    zip_code  = state_zip.split(" ")[1] if len(state_zip.split(" ")) > 1 else ""
    return {
        "source": source,
        "business_name": place.get("displayName", {}).get("text", ""),
        "address": street,
        "city": city,
        "state": state,
        "zip_code": zip_code,
        "phone": place.get("nationalPhoneNumber") or place.get("internationalPhoneNumber", ""),
        "website": place.get("websiteUri", ""),
        "google_rating": place.get("rating"),
        "google_review_count": place.get("userRatingCount"),
        "business_status": place.get("businessStatus", ""),
        "categories": place.get("types", []),
        "raw_data": place,
    }
