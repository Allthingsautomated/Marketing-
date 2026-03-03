"""
All Things Automated — AI Lead Engine
FastAPI Web Dashboard + API
"""
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List
import csv
import io
import json
from datetime import datetime

from database import init_db, get_db, Lead, LearningRecord, SearchSession
from pipeline import run_search
from ai.scorer import generate_outreach_email, learn_from_outcome
from config import PORT, DEBUG

app = FastAPI(title="AI Lead Engine", version="1.0.0")
templates = Jinja2Templates(directory="dashboard/templates")
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")

# Init DB on startup
@app.on_event("startup")
def startup():
    init_db()


# ─────────────────────────────────────────────
# DASHBOARD PAGES
# ─────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    total = db.query(Lead).count()
    new = db.query(Lead).filter(Lead.status == "new").count()
    contacted = db.query(Lead).filter(Lead.status == "contacted").count()
    qualified = db.query(Lead).filter(Lead.status == "qualified").count()
    converted = db.query(Lead).filter(Lead.status == "converted").count()
    top_leads = db.query(Lead).order_by(Lead.ai_score.desc()).limit(5).all()
    recent_sessions = db.query(SearchSession).order_by(SearchSession.created_at.desc()).limit(5).all()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": {
            "total": total, "new": new, "contacted": contacted,
            "qualified": qualified, "converted": converted,
        },
        "top_leads": top_leads,
        "recent_sessions": recent_sessions,
    })


@app.get("/leads", response_class=HTMLResponse)
async def leads_page(
    request: Request,
    status: Optional[str] = None,
    industry: Optional[str] = None,
    min_score: Optional[float] = None,
    page: int = 1,
    db: Session = Depends(get_db)
):
    query = db.query(Lead)
    if status:
        query = query.filter(Lead.status == status)
    if industry:
        query = query.filter(Lead.industry.ilike(f"%{industry}%"))
    if min_score:
        query = query.filter(Lead.ai_score >= min_score)

    total = query.count()
    per_page = 25
    leads = query.order_by(Lead.ai_score.desc()).offset((page - 1) * per_page).limit(per_page).all()
    industries = [r[0] for r in db.query(Lead.industry).distinct().all() if r[0]]

    return templates.TemplateResponse("leads.html", {
        "request": request,
        "leads": leads,
        "total": total,
        "page": page,
        "per_page": per_page,
        "filters": {"status": status, "industry": industry, "min_score": min_score},
        "industries": industries,
    })


@app.get("/leads/{lead_id}", response_class=HTMLResponse)
async def lead_detail(request: Request, lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return templates.TemplateResponse("lead_detail.html", {"request": request, "lead": lead})


@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request):
    return templates.TemplateResponse("search.html", {"request": request})


# ─────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────

@app.post("/api/search")
async def api_search(
    background_tasks: BackgroundTasks,
    query: str = Form(...),
    location: str = Form(...),
    industry: str = Form(""),
    sources: str = Form("google_maps,yelp"),
    max_per_source: int = Form(20),
    db: Session = Depends(get_db)
):
    """Kick off a lead search in the background."""
    source_list = [s.strip() for s in sources.split(",")]
    background_tasks.add_task(
        run_search, query, location, industry, source_list, max_per_source, db
    )
    return JSONResponse({"status": "started", "message": f"Searching for '{query}' in '{location}'..."})


@app.post("/api/leads/{lead_id}/status")
async def update_status(lead_id: int, status: str = Form(...), db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    old_status = lead.status
    lead.status = status
    if status in ("converted", "lost") and old_status != status:
        learn_from_outcome(lead.__dict__, status, db)
    db.commit()
    return {"status": "updated", "new_status": status}


@app.post("/api/leads/{lead_id}/notes")
async def update_notes(lead_id: int, notes: str = Form(...), db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.notes = notes
    db.commit()
    return {"status": "saved"}


@app.get("/api/leads/{lead_id}/email")
async def get_outreach_email(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    email = generate_outreach_email(lead.__dict__)
    return {"email": email}


@app.get("/api/leads/export/csv")
async def export_leads_csv(
    status: Optional[str] = None,
    min_score: Optional[float] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Lead)
    if status:
        query = query.filter(Lead.status == status)
    if min_score:
        query = query.filter(Lead.ai_score >= min_score)
    leads = query.order_by(Lead.ai_score.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Business Name", "Industry", "City", "State", "Phone", "Email",
        "Website", "AI Score", "Opportunity Score", "Status",
        "Google Rating", "Google Reviews", "Has Meta Pixel", "Has Google Ads",
        "Pain Points", "Best Pitch", "Created"
    ])
    for l in leads:
        writer.writerow([
            l.business_name, l.industry, l.city, l.state, l.phone, l.email,
            l.website, l.ai_score, l.opportunity_score, l.status,
            l.google_rating, l.google_review_count, l.has_meta_ads, l.has_google_ads,
            " | ".join(l.pain_points or []), l.ai_reasoning, l.created_at
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"}
    )


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    leads = db.query(Lead).all()
    return {
        "total": len(leads),
        "by_status": {
            s: sum(1 for l in leads if l.status == s)
            for s in ["new", "contacted", "qualified", "converted", "lost"]
        },
        "avg_score": sum(l.ai_score or 0 for l in leads) / max(len(leads), 1),
        "top_industries": _top_industries(leads),
    }


def _top_industries(leads):
    counts = {}
    for l in leads:
        if l.industry:
            counts[l.industry] = counts.get(l.industry, 0) + 1
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=DEBUG)
