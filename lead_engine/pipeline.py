"""
Lead Generation Pipeline
Orchestrates: scrape → analyze website → AI score → save to DB
"""
import time
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from scrapers.google_maps import search_businesses as google_search
from scrapers.yellow_pages import search_businesses as yp_search
from scrapers.web_scraper import analyze_website
from ai.scorer import batch_score_leads, get_learning_context
from database import Lead, SearchSession, get_db


def run_search(
    query: str,
    location: str,
    industry: str = "",
    sources: List[str] = None,
    max_per_source: int = 20,
    db: Session = None,
) -> List[Dict]:
    """
    Full pipeline: search → scrape websites → AI score → save to DB.
    Sources: google_maps (Text + Nearby Search), yellow_pages (free, no API).
    """
    if sources is None:
        sources = ["google_maps", "yellow_pages"]

    print(f"\n[Pipeline] Starting search: '{query}' in '{location}'")
    raw_leads = []

    # --- Step 1: Collect raw business data ---
    if "google_maps" in sources:
        print("[Pipeline] Searching Google Maps (Text + Nearby)...")
        results = google_search(query, location, max_results=max_per_source)
        raw_leads.extend(results)
        print(f"[Pipeline] Google Maps: {len(results)} businesses found")

    if "yellow_pages" in sources:
        print("[Pipeline] Searching Yellow Pages...")
        results = yp_search(query, location, max_results=max_per_source)
        raw_leads.extend(results)
        print(f"[Pipeline] Yellow Pages: {len(results)} businesses found")

    # Deduplicate by business name + city
    raw_leads = _deduplicate(raw_leads)
    print(f"[Pipeline] After dedup: {len(raw_leads)} unique businesses")

    # --- Step 2: Analyze each website ---
    print("[Pipeline] Analyzing websites...")
    enriched = []
    for i, lead in enumerate(raw_leads):
        url = lead.get("website", "")
        if url:
            print(f"  [{i+1}/{len(raw_leads)}] Analyzing: {url}")
            web_data = analyze_website(url)
            lead.update({k: v for k, v in web_data.items() if k != "url"})
            time.sleep(0.5)  # Polite delay
        lead["industry"] = industry or _guess_industry(lead.get("categories", []))
        enriched.append(lead)

    # --- Step 3: AI scoring ---
    print("[Pipeline] AI scoring all leads...")
    learning_ctx = get_learning_context(db) if db else ""
    scored_leads = batch_score_leads(enriched, learning_ctx)

    # --- Step 4: Save to database ---
    if db:
        saved_count = _save_leads(scored_leads, db)
        session = SearchSession(
            query=query,
            location=location,
            industry=industry,
            leads_found=saved_count,
            avg_score=sum(l.get("ai_score", 0) for l in scored_leads) / max(len(scored_leads), 1),
            source=",".join(sources),
        )
        db.add(session)
        db.commit()
        print(f"[Pipeline] Saved {saved_count} leads to database")

    return scored_leads


def _deduplicate(leads: List[Dict]) -> List[Dict]:
    seen = set()
    unique = []
    for lead in leads:
        key = (
            lead.get("business_name", "").lower().strip(),
            lead.get("city", "").lower().strip()
        )
        if key not in seen and key[0]:
            seen.add(key)
            unique.append(lead)
    return unique


def _save_leads(leads: List[Dict], db: Session) -> int:
    count = 0
    for data in leads:
        # Check for duplicate by name + city
        existing = db.query(Lead).filter(
            Lead.business_name == data.get("business_name"),
            Lead.city == data.get("city"),
        ).first()
        if existing:
            # Update scores if better data available
            existing.ai_score = data.get("ai_score", existing.ai_score)
            existing.opportunity_score = data.get("opportunity_score", existing.opportunity_score)
            existing.pain_points = data.get("pain_points", existing.pain_points)
            db.commit()
            continue

        lead = Lead(
            business_name=data.get("business_name", ""),
            industry=data.get("industry", ""),
            address=data.get("address", ""),
            city=data.get("city", ""),
            state=data.get("state", ""),
            zip_code=data.get("zip_code", ""),
            phone=data.get("phone") or data.get("phone_found", ""),
            email=data.get("email_found", ""),
            website=data.get("website", ""),
            google_rating=data.get("google_rating"),
            google_review_count=data.get("google_review_count"),
            yelp_rating=data.get("yelp_rating"),
            yelp_review_count=data.get("yelp_review_count"),
            has_facebook="facebook" in data.get("social_profiles", {}),
            has_instagram="instagram" in data.get("social_profiles", {}),
            has_google_ads=data.get("has_google_ads", False),
            has_meta_ads=data.get("has_meta_pixel", False),
            website_score=data.get("website_quality_score", 0),
            ai_score=data.get("ai_score", 0),
            ai_reasoning=data.get("reasoning", ""),
            pain_points=data.get("pain_points", []),
            opportunity_score=data.get("opportunity_score", 0),
            source=data.get("source", ""),
            raw_data=data.get("raw_data", {}),
            status="new",
        )
        db.add(lead)
        count += 1

    db.commit()
    return count


def _guess_industry(categories: list) -> str:
    if not categories:
        return "General Business"
    cat_map = {
        "restaurant": "Restaurant & Food",
        "food": "Restaurant & Food",
        "cafe": "Restaurant & Food",
        "salon": "Beauty & Wellness",
        "spa": "Beauty & Wellness",
        "beauty": "Beauty & Wellness",
        "gym": "Fitness & Health",
        "fitness": "Fitness & Health",
        "dental": "Healthcare",
        "medical": "Healthcare",
        "doctor": "Healthcare",
        "lawyer": "Legal",
        "attorney": "Legal",
        "real estate": "Real Estate",
        "realtor": "Real Estate",
        "contractor": "Home Services",
        "plumber": "Home Services",
        "electrician": "Home Services",
        "retail": "Retail",
        "shop": "Retail",
        "store": "Retail",
        "hotel": "Hospitality",
        "auto": "Automotive",
        "car": "Automotive",
    }
    combined = " ".join(str(c).lower() for c in categories)
    for keyword, industry in cat_map.items():
        if keyword in combined:
            return industry
    return categories[0] if categories else "General Business"
