"""
main.py – Sports Diary FastAPI application entry point  (v3)

Route summary
-------------
/api/auth/*              Authentication (phone OTP + email OTP), user profiles,
                         multi-role management, organiser/professional role requests
/api/media/*             Image upload, ad banners, dynamic filter config, gallery
/api/tournaments/*       Tournament & team CRUD, registrations,
                         match scheduling, fixtures, results, standings
/api/venues/*            Venue discovery, booking, reviews
/api/marketplace/*       Shops, job listings, job applications lifecycle
/api/nearby/*            Geo-proximity search (50 km default radius)
/api/reviews/*           Unified entity reviews
/api/community/*         Communities & posts & polls
/api/professionals/*     Professional availability & bookings
/api/organizer-team/     Organiser manager / co-manager management
/api/admin/*             Super admin / admin panel, organiser approvals,
                         professional fee confirmations
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api import (
    auth, tournaments, venues, marketplace, nearby,
    reviews, community, professionals, organizer_team, admin, media,
)
from app.core.database import connect_to_mongo, close_mongo_connection
from app.core.scheduler import start_scheduler, stop_scheduler

app = FastAPI(
    title="Sports Diary API",
    description="Backend API for the Sports Diary multi-sport ERP platform.",
    version="3.0.0",
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
cors_origins_env = os.getenv("CORS_ORIGINS", "*")
origins = ["*"] if cors_origins_env == "*" else cors_origins_env.split(",")
print(f"🔒 CORS origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ─── LIFECYCLE ────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    await connect_to_mongo()
    for subdir in [
        "user_avatar", "venue", "shop", "tournament_banner", "tournament_image",
        "ad_banner", "academy", "community", "team_logo", "job_banner", "profile_image",
    ]:
        os.makedirs(os.path.join("uploads", subdir), exist_ok=True)
    start_scheduler()
    print("✅ MongoDB connected and upload directories ready!")


@app.on_event("shutdown")
async def shutdown():
    stop_scheduler()
    await close_mongo_connection()


# ─── HEALTH / ROOT ────────────────────────────────────────────────────────────
@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {
        "status":   "healthy",
        "service":  "sports-diary-api",
        "version":  "3.0.0",
        "database": "mongodb",
    }


@app.get("/")
@app.get("/api")
async def root():
    return {
        "message": "Welcome to Sports Diary API v3",
        "docs":    "/docs",
        "version": "3.0.0",
        "database": "MongoDB",
        "new_in_v3": [
            "Email OTP login",
            "Multi-role users (roles[])",
            "Organiser role approval workflow",
            "Professional ₹3000 fee gate",
            "Job applications lifecycle",
            "Match scheduling & results",
            "Tournament standings",
        ],
    }


# ─── ROUTERS ──────────────────────────────────────────────────────────────────
app.include_router(auth.router,           prefix="/api/auth",           tags=["Authentication"])
app.include_router(media.router,          prefix="/api/media",          tags=["Media & Config"])
app.include_router(tournaments.router,    prefix="/api/tournaments",    tags=["Tournaments"])
app.include_router(venues.router,         prefix="/api/venues",         tags=["Venues"])
app.include_router(marketplace.router,    prefix="/api/marketplace",    tags=["Marketplace"])
app.include_router(nearby.router,         prefix="/api/nearby",         tags=["Nearby"])
app.include_router(reviews.router,        prefix="/api/reviews",        tags=["Reviews"])
app.include_router(community.router,      prefix="/api/community",      tags=["Community"])
app.include_router(professionals.router,  prefix="/api/professionals",  tags=["Professionals"])
app.include_router(organizer_team.router, prefix="/api/organizer-team", tags=["Organizer Team"])
app.include_router(admin.router,          prefix="/api/admin",          tags=["Admin"])

# ─── STATIC FILES ─────────────────────────────────────────────────────────────
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
