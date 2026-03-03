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
    Search Google Maps for businesses matching query + location.
    Returns raw business data ready for AI scoring.
    """
    if not GOOGLE_PLACES_API_KEY:
        print("[Google Maps] No API key configured — skipping.")
        return []

    # First geocode the location
    coords = _geocode(location)
    if not coords:
        print(f"[Google Maps] Could not geocode: {location}")
        return []

    results = []
    next_page_token = None

    while len(results) < max_results:
        params = {
            "query": f"{query} in {location}",
            "key": GOOGLE_PLACES_API_KEY,
            "type": "establishment",
        }
        if next_page_token:
            params = {"pagetoken": next_page_token, "key": GOOGLE_PLACES_API_KEY}
            time.sleep(2)  # Google requires delay before using next_page_token
        else:
            params["location"] = f"{coords['lat']},{coords['lng']}"
            params["radius"] = radius_meters

        resp = requests.get(f"{PLACES_BASE}/textsearch/json", params=params, timeout=10)
        data = resp.json()

        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            print(f"[Google Maps] API error: {data.get('status')} — {data.get('error_message', '')}")
            break

        for place in data.get("results", []):
            detail = _get_place_detail(place["place_id"])
            results.append(_normalize(place, detail))

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


def _normalize(place: Dict, detail: Dict) -> Dict:
    address_parts = detail.get("formatted_address", "").split(",")
    return {
        "source": "google_maps",
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
