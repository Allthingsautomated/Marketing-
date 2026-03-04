"""
All Things Automated — Lead Generation Pipeline
Sarasota FL | Smart Home & Lighting Control
"""
import time
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from scrapers.google_maps import search_businesses as google_search
from scrapers.web_scraper import analyze_website
from database import Lead, SearchSession
from config import CATEGORIES, MARKETS


def run_search(
    query: str,
    location: str,
    category: str = "",
    sources: List[str] = None,
    max_per_source: int = 20,
    db: Session = None,
) -> List[Dict]:
    """
    Full pipeline: search Google Maps → scrape websites for contact info → save to DB.
    """
    if sources is None:
        sources = ["google_maps"]

    print(f"\n[Pipeline] '{query}' in '{location}' [{category}]")
    raw_leads = []

    if "google_maps" in sources:
        results = google_search(query, location, max_results=max_per_source)
        raw_leads.extend(results)
        print(f"[Pipeline] Google Maps: {len(results)} found")

    raw_leads = _deduplicate(raw_leads)
    print(f"[Pipeline] Unique: {len(raw_leads)}")

    # Scrape websites for email, phone, owner name
    enriched = []
    for i, lead in enumerate(raw_leads):
        url = lead.get("website", "")
        if url:
            print(f"  [{i+1}/{len(raw_leads)}] Scraping: {url}")
            web_data = analyze_website(url)
            lead.update({k: v for k, v in web_data.items() if k not in ("url",)})
            time.sleep(0.5)
        lead["category"] = category
        enriched.append(lead)

    if db:
        saved = _save_leads(enriched, db)
        session = SearchSession(
            query=query,
            location=location,
            category=category,
            leads_found=saved,
            source=",".join(sources),
        )
        db.add(session)
        db.commit()
        print(f"[Pipeline] Saved {saved} leads")

    return enriched


def run_category_search(
    category_key: str,
    market: str,
    max_per_query: int = 20,
    db: Session = None,
) -> int:
    """Run all queries for a given category in a given market."""
    cat = CATEGORIES.get(category_key)
    if not cat:
        print(f"[Pipeline] Unknown category: {category_key}")
        return 0

    total = 0
    for query in cat["queries"]:
        results = run_search(
            query=query,
            location=market,
            category=category_key,
            sources=["google_maps"],
            max_per_source=max_per_query,
            db=db,
        )
        total += len(results)
        time.sleep(1)

    return total


def _deduplicate(leads: List[Dict]) -> List[Dict]:
    seen = set()
    unique = []
    for lead in leads:
        key = (
            lead.get("business_name", "").lower().strip(),
            lead.get("city", "").lower().strip(),
        )
        if key not in seen and key[0]:
            seen.add(key)
            unique.append(lead)
    return unique


def _save_leads(leads: List[Dict], db: Session) -> int:
    count = 0
    for data in leads:
        existing = db.query(Lead).filter(
            Lead.business_name == data.get("business_name"),
            Lead.city == data.get("city"),
        ).first()

        if existing:
            # Update contact info if we got better data
            if data.get("email_found") and not existing.email:
                existing.email = data["email_found"]
            if data.get("phone_found") and not existing.phone:
                existing.phone = data["phone_found"]
            if data.get("owner_name") and not existing.owner_name:
                existing.owner_name = data["owner_name"]
            db.commit()
            continue

        lead = Lead(
            business_name=data.get("business_name", ""),
            owner_name=data.get("owner_name", ""),
            category=data.get("category", ""),
            address=data.get("address", ""),
            city=data.get("city", ""),
            state=data.get("state", ""),
            zip_code=data.get("zip_code", ""),
            phone=data.get("phone") or data.get("phone_found", ""),
            email=data.get("email_found", ""),
            website=data.get("website", ""),
            google_rating=data.get("google_rating"),
            google_review_count=data.get("google_review_count"),
            has_facebook="facebook" in data.get("social_profiles", {}),
            has_instagram="instagram" in data.get("social_profiles", {}),
            source=data.get("source", "google_maps"),
            raw_data=data.get("raw_data", {}),
            status="new",
        )
        db.add(lead)
        count += 1

    db.commit()
    return count
