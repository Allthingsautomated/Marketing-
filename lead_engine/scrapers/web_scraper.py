"""
Web scraper — analyzes a business's website to detect:
- Ad pixels (Meta, Google)
- Social media presence
- Website quality signals
- Contact info
- Tech stack (what tools they're using)
"""
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
from urllib.parse import urlparse
import time


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

AD_PIXEL_PATTERNS = {
    "meta_pixel": [r"connect\.facebook\.net", r"fbq\(", r"_fbq"],
    "google_ads": [r"googleadservices\.com", r"gtag\(.*AW-", r"google_conversion"],
    "google_analytics": [r"google-analytics\.com", r"gtag\(.*G-", r"ga\("],
    "tiktok_pixel": [r"analytics\.tiktok\.com", r"ttq\."],
    "hotjar": [r"hotjar\.com"],
    "hubspot": [r"hs-scripts\.com", r"hubspot\.com"],
    "mailchimp": [r"mailchimp\.com", r"list-manage\.com"],
}

SOCIAL_PATTERNS = {
    "facebook": r"facebook\.com/(?!sharer|share|dialog)[\w\.\-]+",
    "instagram": r"instagram\.com/[\w\.\-]+",
    "twitter": r"twitter\.com/[\w\.\-]+|x\.com/[\w\.\-]+",
    "linkedin": r"linkedin\.com/(?:company|in)/[\w\.\-]+",
    "youtube": r"youtube\.com/(?:channel|user|c)/[\w\.\-]+",
    "tiktok": r"tiktok\.com/@[\w\.\-]+",
}


def analyze_website(url: str, timeout: int = 10) -> Dict:
    """
    Analyze a business website and return intelligence about their marketing setup.
    """
    result = {
        "url": url,
        "reachable": False,
        "has_meta_pixel": False,
        "has_google_ads": False,
        "has_google_analytics": False,
        "has_other_pixels": [],
        "social_profiles": {},
        "has_contact_form": False,
        "has_live_chat": False,
        "has_booking": False,
        "has_ecommerce": False,
        "email_found": None,
        "phone_found": None,
        "website_quality_score": 0,
        "is_mobile_friendly": False,
        "page_title": "",
        "meta_description": "",
        "tech_stack": [],
        "error": None,
    }

    if not url:
        return result

    # Ensure URL has scheme
    if not url.startswith("http"):
        url = "https://" + url

    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        result["reachable"] = resp.status_code < 400
        html = resp.text
    except Exception as e:
        result["error"] = str(e)
        return result

    soup = BeautifulSoup(html, "html.parser")
    html_lower = html.lower()

    # --- Pixels & Tracking ---
    for pixel_name, patterns in AD_PIXEL_PATTERNS.items():
        detected = any(re.search(p, html) for p in patterns)
        if pixel_name == "meta_pixel":
            result["has_meta_pixel"] = detected
        elif pixel_name == "google_ads":
            result["has_google_ads"] = detected
        elif pixel_name == "google_analytics":
            result["has_google_analytics"] = detected
        elif detected:
            result["has_other_pixels"].append(pixel_name)

    # --- Social Profiles ---
    for platform, pattern in SOCIAL_PATTERNS.items():
        match = re.search(pattern, html)
        if match:
            result["social_profiles"][platform] = match.group(0)

    # --- Contact Signals ---
    result["has_contact_form"] = bool(soup.find("form"))
    result["has_live_chat"] = any(
        kw in html_lower for kw in ["intercom", "drift", "tawk.to", "livechat", "zendesk", "crisp.chat"]
    )
    result["has_booking"] = any(
        kw in html_lower for kw in ["calendly", "acuity", "book a", "schedule", "appointlet", "booknow"]
    )
    result["has_ecommerce"] = any(
        kw in html_lower for kw in ["shopify", "woocommerce", "add to cart", "checkout", "buy now"]
    )

    # --- Email & Phone ---
    emails = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", html)
    # Filter out common non-contact emails
    contact_emails = [e for e in emails if not any(x in e.lower() for x in [
        "example", "domain", "sentry", "wix", "adobe", "jquery", "schema"
    ])]
    result["email_found"] = contact_emails[0] if contact_emails else None

    phone_match = re.search(r"(\+?1?\s?)?(\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4})", html)
    result["phone_found"] = phone_match.group(0).strip() if phone_match else None

    # --- Owner/Contact Name ---
    result["owner_name"] = _extract_owner_name(soup, html)

    # --- Page Metadata ---
    title = soup.find("title")
    result["page_title"] = title.get_text(strip=True) if title else ""
    meta_desc = soup.find("meta", attrs={"name": "description"})
    result["meta_description"] = meta_desc.get("content", "") if meta_desc else ""

    # --- Mobile Friendly ---
    viewport = soup.find("meta", attrs={"name": "viewport"})
    result["is_mobile_friendly"] = viewport is not None

    # --- Tech Stack ---
    tech = []
    tech_signals = {
        "WordPress": "wp-content",
        "Shopify": "shopify",
        "Wix": "wix.com",
        "Squarespace": "squarespace",
        "Webflow": "webflow",
        "React": "react",
        "Next.js": "__next",
        "Bootstrap": "bootstrap",
    }
    for name, signal in tech_signals.items():
        if signal in html_lower:
            tech.append(name)
    result["tech_stack"] = tech

    # --- Website Quality Score ---
    result["website_quality_score"] = _score_website(result, soup, html)

    return result


def _extract_owner_name(soup: BeautifulSoup, html: str) -> Optional[str]:
    """
    Try to find the owner/principal name from About or Team sections.
    Looks for common patterns like "Founded by X", "Owner: X", etc.
    """
    # Pattern: "Owner", "Founder", "Principal", "President", "CEO" followed by a name
    patterns = [
        r"(?:owner|founder|principal|president|ceo|director|operator)[:\s,]+([A-Z][a-z]+ [A-Z][a-z]+)",
        r"([A-Z][a-z]+ [A-Z][a-z]+),\s*(?:owner|founder|principal|president|ceo)",
        r"(?:by|with)\s+([A-Z][a-z]+ [A-Z][a-z]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Basic sanity check — skip if it looks like a company or generic phrase
            skip_words = {"All Rights", "Privacy Policy", "Terms Of", "Cookie Policy"}
            if name not in skip_words and len(name.split()) <= 4:
                return name

    # Check meta tags for author
    author_meta = soup.find("meta", attrs={"name": "author"})
    if author_meta:
        content = author_meta.get("content", "").strip()
        if content and len(content.split()) <= 4:
            return content

    return None


def _score_website(data: Dict, soup: BeautifulSoup, html: str) -> int:
    """Score 0-100. Low score = more opportunity for us to help them."""
    score = 0

    if data["reachable"]:
        score += 10
    if data["is_mobile_friendly"]:
        score += 15
    if data["has_meta_pixel"]:
        score += 10
    if data["has_google_ads"]:
        score += 10
    if data["has_google_analytics"]:
        score += 5
    if data["social_profiles"]:
        score += min(len(data["social_profiles"]) * 5, 15)
    if data["has_contact_form"]:
        score += 5
    if data["has_live_chat"]:
        score += 5
    if data["has_booking"]:
        score += 5
    if data["page_title"]:
        score += 5
    if data["meta_description"]:
        score += 5
    if data["has_ecommerce"]:
        score += 5

    return min(score, 100)
