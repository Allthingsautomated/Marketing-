"""
All Things Automated — Lead Engine
Sarasota FL | Smart Home & Lighting Control
"""
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
import csv
import io
from datetime import datetime

from database import init_db, get_db, Lead, SearchSession
from pipeline import run_search, run_category_search
from config import PORT, DEBUG, CATEGORIES, MARKETS, INTRO_EMAIL_TEMPLATE, OWNER_NAME

app = FastAPI(title="ATA Lead Engine", version="2.0.0")
templates = Jinja2Templates(directory="dashboard/templates")
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")


@app.on_event("startup")
def startup():
    init_db()


# ─────────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    total = db.query(Lead).count()
    status_counts = {
        s: db.query(Lead).filter(Lead.status == s).count()
        for s in ["new", "contacted", "meeting_scheduled", "proposal_sent", "closed", "lost"]
    }
    category_counts = {
        key: db.query(Lead).filter(Lead.category == key).count()
        for key in CATEGORIES
    }
    recent_leads = db.query(Lead).order_by(Lead.created_at.desc()).limit(10).all()
    recent_sessions = db.query(SearchSession).order_by(SearchSession.created_at.desc()).limit(5).all()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "total": total,
        "status_counts": status_counts,
        "category_counts": category_counts,
        "categories": CATEGORIES,
        "markets": MARKETS,
        "recent_leads": recent_leads,
        "recent_sessions": recent_sessions,
    })


@app.get("/leads", response_class=HTMLResponse)
async def leads_page(
    request: Request,
    status: Optional[str] = None,
    category: Optional[str] = None,
    city: Optional[str] = None,
    page: int = 1,
    db: Session = Depends(get_db),
):
    query = db.query(Lead)
    if status:
        query = query.filter(Lead.status == status)
    if category:
        query = query.filter(Lead.category == category)
    if city:
        query = query.filter(Lead.city.ilike(f"%{city}%"))

    total = query.count()
    per_page = 30
    leads = query.order_by(Lead.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    cities = sorted([r[0] for r in db.query(Lead.city).distinct().all() if r[0]])

    return templates.TemplateResponse("leads.html", {
        "request": request,
        "leads": leads,
        "total": total,
        "page": page,
        "per_page": per_page,
        "filters": {"status": status, "category": category, "city": city},
        "categories": CATEGORIES,
        "cities": cities,
        "statuses": ["new", "contacted", "meeting_scheduled", "proposal_sent", "closed", "lost"],
    })


@app.get("/leads/{lead_id}", response_class=HTMLResponse)
async def lead_detail(request: Request, lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    cat_label = CATEGORIES.get(lead.category, {}).get("label", lead.category or "—")
    intro_email = INTRO_EMAIL_TEMPLATE.format(name=lead.owner_name or lead.business_name)
    return templates.TemplateResponse("lead_detail.html", {
        "request": request,
        "lead": lead,
        "cat_label": cat_label,
        "intro_email": intro_email,
        "statuses": ["new", "contacted", "meeting_scheduled", "proposal_sent", "closed", "lost"],
    })


@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request):
    return templates.TemplateResponse("search.html", {
        "request": request,
        "categories": CATEGORIES,
        "markets": MARKETS,
    })


# ─────────────────────────────────────────────
# API
# ─────────────────────────────────────────────

@app.post("/api/search")
async def api_search(
    background_tasks: BackgroundTasks,
    query: str = Form(...),
    location: str = Form(...),
    category: str = Form(""),
    max_per_source: int = Form(20),
    db: Session = Depends(get_db),
):
    """Custom keyword search."""
    background_tasks.add_task(
        run_search, query, location, category, ["google_maps"], max_per_source, db
    )
    return JSONResponse({"status": "started", "message": f"Searching '{query}' in {location}..."})


@app.post("/api/search/category")
async def api_search_category(
    background_tasks: BackgroundTasks,
    category: str = Form(...),
    market: str = Form(...),
    db: Session = Depends(get_db),
):
    """One-click: run all queries for a category in a market."""
    if category not in CATEGORIES:
        raise HTTPException(status_code=400, detail="Unknown category")
    if market not in MARKETS:
        raise HTTPException(status_code=400, detail="Unknown market")

    background_tasks.add_task(run_category_search, category, market, 20, db)
    cat_label = CATEGORIES[category]["label"]
    return JSONResponse({"status": "started", "message": f"Searching {cat_label} in {market}..."})


@app.post("/api/leads/{lead_id}/status")
async def update_status(lead_id: int, status: str = Form(...), db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.status = status
    lead.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "updated", "new_status": status}


@app.post("/api/leads/{lead_id}/notes")
async def update_notes(lead_id: int, notes: str = Form(...), db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.notes = notes
    lead.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "saved"}


@app.get("/api/leads/export/csv")
async def export_csv(
    status: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Lead)
    if status:
        query = query.filter(Lead.status == status)
    if category:
        query = query.filter(Lead.category == category)
    leads = query.order_by(Lead.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Business Name", "Owner Name", "Category", "Phone", "Email",
        "Address", "City", "State", "Website",
        "Google Rating", "Google Reviews", "Status", "Notes", "Date Added"
    ])
    for l in leads:
        cat_label = CATEGORIES.get(l.category, {}).get("label", l.category or "")
        writer.writerow([
            l.business_name, l.owner_name or "", cat_label,
            l.phone or "", l.email or "",
            l.address or "", l.city or "", l.state or "",
            l.website or "",
            l.google_rating or "", l.google_review_count or "",
            l.status, l.notes or "",
            l.created_at.strftime("%Y-%m-%d") if l.created_at else "",
        ])

    output.seek(0)
    filename = f"ata_leads_{datetime.now().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    leads = db.query(Lead).all()
    return {
        "total": len(leads),
        "by_status": {
            s: sum(1 for l in leads if l.status == s)
            for s in ["new", "contacted", "meeting_scheduled", "proposal_sent", "closed", "lost"]
        },
        "by_category": {
            key: sum(1 for l in leads if l.category == key)
            for key in CATEGORIES
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=DEBUG)
