from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime
from bson import ObjectId
from typing import Optional, List

from app.core.database import get_database
from app.core.security import get_current_user
from app.schemas.schemas import (
    VenueCreate, VenueUpdate,
    TournamentCreate, TournamentUpdate,
    ShopCreate, ShopUpdate,
    JobCreate, JobUpdate,
    AcademyCreate, AcademyUpdate,
)

router = APIRouter(tags=["admin"])


# ─── guards ───────────────────────────────────────────────────────────────────

def _super_admin(user: dict):
    if user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="super_admin access required")

def _admin_or_super(user: dict):
    if user.get("role") not in ("super_admin", "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

def _serialize(doc: dict) -> dict:
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


# ─── STATS ────────────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_admin_stats(current_user: dict = Depends(get_current_user)):
    """Platform-wide statistics (admin / super_admin)."""
    _admin_or_super(current_user)
    db = get_database()
    return {
        "total_users":        await db.users.count_documents({}),
        "total_tournaments":  await db.tournaments.count_documents({}),
        "total_venues":       await db.venues.count_documents({}),
        "total_shops":        await db.shops.count_documents({}),
        "total_academies":    await db.academies.count_documents({}),
        "total_jobs":         await db.jobs.count_documents({}),
        "total_communities":  await db.communities.count_documents({}),
        "total_posts":        await db.community_posts.count_documents({}),
        "total_ad_banners":   await db.ad_banners.count_documents({"is_active": True}),
        "total_media_assets": await db.media_assets.count_documents({"is_active": True}),
    }


# ─── USER MANAGEMENT ──────────────────────────────────────────────────────────

@router.get("/users")
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
):
    _super_admin(current_user)
    db    = get_database()
    users = await db.users.find({}).skip(skip).limit(limit).sort("created_at", -1).to_list(length=limit)
    for u in users:
        u["id"] = str(u["_id"]); del u["_id"]
    return {"users": users, "total": await db.users.count_documents({})}


@router.post("/users/create")
async def create_user_as_admin(
    user_data: dict,
    current_user: dict = Depends(get_current_user),
):
    """Create a user with any role (super_admin only)."""
    _super_admin(current_user)
    db    = get_database()
    phone = user_data.get("phone")
    name  = user_data.get("name")
    if not phone or not name:
        raise HTTPException(status_code=400, detail="phone and name are required")
    if await db.users.find_one({"phone": phone}):
        raise HTTPException(status_code=400, detail="User with this phone already exists")

    role = user_data.get("role", "player")
    doc  = {
        "phone":                phone,
        "name":                 name,
        "email":                user_data.get("email"),
        "role":                 role,
        "age":                  user_data.get("age"),
        "gender":               user_data.get("gender"),
        "city":                 user_data.get("city"),
        "state":                user_data.get("state", "Gujarat"),
        "bio":                  user_data.get("bio"),
        # avatar URL from /api/media/upload if provided
        "avatar":               user_data.get("avatar"),
        "sports_interests":     user_data.get("sports_interests", []),
        "professional_type":    user_data.get("professional_type") if role == "professional" else None,
        "certification":        user_data.get("certification"),
        "experience_years":     user_data.get("experience_years"),
        "children_count":       user_data.get("children_count", 0) if role == "parent" else None,
        "is_verified":          True,
        "onboarding_completed": True,
        "created_at":           datetime.utcnow(),
        "updated_at":           datetime.utcnow(),
    }
    doc = {k: v for k, v in doc.items() if v is not None}
    result = await db.users.insert_one(doc)
    return {"message": "User created", "user_id": str(result.inserted_id)}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    _super_admin(current_user)
    db = get_database()
    r  = await db.users.delete_one({"_id": ObjectId(user_id)})
    if r.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted", "deleted_id": user_id}


# ─── VENUE MANAGEMENT ─────────────────────────────────────────────────────────

@router.get("/venues")
async def get_all_venues(
    skip: int = 0, limit: int = 100,
    current_user: dict = Depends(get_current_user),
):
    _admin_or_super(current_user)
    db     = get_database()
    venues = await db.venues.find({}).skip(skip).limit(limit).sort("created_at", -1).to_list(length=limit)
    for v in venues:
        v["id"] = str(v["_id"]); del v["_id"]
    return {"venues": venues, "total": await db.venues.count_documents({})}


