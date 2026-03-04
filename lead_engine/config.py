import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
SECRET_KEY = os.getenv("SECRET_KEY", "ata-lead-engine-secret")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/leads.db")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Business Identity
BUSINESS_NAME = "All Things Automated"
OWNER_NAME = "Jorge Romero"

# Target Markets
MARKETS = [
    "Sarasota, FL",
    "Lakewood Ranch, FL",
    "Siesta Key, FL",
    "Longboat Key, FL",
    "Palmer Ranch, FL",
]

# Lead categories with pre-built search queries
CATEGORIES = {
    "custom_builders": {
        "label": "Custom Home Builders",
        "goal": 20,
        "queries": [
            "custom home builder",
            "luxury home builder",
            "custom home contractor",
            "residential home builder",
        ],
    },
    "interior_designers": {
        "label": "Interior Designers",
        "goal": 15,
        "queries": [
            "interior designer",
            "luxury interior designer",
            "interior design studio",
        ],
    },
    "architects": {
        "label": "Architects",
        "goal": 10,
        "queries": [
            "residential architect",
            "custom home architect",
            "architecture firm",
        ],
    },
    "commercial_contractors": {
        "label": "Commercial General Contractors",
        "goal": 10,
        "queries": [
            "general contractor",
            "commercial contractor",
            "construction company",
        ],
    },
}

# Intro email template (Jorge's version)
INTRO_EMAIL_TEMPLATE = """Hi {name},

I specialize in engineered lighting control and smart home automation systems for high-end residential builds in Sarasota. My focus is designing lighting and automation architecture early in the build process to simplify coordination and enhance the homeowner experience.

Would you be open to a short introduction meeting?

Jorge Romero
All Things Automated
"""
