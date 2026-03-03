"""
AI Lead Scoring Engine
- Scores each lead 0-100 based on opportunity
- Identifies pain points
- Generates personalized outreach angles
- Learns from past outcomes
"""
import json
import anthropic
from typing import Dict, List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ANTHROPIC_API_KEY


client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None


SCORING_PROMPT = """You are the world's best marketing agency sales expert. You analyze businesses to determine if they are good leads for a full-service marketing agency.

You will be given data about a business including:
- Basic info (name, industry, location)
- Their current marketing setup (pixels, ads, social media)
- Website quality score
- Review counts and ratings
- Any other signals

Your job is to:
1. Score them 0-100 as a lead (100 = perfect lead, 0 = terrible lead)
2. Score their opportunity 0-100 (how much room is there for marketing improvement)
3. List their specific pain points
4. Suggest the best angle to pitch them
5. Recommend which services would help them most

A GOOD lead has:
- A real business with revenue potential
- Clear gaps in their marketing (no pixel, no ads, poor social, bad website)
- Signs they WANT to grow (decent reviews, existing customers, active business)
- Budget signals (established, multiple locations, decent review count)

A BAD lead has:
- Already has a sophisticated marketing team
- Tiny business with no growth potential
- Permanently closed or suspicious

Return a JSON object with this exact structure:
{
  "ai_score": <0-100 float>,
  "opportunity_score": <0-100 float>,
  "pain_points": ["point1", "point2", "point3"],
  "best_pitch_angle": "<1-2 sentence pitch hook specific to this business>",
  "recommended_services": ["service1", "service2"],
  "reasoning": "<2-3 sentences explaining your score>",
  "priority": "<high|medium|low>",
  "estimated_monthly_budget": "<low $500-1k|medium $1k-3k|high $3k+>"
}"""


def score_lead(lead_data: Dict, learning_context: Optional[str] = None) -> Dict:
    """
    Score a lead using AI. Returns scoring dict.
    lead_data should contain all scraped fields.
    """
    if not client:
        return _fallback_score(lead_data)

    # Build context for AI
    context = _build_context(lead_data)
    if learning_context:
        context += f"\n\nLEARNING FROM PAST WINS:\n{learning_context}"

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": f"{SCORING_PROMPT}\n\nBUSINESS DATA:\n{context}"}
            ]
        )
        raw = message.content[0].text.strip()
        # Extract JSON even if wrapped in markdown
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        print(f"[AI Scorer] Error: {e}")
        return _fallback_score(lead_data)


def batch_score_leads(leads: List[Dict], learning_context: Optional[str] = None) -> List[Dict]:
    """Score multiple leads and return them sorted by ai_score descending."""
    scored = []
    for i, lead in enumerate(leads):
        print(f"[AI Scorer] Scoring lead {i+1}/{len(leads)}: {lead.get('business_name', 'Unknown')}")
        scores = score_lead(lead, learning_context)
        scored.append({**lead, **scores})
    return sorted(scored, key=lambda x: x.get("ai_score", 0), reverse=True)


def generate_outreach_email(lead: Dict) -> str:
    """Generate a personalized cold outreach email for a lead."""
    if not client:
        return _fallback_email(lead)

    prompt = f"""Write a short, personalized cold outreach email from a marketing agency to this business.

Business: {lead.get('business_name')}
Industry: {lead.get('industry', 'unknown')}
Location: {lead.get('city')}, {lead.get('state')}
Their Pain Points: {json.dumps(lead.get('pain_points', []))}
Best Pitch Angle: {lead.get('best_pitch_angle', '')}

Rules:
- 3-4 short paragraphs max
- Sound human, not salesy
- Reference something specific about their business
- One clear CTA (15-minute call)
- Subject line included at top as "Subject: ..."
- Do NOT use generic phrases like "I hope this finds you well"
"""
    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text.strip()
    except Exception as e:
        return _fallback_email(lead)