@router.post("/venues/create")
async def create_venue_as_admin(
    venue_data: VenueCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Super admin creates a venue.
    images field should contain URLs from POST /api/media/upload (entity_type='venue').
    """
    _admin_or_super(current_user)
    db  = get_database()
    doc = venue_data.dict()
    doc.update({
        "owner_id":      str(current_user["_id"]),
        "rating":        0.0,
        "total_reviews": 0,
        "total_bookings":0,
        "is_verified":   True,
        "is_featured":   False,
        "is_active":     True,
        "created_at":    datetime.utcnow(),
        "updated_at":    datetime.utcnow(),
    })
    result = await db.venues.insert_one(doc)
    return {"message": "Venue created", "venue_id": str(result.inserted_id)}


@router.put("/venues/{venue_id}")
async def update_venue_as_admin(
    venue_id: str,
    venue_data: VenueUpdate,
    current_user: dict = Depends(get_current_user),
):
    _admin_or_super(current_user)
    db     = get_database()
    update = {k: v for k, v in venue_data.dict(exclude_unset=True).items() if v is not None}
    update["updated_at"] = datetime.utcnow()
    await db.venues.update_one({"_id": ObjectId(venue_id)}, {"$set": update})
    updated = await db.venues.find_one({"_id": ObjectId(venue_id)})
    return _serialize(updated)


@router.delete("/venues/{venue_id}")
async def delete_venue(venue_id: str, current_user: dict = Depends(get_current_user)):
    _super_admin(current_user)
    db = get_database()
    r  = await db.venues.delete_one({"_id": ObjectId(venue_id)})
    if r.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Venue not found")
    return {"message": "Venue deleted", "deleted_id": venue_id}


# ─── TOURNAMENT MANAGEMENT ────────────────────────────────────────────────────

@router.get("/tournaments")
async def get_all_tournaments(
    skip: int = 0, limit: int = 100,
    current_user: dict = Depends(get_current_user),
):
    _admin_or_super(current_user)
    db   = get_database()
    docs = await db.tournaments.find({}).skip(skip).limit(limit).sort("created_at", -1).to_list(length=limit)
    for d in docs:
        d["id"] = str(d["_id"]); del d["_id"]
    return {"tournaments": docs, "total": await db.tournaments.count_documents({})}


@router.post("/tournaments/create")
async def create_tournament_as_admin(
    tournament_data: TournamentCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Admin creates a tournament.
    banner_image / additional_images should be URLs from /api/media/upload
    (entity_type='tournament_banner' or 'tournament_image').
    """
    _admin_or_super(current_user)
    db  = get_database()
    doc = tournament_data.dict()
    doc.update({
        "organizer_id":  str(current_user["_id"]),
        "created_by":    str(current_user["_id"]),
        "current_teams": 0,
        "views_count":   0,
        "status":        "upcoming",
        "is_featured":   False,
        "is_verified":   True,
        "is_active":     True,
        "created_at":    datetime.utcnow(),
        "updated_at":    datetime.utcnow(),
    })
    result = await db.tournaments.insert_one(doc)
    return {"message": "Tournament created", "tournament_id": str(result.inserted_id)}


@router.put("/tournaments/{tournament_id}/feature")
async def feature_tournament(
    tournament_id: str,
    featured: bool,
    current_user: dict = Depends(get_current_user),
):
    """Toggle is_featured on a tournament."""
    _admin_or_super(current_user)
    db = get_database()
    await db.tournaments.update_one(
        {"_id": ObjectId(tournament_id)},
        {"$set": {"is_featured": featured, "updated_at": datetime.utcnow()}},
    )
    return {"message": f"Tournament {'featured' if featured else 'unfeatured'}"}


@router.delete("/tournaments/{tournament_id}")
async def delete_tournament(tournament_id: str, current_user: dict = Depends(get_current_user)):
    _super_admin(current_user)
    db = get_database()
    r  = await db.tournaments.delete_one({"_id": ObjectId(tournament_id)})
    if r.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return {"message": "Tournament deleted", "deleted_id": tournament_id}


# ─── SHOP MANAGEMENT ──────────────────────────────────────────────────────────

@router.get("/shops")
async def get_all_shops(
    skip: int = 0, limit: int = 100,
    current_user: dict = Depends(get_current_user),
):
    _admin_or_super(current_user)
    db   = get_database()
    docs = await db.shops.find({}).skip(skip).limit(limit).sort("created_at", -1).to_list(length=limit)
    for d in docs:
        d["id"] = str(d["_id"]); del d["_id"]
    return {"shops": docs, "total": await db.shops.count_documents({})}


@router.post("/shops/create")
async def create_shop_as_admin(
    shop_data: ShopCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Admin creates a shop.
    images should be URLs from POST /api/media/upload (entity_type='shop').
    """
    _admin_or_super(current_user)
    db  = get_database()
    doc = shop_data.dict()
    doc.update({
        "owner_id":       str(current_user["_id"]),
        "rating":         0.0,
        "total_reviews":  0,
        "total_enquiries":0,
        "is_featured":    False,
        "is_verified":    True,
        "is_active":      True,
        "created_at":     datetime.utcnow(),
        "updated_at":     datetime.utcnow(),
    })
    result = await db.shops.insert_one(doc)
    return {"message": "Shop created", "shop_id": str(result.inserted_id)}


@router.delete("/shops/{shop_id}")
async def delete_shop(shop_id: str, current_user: dict = Depends(get_current_user)):
    _super_admin(current_user)
    db = get_database()
    r  = await db.shops.delete_one({"_id": ObjectId(shop_id)})
    if r.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Shop not found")
    return {"message": "Shop deleted", "deleted_id": shop_id}


# ─── JOB MANAGEMENT ───────────────────────────────────────────────────────────

@router.get("/jobs")
async def get_all_jobs(
    skip: int = 0, limit: int = 100,
    current_user: dict = Depends(get_current_user),
):
    _admin_or_super(current_user)
    db   = get_database()
    docs = await db.jobs.find({}).skip(skip).limit(limit).sort("created_at", -1).to_list(length=limit)
    for d in docs:
        d["id"] = str(d["_id"]); del d["_id"]
    return {"jobs": docs, "total": await db.jobs.count_documents({})}


@router.post("/jobs/create")
async def create_job_as_admin(
    job_data: JobCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Admin creates a job listing.
    banner_image should be a URL from POST /api/media/upload (entity_type='job_banner').
    """
    _admin_or_super(current_user)
    db  = get_database()
    doc = job_data.dict()
    doc.update({
        "posted_by":          str(current_user["_id"]),
        "views_count":        0,
        "applications_count": 0,
        "status":             "open",
        "is_featured":        False,
        "is_verified":        True,
        "is_active":          True,
        "created_at":         datetime.utcnow(),
        "updated_at":         datetime.utcnow(),
    })
    result = await db.jobs.insert_one(doc)
    return {"message": "Job created", "job_id": str(result.inserted_id)}


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, current_user: dict = Depends(get_current_user)):
    _super_admin(current_user)
    db = get_database()
    r  = await db.jobs.delete_one({"_id": ObjectId(job_id)})
    if r.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job deleted", "deleted_id": job_id}


# ─── ACADEMY MANAGEMENT (super_admin) ─────────────────────────────────────────

@router.get("/academies")
async def get_all_academies(
    skip: int = 0, limit: int = 100,
    sport_type: Optional[str] = None,
    city: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """List all academies from the academies collection (admin+)."""
    _admin_or_super(current_user)
    db    = get_database()
    query: dict = {}
    if sport_type:
        query["sport_type"] = {"$regex": sport_type, "$options": "i"}
    if city:
        query["city"] = {"$regex": city, "$options": "i"}
    docs  = await db.academies.find(query).skip(skip).limit(limit).sort("created_at", -1).to_list(length=limit)
    for d in docs:
        d["id"] = str(d["_id"]); del d["_id"]
    return {"academies": docs, "total": await db.academies.count_documents(query)}


@router.post("/academies/create")
async def create_academy_as_admin(
    academy_data: AcademyCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Super admin creates an academy entry.
    Stores all rich fields (programs, timing, fees, coaching_staff, amenities,
    age_groups, cover_image, gallery_images, etc.) in the `academies` collection.

    Image URLs must come from POST /api/media/upload (entity_type="academy").
    """
    _admin_or_super(current_user)
    db  = get_database()

    # Build document — keep every field the admin sends, including rich ones
    doc = {k: v for k, v in academy_data.dict().items() if v is not None}

    # Normalise: store sport under both keys so old and new queries both work
    doc.setdefault("sport", doc.get("sport_type"))
    doc.setdefault("term",  doc.get("name"))         # backward compat alias

    doc.update({
        "owner_id":      str(current_user["_id"]),
        "rating":        0.0,
        "total_reviews": 0,
        "views_count":   0,
        "helpful_count": 0,
        "is_featured":   False,
        "is_verified":   True,
        "is_active":     True,
        "category":      "Academy",
        "created_at":    datetime.utcnow(),
        "updated_at":    datetime.utcnow(),
    })

    result  = await db.academies.insert_one(doc)
    created = await db.academies.find_one({"_id": result.inserted_id})
    created["id"] = str(created["_id"]); del created["_id"]
    return {"message": "Academy created", "academy_id": created["id"], "academy": created}


@router.get("/academies/{academy_id}")
async def get_academy_as_admin(
    academy_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a single academy document (admin+)."""
    _admin_or_super(current_user)
    db = get_database()
    try:
        doc = await db.academies.find_one({"_id": ObjectId(academy_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid academy ID")
    if not doc:
        raise HTTPException(status_code=404, detail="Academy not found")
    return _serialize(doc)


@router.put("/academies/{academy_id}")
async def update_academy_as_admin(
    academy_id: str,
    data: AcademyUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update any field on an academy (admin+)."""
    _admin_or_super(current_user)
    db     = get_database()
    update = {k: v for k, v in data.dict(exclude_unset=True).items() if v is not None}
    # Keep alias fields in sync
    if "name" in update:
        update["term"] = update["name"]
    if "sport_type" in update:
        update["sport"] = update["sport_type"]
    update["updated_at"] = datetime.utcnow()
    await db.academies.update_one({"_id": ObjectId(academy_id)}, {"$set": update})
    updated = await db.academies.find_one({"_id": ObjectId(academy_id)})
    return _serialize(updated)


@router.delete("/academies/{academy_id}")
async def delete_academy(academy_id: str, current_user: dict = Depends(get_current_user)):
    """Hard-delete an academy (super_admin only)."""
    _super_admin(current_user)
    db = get_database()
    r  = await db.academies.delete_one({"_id": ObjectId(academy_id)})
    if r.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Academy not found")
    return {"message": "Academy deleted", "deleted_id": academy_id}


@router.post("/academies/migrate-from-dictionary")
async def migrate_academies_from_dictionary(
    current_user: dict = Depends(get_current_user),
):
    """
    ONE-TIME migration: copies all documents where category='Academy'
    from the `dictionary` collection into the `academies` collection.

    Safe to call multiple times — skips documents already present
    (matched by the original _id).  Run this once after deploying v3
    to make existing seeded academies visible in the new endpoints.
    """
    _super_admin(current_user)
    db = get_database()

    cursor      = db.dictionary.find({"category": "Academy"})
    old_docs    = await cursor.to_list(length=None)
    migrated    = 0
    skipped     = 0
    errors      = []

    for doc in old_docs:
        original_id = doc["_id"]
        # Check if already migrated (same _id exists in academies)
        exists = await db.academies.find_one({"_id": original_id})
        if exists:
            skipped += 1
            continue

        # Normalise field names to the unified schema
        new_doc = dict(doc)
        # sport_type from sport
        new_doc.setdefault("sport_type", new_doc.get("sport", ""))
        # name from term
        new_doc.setdefault("name", new_doc.get("term", ""))
        # description from definition/explanation
        if not new_doc.get("description"):
            defn = new_doc.get("definition", "")
            expl = new_doc.get("explanation", "")
            new_doc["description"] = f"{defn}. {expl}".strip(". ") if expl else defn
        # ensure category tag
        new_doc["category"] = "Academy"
        # ensure system fields
        new_doc.setdefault("rating", 0.0)
        new_doc.setdefault("total_reviews", 0)
        new_doc.setdefault("views_count", new_doc.get("views_count", 0))
        new_doc.setdefault("is_featured", new_doc.get("is_featured", False))
        new_doc.setdefault("is_verified", True)
        new_doc.setdefault("is_active",   new_doc.get("is_active", True))
        new_doc.setdefault("updated_at",  datetime.utcnow())

        try:
            await db.academies.insert_one(new_doc)
            migrated += 1
        except Exception as exc:
            errors.append({"id": str(original_id), "error": str(exc)})

    return {
        "message":  f"Migration complete. {migrated} migrated, {skipped} already present.",
        "migrated": migrated,
        "skipped":  skipped,
        "errors":   errors,
    }


# ─── COMMUNITY MANAGEMENT ─────────────────────────────────────────────────────

@router.get("/communities")
async def get_all_communities(
    skip: int = 0, limit: int = 100,
    current_user: dict = Depends(get_current_user),
):
    _admin_or_super(current_user)
    db   = get_database()
    docs = await db.communities.find({}).skip(skip).limit(limit).sort("created_at", -1).to_list(length=limit)
    for d in docs:
        d["id"] = str(d["_id"]); del d["_id"]
    return {"communities": docs, "total": await db.communities.count_documents({})}


@router.post("/communities/create")
async def create_community_as_admin(
    community_data: dict,
    current_user: dict = Depends(get_current_user),
):
    """
    Admin creates a community.
    cover_image should be a URL from POST /api/media/upload (entity_type='community').
    """
    _admin_or_super(current_user)
    db   = get_database()
    name = community_data.get("name")
    sport = community_data.get("sport_type")
    city  = community_data.get("city")
    if not name or not sport or not city:
        raise HTTPException(status_code=400, detail="name, sport_type, and city are required")
    doc = {
        "name":         name,
        "description":  community_data.get("description", ""),
        "sport_type":   sport,
        "city":         city,
        "state":        community_data.get("state", "Gujarat"),
        # cover_image URL from /api/media/upload (entity_type='community')
        "cover_image":  community_data.get("cover_image"),
        "created_by":   str(current_user["_id"]),
        "members":      [str(current_user["_id"])],
        "members_count":1,
        "posts_count":  0,
        "is_active":    True,
        "created_at":   datetime.utcnow(),
        "updated_at":   datetime.utcnow(),
    }
    result = await db.communities.insert_one(doc)
    return {"message": "Community created", "community_id": str(result.inserted_id)}


@router.delete("/communities/{community_id}")
async def delete_community(community_id: str, current_user: dict = Depends(get_current_user)):
    _super_admin(current_user)
    db = get_database()
    r  = await db.communities.delete_one({"_id": ObjectId(community_id)})
    if r.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Community not found")
    return {"message": "Community deleted", "deleted_id": community_id}


# ─── FEATURE / VERIFY TOGGLES ─────────────────────────────────────────────────

@router.put("/{collection}/{doc_id}/feature")
async def toggle_feature(
    collection: str,
    doc_id: str,
    featured: bool,
    current_user: dict = Depends(get_current_user),
):
    """Toggle is_featured on any collection document (admin+)."""
    _admin_or_super(current_user)
    if collection not in ("venues", "shops", "academies", "jobs", "tournaments", "communities"):
        raise HTTPException(status_code=400, detail="Invalid collection")
    db = get_database()
    await db[collection].update_one(
        {"_id": ObjectId(doc_id)},
        {"$set": {"is_featured": featured, "updated_at": datetime.utcnow()}},
    )
    return {"message": f"{'Featured' if featured else 'Unfeatured'} {collection}/{doc_id}"}


@router.put("/{collection}/{doc_id}/verify")
async def toggle_verify(
    collection: str,
    doc_id: str,
    verified: bool,
    current_user: dict = Depends(get_current_user),
):
    """Toggle is_verified on any collection document (admin+)."""
    _admin_or_super(current_user)
    if collection not in ("venues", "shops", "academies", "jobs", "tournaments", "users"):
        raise HTTPException(status_code=400, detail="Invalid collection")
    db = get_database()
    await db[collection].update_one(
        {"_id": ObjectId(doc_id)},
        {"$set": {"is_verified": verified, "updated_at": datetime.utcnow()}},
    )
    return {"message": f"{'Verified' if verified else 'Unverified'} {collection}/{doc_id}"}


# ─── ORGANISER APPROVAL ────────────────────────────────────────────────────────

@router.get("/pending-organizers")
async def get_pending_organizers(
    skip: int = 0, limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    """List all users with organizer_status='pending' (admin+)."""
    _admin_or_super(current_user)
    db   = get_database()
    docs = await db.users.find(
        {"organizer_status": "pending"}
    ).skip(skip).limit(limit).to_list(length=limit)
    result = []
    for d in docs:
        result.append({
            "id":                   str(d["_id"]),
            "name":                 d.get("name"),
            "phone":                d.get("phone"),
            "email":                d.get("email"),
            "city":                 d.get("city"),
            "organizer_status":     d.get("organizer_status"),
            "organizer_requested_at": d.get("organizer_requested_at"),
            "roles":                d.get("roles", []),
        })
    return {"pending_organizers": result, "total": len(result)}


@router.post("/approve-organizer/{user_id}")
async def approve_organizer(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Approve a user's organizer role request (admin+)."""
    _admin_or_super(current_user)
    db = get_database()
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.get("organizer_status") != "pending":
        raise HTTPException(status_code=400, detail="No pending organizer request for this user")

    roles = user.get("roles", [])
    if "organizer" not in roles:
        roles.append("organizer")
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "roles":                    roles,
            "role":                     roles[0],
            "organizer_status":         "approved",
            "organizer_approved_by":    str(current_user["_id"]),
            "organizer_approved_at":    datetime.utcnow(),
            "updated_at":               datetime.utcnow(),
        }},
    )
    return {"message": f"Organizer role approved for user {user_id}"}


@router.post("/reject-organizer/{user_id}")
async def reject_organizer(
    user_id: str,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Reject a user's organizer role request (admin+)."""
    _admin_or_super(current_user)
    db = get_database()
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "organizer_status":            "rejected",
            "organizer_rejection_reason":  reason,
            "updated_at":                  datetime.utcnow(),
        }},
    )
    return {"message": f"Organizer request rejected for user {user_id}"}


# ─── PROFESSIONAL FEE CONFIRMATION ────────────────────────────────────────────

@router.get("/pending-professionals")
async def get_pending_professionals(
    skip: int = 0, limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    """List users with professional_status='pending_payment' (admin+)."""
    _admin_or_super(current_user)
    db   = get_database()
    docs = await db.users.find(
        {"professional_status": "pending_payment"}
    ).skip(skip).limit(limit).to_list(length=limit)
    result = []
    for d in docs:
        result.append({
            "id":                    str(d["_id"]),
            "name":                  d.get("name"),
            "phone":                 d.get("phone"),
            "email":                 d.get("email"),
            "professional_type":     d.get("professional_type"),
            "professional_status":   d.get("professional_status"),
            "city":                  d.get("city"),
            "roles":                 d.get("roles", []),
        })
    return {"pending_professionals": result, "total": len(result)}


@router.post("/confirm-professional-fee/{user_id}")
async def confirm_professional_fee(
    user_id: str,
    transaction_ref: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Admin confirms that the ₹3000 professional fee has been received.
    Activates the professional role on the user's account.
    In a live system, wire this to your payment gateway webhook instead.
    """
    _admin_or_super(current_user)
    db = get_database()
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.get("professional_status") not in ("pending_payment", None):
        raise HTTPException(status_code=400, detail="No pending professional fee for this user")

    roles = user.get("roles", [])
    if "professional" not in roles:
        roles.append("professional")
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "roles":                        roles,
            "role":                         roles[0],
            "professional_status":          "active",
            "professional_fee_paid":        True,
            "professional_fee_paid_at":     datetime.utcnow(),
            "professional_fee_transaction": transaction_ref,
            "updated_at":                   datetime.utcnow(),
        }},
    )
    return {"message": f"Professional role activated for user {user_id}", "roles": roles}


# ─── ADMIN STATS (update to include new collections) ──────────────────────────

@router.get("/stats/extended")
async def get_extended_stats(current_user: dict = Depends(get_current_user)):
    """Extended platform stats including applications and matches."""
    _admin_or_super(current_user)
    db = get_database()
    return {
        "users":                    await db.users.count_documents({}),
        "venues":                   await db.venues.count_documents({}),
        "tournaments":              await db.tournaments.count_documents({}),
        "matches":                  await db.matches.count_documents({}),
        "shops":                    await db.shops.count_documents({}),
        "jobs":                     await db.jobs.count_documents({}),
        "job_applications":         await db.job_applications.count_documents({}),
        "academies":                await db.academies.count_documents({}),
        "communities":              await db.communities.count_documents({}),
        "pending_organizers":       await db.users.count_documents({"organizer_status": "pending"}),
        "pending_professionals":    await db.users.count_documents({"professional_status": "pending_payment"}),
        "professional_fee_revenue": await db.users.count_documents({"professional_fee_paid": True}) * 3000,
    }