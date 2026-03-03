import requests
import time
from typing import List, Dict, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GOOGLE_PLACES_API_KEY


PLACES_BASE = "https://maps.googleapis.com/maps/api/place"


def search_businesses(
    query: str,
    location: str,
    radius_meters: int = 50000,
    max_results: int = 60
) -> List[Dict]:
    """
    Search Google Maps using Text Search + Nearby Search for maximum coverage.
    Text Search works without Geocoding API. Nearby Search uses it if available.
    """
    if not GOOGLE_PLACES_API_KEY:
        print("[Google Maps] No API key configured — skipping.")
        return []

    # Geocoding is optional — Text Search works without it
    coords = _geocode(location)
    if not coords:
        print("[Google Maps] Geocoding API not enabled — running Text Search only (still works great)")

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
    next_page_token = None

    while len(results) < max_results:
        if next_page_token:
            params = {"pagetoken": next_page_token, "key": GOOGLE_PLACES_API_KEY}
            time.sleep(2)
        else:
            params = {
                "query": f"{query} in {location}",
                "key": GOOGLE_PLACES_API_KEY,
            }
            # Add location bias only when coords are available
            if coords:
                params["location"] = f"{coords['lat']},{coords['lng']}"
                params["radius"] = 50000

        resp = requests.get(f"{PLACES_BASE}/textsearch/json", params=params, timeout=10)
        if resp.status_code != 200 or not resp.text.strip():
            print(f"[Google Text Search] HTTP {resp.status_code} — Places API may not be enabled. Enable it at: console.cloud.google.com/apis/library/places-backend.googleapis.com")
            break
        data = resp.json()

        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            print(f"[Google Text Search] Error: {data.get('status')} — {data.get('error_message', '')}")
            break

        for place in data.get("results", []):
            detail = _get_place_detail(place["place_id"])
            results.append(_normalize(place, detail, "google_text_search"))

        next_page_token = data.get("next_page_token")
        if not next_page_token or len(results) >= max_results:
            break

    return results[:max_results]


def _nearby_search(query: str, coords: Dict, radius_meters: int, max_results: int) -> List[Dict]:
    """
    Nearby Search finds businesses close to the coordinates — often surfaces
    different results than Text Search, especially smaller local businesses.
    """
    results = []
    next_page_token = None

    while len(results) < max_results:
        if next_page_token:
            params = {"pagetoken": next_page_token, "key": GOOGLE_PLACES_API_KEY}
            time.sleep(2)
        else:
            params = {
                "keyword": query,
                "location": f"{coords['lat']},{coords['lng']}",
                "radius": radius_meters,
                "key": GOOGLE_PLACES_API_KEY,
            }

        resp = requests.get(f"{PLACES_BASE}/nearbysearch/json", params=params, timeout=10)
        if resp.status_code != 200 or not resp.text.strip():
            print(f"[Google Nearby Search] HTTP {resp.status_code} — skipping nearby search.")
            break
        data = resp.json()

        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            print(f"[Google Nearby Search] Error: {data.get('status')} — {data.get('error_message', '')}")
            break

        for place in data.get("results", []):
            detail = _get_place_detail(place["place_id"])
            results.append(_normalize(place, detail, "google_nearby_search"))

        next_page_token = data.get("next_page_token")
        if not next_page_token or len(results) >= max_results:
            break

    return results[:max_results]


def _geocode(location: str) -> Optional[Dict]:
    resp = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={"address": location, "key": GOOGLE_PLACES_API_KEY},
        timeout=10
    )
    data = resp.json()
    if data.get("results"):
        loc = data["results"][0]["geometry"]["location"]
        return {"lat": loc["lat"], "lng": loc["lng"]}
    return None


def _get_place_detail(place_id: str) -> Dict:
    fields = "name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,business_status,opening_hours,types"
    resp = requests.get(
        f"{PLACES_BASE}/details/json",
        params={"place_id": place_id, "fields": fields, "key": GOOGLE_PLACES_API_KEY},
        timeout=10
    )
    return resp.json().get("result", {})


def _normalize(place: Dict, detail: Dict, source: str = "google_maps") -> Dict:
    address_parts = detail.get("formatted_address", "").split(",")
    return {
        "source": source,
        "business_name": detail.get("name") or place.get("name", ""),
        "address": address_parts[0].strip() if address_parts else "",
        "city": address_parts[1].strip() if len(address_parts) > 1 else "",
        "state": address_parts[2].strip().split(" ")[0] if len(address_parts) > 2 else "",
        "zip_code": address_parts[2].strip().split(" ")[-1] if len(address_parts) > 2 else "",
        "phone": detail.get("formatted_phone_number", ""),
        "website": detail.get("website", ""),
        "google_rating": detail.get("rating"),
        "google_review_count": detail.get("user_ratings_total"),
        "business_status": detail.get("business_status", ""),
        "categories": detail.get("types", []),
        "raw_data": {**place, **detail},
    }