def learn_from_outcome(lead: Dict, outcome: str, db_session) -> str:
    """
    When a lead converts or is lost, extract lessons to improve future scoring.
    Saves insight to learning_records table.
    """
    if not client:
        return ""

    prompt = f"""A marketing agency just {outcome} a business lead. Extract lessons to improve future lead scoring.

Business: {lead.get('business_name')} ({lead.get('industry')})
AI Score Given: {lead.get('ai_score')}
Outcome: {outcome}
Pain Points Identified: {json.dumps(lead.get('pain_points', []))}
Website Score: {lead.get('website_quality_score')}
Had Meta Pixel: {lead.get('has_meta_pixel')}
Had Google Ads: {lead.get('has_google_ads')}
Reviews: {lead.get('google_review_count')} Google, {lead.get('yelp_review_count')} Yelp

What patterns should we look for more/less in future leads of this industry?
Return 2-3 bullet points as plain text."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        lesson = message.content[0].text.strip()

        # Save to DB
        from database import LearningRecord
        record = LearningRecord(
            lead_id=lead.get("id"),
            outcome=outcome,
            industry=lead.get("industry"),
            ai_score_at_contact=lead.get("ai_score"),
            features={
                "has_meta_pixel": lead.get("has_meta_pixel"),
                "has_google_ads": lead.get("has_google_ads"),
                "website_score": lead.get("website_quality_score"),
                "google_reviews": lead.get("google_review_count"),
            },
            lesson=lesson,
        )
        db_session.add(record)
        db_session.commit()
        return lesson
    except Exception as e:
        print(f"[AI Learner] Error: {e}")
        return ""


def get_learning_context(db_session) -> str:
    """Pull recent lessons from DB to feed into scoring prompts."""
    try:
        from database import LearningRecord
        records = db_session.query(LearningRecord).order_by(
            LearningRecord.created_at.desc()
        ).limit(20).all()
        if not records:
            return ""
        lines = []
        for r in records:
            lines.append(f"[{r.outcome.upper()} - {r.industry}] {r.lesson}")
        return "\n".join(lines)
    except Exception:
        return ""


def _build_context(lead: Dict) -> str:
    lines = [
        f"Business Name: {lead.get('business_name', 'Unknown')}",
        f"Industry/Categories: {lead.get('industry') or lead.get('categories', [])}",
        f"Location: {lead.get('city')}, {lead.get('state')}",
        f"Phone: {lead.get('phone', 'None')}",
        f"Website: {lead.get('website', 'None')}",
        f"Google Rating: {lead.get('google_rating')} ({lead.get('google_review_count')} reviews)",
        f"Yelp Rating: {lead.get('yelp_rating')} ({lead.get('yelp_review_count')} reviews)",
        f"Has Meta Pixel: {lead.get('has_meta_pixel', False)}",
        f"Has Google Ads Pixel: {lead.get('has_google_ads', False)}",
        f"Has Google Analytics: {lead.get('has_google_analytics', False)}",
        f"Social Profiles: {json.dumps(lead.get('social_profiles', {}))}",
        f"Website Quality Score: {lead.get('website_quality_score', 0)}/100",
        f"Has Contact Form: {lead.get('has_contact_form', False)}",
        f"Has Live Chat: {lead.get('has_live_chat', False)}",
        f"Has Online Booking: {lead.get('has_booking', False)}",
        f"Has E-commerce: {lead.get('has_ecommerce', False)}",
        f"Tech Stack: {lead.get('tech_stack', [])}",
    ]
    return "\n".join(lines)


def _fallback_score(lead: Dict) -> Dict:
    """Basic scoring when AI is unavailable."""
    score = 40.0
    opportunity = 60.0
    pain_points = []

    if not lead.get("has_meta_pixel"):
        score += 5
        opportunity += 10
        pain_points.append("No Meta advertising pixel installed")
    if not lead.get("has_google_ads"):
        score += 5
        opportunity += 10
        pain_points.append("Not running Google Ads")
    if not lead.get("social_profiles"):
        pain_points.append("Limited or no social media presence")
    website_score = lead.get("website_quality_score", 0)
    if website_score < 40:
        opportunity += 10
        pain_points.append("Outdated or low-quality website")

    reviews = (lead.get("google_review_count") or 0) + (lead.get("yelp_review_count") or 0)
    if reviews > 50:
        score += 10  # Established business

    return {
        "ai_score": min(score, 100),
        "opportunity_score": min(opportunity, 100),
        "pain_points": pain_points,
        "best_pitch_angle": f"Help {lead.get('business_name')} grow their online presence",
        "recommended_services": ["Social Media Management", "Google Ads", "Website Redesign"],
        "reasoning": "Scored using fallback rules (AI unavailable)",
        "priority": "medium",
        "estimated_monthly_budget": "medium $1k-3k",
    }


def _fallback_email(lead: Dict) -> str:
    name = lead.get("business_name", "there")
    return f"""Subject: Quick question about {name}'s online growth

Hi {name} team,

I came across your business and noticed some opportunities to help you attract more customers online.

Most businesses in your area are missing out on [specific opportunity]. We've helped similar businesses grow their revenue by 30-50% in the first 90 days.

Would you be open to a 15-minute call this week to explore if we'd be a good fit?

Best,
All Things Automated Marketing"""
