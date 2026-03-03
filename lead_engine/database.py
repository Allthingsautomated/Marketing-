from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime,
    Text, Boolean, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String(255), nullable=False)
    industry = Column(String(100))
    address = Column(String(500))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    phone = Column(String(50))
    email = Column(String(255))
    website = Column(String(500))
    google_rating = Column(Float)
    google_review_count = Column(Integer)
    yelp_rating = Column(Float)
    yelp_review_count = Column(Integer)
    has_facebook = Column(Boolean, default=False)
    has_instagram = Column(Boolean, default=False)
    has_google_ads = Column(Boolean, default=False)
    has_meta_ads = Column(Boolean, default=False)
    website_score = Column(Integer, default=0)   # 0-100: how good their site is
    ai_score = Column(Float, default=0.0)         # 0-100: overall lead quality
    ai_reasoning = Column(Text)
    pain_points = Column(JSON)                    # list of identified pain points
    opportunity_score = Column(Float, default=0.0)  # how much room to improve
    status = Column(String(50), default="new")   # new, contacted, qualified, converted, lost
    notes = Column(Text)
    source = Column(String(100))                 # google_maps, yelp, scraper, manual
    raw_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_contacted = Column(DateTime)


class LearningRecord(Base):
    __tablename__ = "learning_records"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer)
    outcome = Column(String(50))        # converted, lost, qualified
    industry = Column(String(100))
    ai_score_at_contact = Column(Float)
    features = Column(JSON)             # features that mattered for this outcome
    lesson = Column(Text)               # AI-generated insight
    created_at = Column(DateTime, default=datetime.utcnow)


class SearchSession(Base):
    __tablename__ = "search_sessions"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(500))
    location = Column(String(255))
    industry = Column(String(100))
    leads_found = Column(Integer, default=0)
    avg_score = Column(Float, default=0.0)
    source = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
