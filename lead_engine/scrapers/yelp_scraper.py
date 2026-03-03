import requests
from typing import List, Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import YELP_API_KEY


YELP_BASE = "https://api.yelp.com/v3"


def search_businesses(
    term: str,
    location: str,
    limit: int = 50,
    offset: int = 0
) -> List[Dict]:
    """
    Search Yelp for businesses. Returns normalized lead data.
    """
    if not YELP_API_KEY:
        print("[Yelp] No API key configured — skipping.")
        return []

    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    results = []

    while len(results) < limit:
        batch = min(50, limit - len(results))
        params = {
            "term": term,
            "location": location,
            "limit": batch,
            "offset": offset + len(results),
        }
        resp = requests.get(f"{YELP_BASE}/businesses/search", headers=headers, params=params, timeout=10)
        if resp.status_code != 200:
            print(f"[Yelp] Error {resp.status_code}: {resp.text[:200]}")
            break

        data = resp.json()
        businesses = data.get("businesses", [])
        if not businesses:
            break

        for biz in businesses:
            detail = _get_detail(biz["id"], headers)
            results.append(_normalize(biz, detail))

    return results


def _get_detail(biz_id: str, headers: Dict) -> Dict:
    resp = requests.get(f"{YELP_BASE}/businesses/{biz_id}", headers=headers, timeout=10)
    return resp.json() if resp.status_code == 200 else {}


def _normalize(biz: Dict, detail: Dict) -> Dict:
    location = biz.get("location", {})
    return {
        "source": "yelp",
        "business_name": biz.get("name", ""),
        "address": location.get("address1", ""),
        "city": location.get("city", ""),
        "state": location.get("state", ""),
        "zip_code": location.get("zip_code", ""),
        "phone": biz.get("phone", ""),
        "website": detail.get("url", biz.get("url", "")),
        "yelp_rating": biz.get("rating"),
        "yelp_review_count": biz.get("review_count"),
        "categories": [c.get("title") for c in biz.get("categories", [])],
        "price_tier": biz.get("price", ""),
        "is_closed": biz.get("is_closed", False),
        "raw_data": {**biz, **detail},
    }
