"""
Yellow Pages scraper — free, no API key needed.
Scrapes yellowpages.com for local businesses.
Complements Google Maps by surfacing different businesses.
"""
import requests
import re
import time
from bs4 import BeautifulSoup
from typing import List, Dict
from urllib.parse import quote_plus


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def search_businesses(query: str, location: str, max_results: int = 30) -> List[Dict]:
    """
    Search Yellow Pages for businesses. No API key needed.
    """
    results = []
    page = 1

    while len(results) < max_results:
        url = (
            f"https://www.yellowpages.com/search"
            f"?search_terms={quote_plus(query)}"
            f"&geo_location_terms={quote_plus(location)}"
            f"&page={page}"
        )
        try:
            resp = requests.get(url, headers=HEADERS, timeout=12)
            if resp.status_code != 200:
                print(f"[Yellow Pages] HTTP {resp.status_code} on page {page}")
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            listings = soup.select("div.result")

            if not listings:
                break

            for listing in listings:
                biz = _parse_listing(listing)
                if biz and biz["business_name"]:
                    results.append(biz)

            # Check for next page
            next_btn = soup.select_one("a.next")
            if not next_btn or len(results) >= max_results:
                break

            page += 1
            time.sleep(1)  # Polite delay

        except Exception as e:
            print(f"[Yellow Pages] Error: {e}")
            break

    print(f"[Yellow Pages] Found {len(results)} businesses")
    return results[:max_results]


def _parse_listing(listing) -> Dict:
    try:
        name_el = listing.select_one("a.business-name span") or listing.select_one(".business-name")
        name = name_el.get_text(strip=True) if name_el else ""

        phone_el = listing.select_one(".phones.phone.primary")
        phone = phone_el.get_text(strip=True) if phone_el else ""

        address_el = listing.select_one(".street-address")
        city_el = listing.select_one(".locality")
        address = address_el.get_text(strip=True) if address_el else ""
        locality = city_el.get_text(strip=True) if city_el else ""

        # Parse "City, ST  ZIP"
        city, state, zip_code = "", "", ""
        if locality:
            parts = locality.split(",")
            city = parts[0].strip() if parts else ""
            if len(parts) > 1:
                state_zip = parts[1].strip().split()
                state = state_zip[0] if state_zip else ""
                zip_code = state_zip[1] if len(state_zip) > 1 else ""

        website_el = listing.select_one("a.track-visit-website")
        website = website_el.get("href", "") if website_el else ""

        category_els = listing.select(".categories a")
        categories = [c.get_text(strip=True) for c in category_els]

        rating_el = listing.select_one(".ratings .count")
        review_count = None
        if rating_el:
            match = re.search(r"\d+", rating_el.get_text())
            review_count = int(match.group()) if match else None

        return {
            "source": "yellow_pages",
            "business_name": name,
            "address": address,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "phone": phone,
            "website": website,
            "categories": categories,
            "yp_review_count": review_count,
            "raw_data": {},
        }
    except Exception:
        return {}
