from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime,
    Text, Boolean, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from config import DATABASE_URL

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String(255), nullable=False)
    owner_name = Column(String(255))              # owner/contact name
    category = Column(String(100))               # custom_builders, interior_designers, architects, commercial_contractors
    address = Column(String(500))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    phone = Column(String(50))
    email = Column(String(255))
    website = Column(String(500))
    google_rating = Column(Float)
    google_review_count = Column(Integer)
    has_facebook = Column(Boolean, default=False)
    has_instagram = Column(Boolean, default=False)
    status = Column(String(50), default="new")   # new, contacted, meeting_scheduled, proposal_sent, closed, lost
    notes = Column(Text)
    source = Column(String(100))
    raw_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SearchSession(Base):
    __tablename__ = "search_sessions"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(500))
    location = Column(String(255))
    category = Column(String(100))
    leads_found = Column(Integer, default=0)
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
