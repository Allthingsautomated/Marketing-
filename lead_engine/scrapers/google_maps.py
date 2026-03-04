"""
Google Maps scraper using the Places API (New) — v1 endpoint.
More powerful, future-proof, and gives cleaner data than the legacy API.

To enable: console.developers.google.com/apis/api/places.googleapis.com/overview
"""
import requests
import time
from typing import List, Dict, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GOOGLE_PLACES_API_KEY


NEW_PLACES_BASE = "https://places.googleapis.com/v1/places"
GEOCODE_BASE = "https://maps.googleapis.com/maps/api/geocode/json"

# Fields to request from the new API
TEXT_SEARCH_FIELDS = ",".join([
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

NEARBY_SEARCH_FIELDS = TEXT_SEARCH_FIELDS  # same fields


def search_businesses(
    query: str,
    location: str,
    radius_meters: int = 50000,
    max_results: int = 60
) -> List[Dict]:
    """
    Search Google Maps using the new Places API (v1).
    Runs Text Search + Nearby Search for maximum coverage.
    Geocoding is optional — Text Search works without it.
    """
    if not GOOGLE_PLACES_API_KEY:
        print("[Google Maps] No API key configured — skipping.")
        return []

    coords = _geocode(location)
    if not coords:
        print("[Google Maps] Geocoding unavailable — running Text Search only")

    text_results = _text_search(query, location, coords, max_results if not coords else max_results // 2)

    nearby_results = []
    if coords:
        nearby_results = _nearby_search(query, coords, radius_meters, max_results // 2)

    combined = {r["business_name"]: r for r in text_results}
    for r in nearby_results:
        if r["business_name"] not in combined:
            combined[r["business_name"]] = r

    results = list(combined.values())[:max_results]
    print(f"[Google Maps] Text: {len(text_results)}, Nearby: {len(nearby_results)}, Unique total: {len(results)}")
    return results


def _text_search(query: str, location: str, coords: Optional[Dict], max_results: int) -> List[Dict]:
    results = []
    page_token = None
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": TEXT_SEARCH_FIELDS + ",nextPageToken",
    }

    while len(results) < max_results:
        body = {
            "textQuery": f"{query} in {location}",
            "maxResultCount": min(20, max_results - len(results)),
        }
        if coords:
            body["locationBias"] = {
                "circle": {
                    "center": {"latitude": coords["lat"], "longitude": coords["lng"]},
                    "radius": 50000.0,
                }
            }
        if page_token:
            body["pageToken"] = page_token
            time.sleep(2)

        resp = requests.post(f"{NEW_PLACES_BASE}:searchText", json=body, headers=headers, timeout=10)

        if resp.status_code != 200:
            data = resp.json() if resp.text.strip() else {}
            err = data.get("error", {})
            print(f"[Google Text Search] Error {resp.status_code}: {err.get('message', resp.text[:200])}")
            if err.get("status") == "PERMISSION_DENIED":
                print("  → Enable 'Places API (New)' at: console.cloud.google.com/apis/library/places.googleapis.com")
            break

        data = resp.json()
        for place in data.get("places", []):
            results.append(_normalize_new(place, "google_text_search"))

        page_token = data.get("nextPageToken")
        if not page_token or len(results) >= max_results:
            break

    return results[:max_results]


def _nearby_search(query: str, coords: Dict, radius_meters: int, max_results: int) -> List[Dict]:
    results = []
    page_token = None
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": NEARBY_SEARCH_FIELDS + ",nextPageToken",
    }

    while len(results) < max_results:
        body = {
            "textQuery": query,
            "maxResultCount": min(20, max_results - len(results)),
            "locationBias": {
                "circle": {
                    "center": {"latitude": coords["lat"], "longitude": coords["lng"]},
                    "radius": float(radius_meters),
                }
            }
        }
        if page_token:
            body["pageToken"] = page_token
            time.sleep(2)

        resp = requests.post(f"{NEW_PLACES_BASE}:searchText", json=body, headers=headers, timeout=10)

        if resp.status_code != 200:
            data = resp.json() if resp.text.strip() else {}
            print(f"[Google Nearby Search] Error {resp.status_code}: {data.get('error', {}).get('message', '')}")
            break

        data = resp.json()
        for place in data.get("places", []):
            results.append(_normalize_new(place, "google_nearby_search"))

        page_token = data.get("nextPageToken")
        if not page_token or len(results) >= max_results:
            break

    return results[:max_results]


def _geocode(location: str) -> Optional[Dict]:
    try:
        resp = requests.get(
            GEOCODE_BASE,
            params={"address": location, "key": GOOGLE_PLACES_API_KEY},
            timeout=10
        )
        data = resp.json()
        if data.get("status") == "OK" and data.get("results"):
            loc = data["results"][0]["geometry"]["location"]
            return {"lat": loc["lat"], "lng": loc["lng"]}
    except Exception:
        pass
    return None


def _normalize_new(place: Dict, source: str) -> Dict:
    """Normalize new Places API v1 response to our standard format."""
    address = place.get("formattedAddress", "")
    parts = [p.strip() for p in address.split(",")]

    # Parse "123 Main St, Miami, FL 33101, USA"
    street = parts[0] if parts else ""
    city = parts[1] if len(parts) > 1 else ""
    state_zip = parts[2].strip() if len(parts) > 2 else ""
    state = state_zip.split(" ")[0] if state_zip else ""
    zip_code = state_zip.split(" ")[1] if len(state_zip.split(" ")) > 1 else ""

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
