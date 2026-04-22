"""
media.py – Centralised image/file upload + ad-banner management + dynamic config.

Upload pipeline
---------------
POST /api/media/upload
  • Accepts any image (JPEG, PNG, WEBP, GIF) up to 10 MB.
  • If CLOUDINARY_CLOUD_NAME env var is set → uploads to Cloudinary (permanent CDN URL).
  • Otherwise → saves to uploads/<entity_type>/ on local disk (dev fallback).
  • Inserts a media_assets document in MongoDB with the public URL.
  • Returns the URL and media_id so the caller stores the URL in the
    relevant entity (user.avatar, venue.images, tournament.banner_image …).

  Required env vars for Cloudinary (set on Render):
    CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET

  Allowed entity_types:
    user_avatar | venue | shop | tournament_banner | tournament_image |
    ad_banner | academy | community | team_logo | job_banner | profile_image

Ad Banners (super_admin only)
------------------------------
POST   /api/media/ad-banners            create
GET    /api/media/ad-banners            list (public – Flutter carousel reads this)
PUT    /api/media/ad-banners/{id}       update
DELETE /api/media/ad-banners/{id}       delete
PUT    /api/media/ad-banners/reorder    bulk reorder

Dynamic Filter Config (super_admin write, public read)
-------------------------------------------------------
GET  /api/media/config/filters/{page}   Flutter reads per-page dynamic filter chips
PUT  /api/media/config/filters/{page}   super_admin overrides
GET  /api/media/config/{key}            generic key-value config read
PUT  /api/media/config/{key}            super_admin sets generic config

Media Gallery
-------------
GET  /api/media/gallery/{entity_type}/{entity_id}  all assets for one entity
"""

import os
import re
import uuid
import mimetypes
from datetime import datetime
from typing import Optional, List

import cloudinary
import cloudinary.uploader

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from bson import ObjectId

from app.core.database import get_database
from app.core.security import get_current_user
from app.schemas.schemas import (
    AdBannerCreate, AdBannerUpdate, AdBannerResponse,
    FilterConfigResponse, AppConfigResponse, MediaUploadResponse,
)

router = APIRouter(tags=["media"])

# ─── constants ────────────────────────────────────────────────────────────────

UPLOAD_DIR    = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024          # 10 MB
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

ALLOWED_ENTITY_TYPES = {
    "user_avatar", "venue", "shop", "tournament_banner", "tournament_image",
    "ad_banner", "academy", "community", "team_logo", "job_banner", "profile_image",
}

# ─── helpers ──────────────────────────────────────────────────────────────────

def _super_admin_guard(user: dict):
    if user.get("role") != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only super_admin can perform this action")

def _admin_guard(user: dict):
    if user.get("role") not in ("super_admin", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Admin access required")

def _serialize(doc: dict) -> dict:
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc

def _get_base_url() -> str:
    url = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
    # Normalize: http://host:443 → https://host (common Render misconfiguration)
    url = re.sub(r'^http://(.*):443$', r'https://\1', url)
    # Normalize: http://host:80 → http://host
    url = re.sub(r'^(http://.*):80$', r'\1', url)
    return url


def _use_cloudinary() -> bool:
    """True when Cloudinary env vars are present (production). Falls back to local disk."""
    return bool(os.getenv("CLOUDINARY_CLOUD_NAME"))


def _cloudinary_cfg():
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", ""),
        api_key=os.getenv("CLOUDINARY_API_KEY", ""),
        api_secret=os.getenv("CLOUDINARY_API_SECRET", ""),
        secure=True,
    )


# ─── UPLOAD ──────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=MediaUploadResponse)
async def upload_media(
    file: UploadFile = File(...),
    entity_type: str = Form(...),
    entity_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a single image and receive a publicly accessible URL.

    The caller then stores that URL in the relevant entity document, e.g.:
      • PUT /api/auth/profile          { "avatar": "<url>" }
      • POST /api/media/ad-banners     { "image_url": "<url>", … }
      • POST /api/venues               { "images": ["<url>", …], … }
      • POST /api/tournaments          { "banner_image": "<url>", … }

    entity_type must be one of:
      user_avatar, venue, shop, tournament_banner, tournament_image,
      ad_banner, academy, community, team_logo, job_banner, profile_image

    Rules
    -----
    • ad_banner uploads are restricted to super_admin.
    • All other authenticated users may upload for their own entities.
    """
    if entity_type not in ALLOWED_ENTITY_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"entity_type '{entity_type}' not allowed. Choose from: {sorted(ALLOWED_ENTITY_TYPES)}",
        )

    if entity_type == "ad_banner":
        _super_admin_guard(current_user)

    # Validate MIME type
    content_type = file.content_type or ""
    if content_type not in ALLOWED_TYPES:
        guessed, _ = mimetypes.guess_type(file.filename or "")
        if guessed not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '{content_type}'. Allowed: JPEG, PNG, WEBP, GIF",
            )
        content_type = guessed

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds maximum size of 10 MB",
        )

    ext      = (file.filename or "image.jpg").rsplit(".", 1)[-1].lower()
    filename = f"{entity_type}_{uuid.uuid4().hex}.{ext}"

    cld_public_id: str | None = None

    if _use_cloudinary():
        _cloudinary_cfg()
        cld_pid = f"sports_diary/{entity_type}/{filename.rsplit('.', 1)[0]}"
        result  = cloudinary.uploader.upload(
            data,
            public_id=cld_pid,
            resource_type="image",
            overwrite=False,
        )
        public_url    = result["secure_url"]
        cld_public_id = result["public_id"]
        print(f"[MEDIA] Uploaded to Cloudinary: {public_url}")
    else:
        sub_dir   = os.path.join(UPLOAD_DIR, entity_type)
        os.makedirs(sub_dir, exist_ok=True)
        file_path = os.path.join(sub_dir, filename)
        with open(file_path, "wb") as f:
            f.write(data)
        public_url = f"{_get_base_url()}/uploads/{entity_type}/{filename}"
        print(f"[MEDIA] Saved locally: {file_path}")

    db  = get_database()
    now = datetime.utcnow()
    doc = {
        "url":                  public_url,
        "filename":             filename,
        "original_filename":    file.filename,
        "media_type":           "image",
        "entity_type":          entity_type,
        "entity_id":            entity_id,
        "content_type":         content_type,
        "size_bytes":           len(data),
        "uploaded_by":          str(current_user["_id"]),
        "storage":              "cloudinary" if cld_public_id else "local",
        "cloudinary_public_id": cld_public_id,
        "is_active":            True,
        "created_at":           now,
        "updated_at":           now,
    }
    result = await db.media_assets.insert_one(doc)

    return MediaUploadResponse(
        url=public_url,
        media_id=str(result.inserted_id),
        media_type="image",
        entity_type=entity_type,
        entity_id=entity_id,
        uploaded_by=str(current_user["_id"]),
        created_at=now,
    )


@router.delete("/media-assets/{media_id}")
async def delete_media(
    media_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a media asset. Owner or admin/super_admin can delete."""
    db = get_database()
    try:
        doc = await db.media_assets.find_one({"_id": ObjectId(media_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid media ID")

    if not doc:
        raise HTTPException(status_code=404, detail="Media not found")

    user_id = str(current_user["_id"])
    role    = current_user.get("role", "")
    if doc["uploaded_by"] != user_id and role not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Not authorised to delete this media")

    # Remove file from storage
    cld_pid = doc.get("cloudinary_public_id")
    if cld_pid:
        try:
            _cloudinary_cfg()
            cloudinary.uploader.destroy(cld_pid, resource_type="image")
        except Exception as e:
            print(f"[MEDIA] Warning: could not delete from Cloudinary: {e}")
    else:
        try:
            fp = os.path.join(UPLOAD_DIR, doc.get("entity_type", ""), doc.get("filename", ""))
            if os.path.exists(fp):
                os.remove(fp)
        except Exception as e:
            print(f"[MEDIA] Warning: could not delete file from disk: {e}")

    await db.media_assets.delete_one({"_id": ObjectId(media_id)})
    return {"message": "Media deleted successfully"}


# ─── AD BANNERS ───────────────────────────────────────────────────────────────

@router.get("/ad-banners")
async def list_ad_banners(active_only: bool = True):
    """
    Public endpoint – Flutter RoleSelectionScreen reads this to build the
    ad carousel. Returns banners sorted by sort_order ascending.
    Upload the image first via POST /api/media/upload (entity_type=ad_banner),
    then create the banner with the returned URL.
    """
    db    = get_database()
    query = {"is_active": True} if active_only else {}
    cursor  = db.ad_banners.find(query).sort([("sort_order", 1), ("created_at", -1)])
    banners = await cursor.to_list(length=100)
    for b in banners:
        b["id"] = str(b["_id"])
        del b["_id"]
    return {"banners": banners, "count": len(banners)}


@router.post("/ad-banners")
async def create_ad_banner(
    data: AdBannerCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Super admin creates an ad banner.
    image_url must come from POST /api/media/upload with entity_type='ad_banner'.
    """
    _super_admin_guard(current_user)
    db  = get_database()
    now = datetime.utcnow()
    doc = {
        **data.dict(),
        "created_by": str(current_user["_id"]),
        "created_at": now,
        "updated_at": now,
    }
    result  = await db.ad_banners.insert_one(doc)
    created = await db.ad_banners.find_one({"_id": result.inserted_id})
    return _serialize(created)


@router.put("/ad-banners/reorder")
async def reorder_ad_banners(
    order: List[dict],          # [{"id": "...", "sort_order": 0}, …]
    current_user: dict = Depends(get_current_user),
):
    """Super admin bulk-reorders ad banners."""
    _super_admin_guard(current_user)
    db = get_database()
    for item in order:
        try:
            await db.ad_banners.update_one(
                {"_id": ObjectId(item["id"])},
                {"$set": {"sort_order": item["sort_order"], "updated_at": datetime.utcnow()}},
            )
        except Exception:
            pass
    return {"message": "Banners reordered successfully"}


@router.put("/ad-banners/{banner_id}")
async def update_ad_banner(
    banner_id: str,
    data: AdBannerUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Super admin updates an existing ad banner."""
    _super_admin_guard(current_user)
    db = get_database()
    try:
        existing = await db.ad_banners.find_one({"_id": ObjectId(banner_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid banner ID")
    if not existing:
        raise HTTPException(status_code=404, detail="Banner not found")

    update = {k: v for k, v in data.dict(exclude_unset=True).items() if v is not None}
    update["updated_at"] = datetime.utcnow()
    await db.ad_banners.update_one({"_id": ObjectId(banner_id)}, {"$set": update})
    updated = await db.ad_banners.find_one({"_id": ObjectId(banner_id)})
    return _serialize(updated)


@router.delete("/ad-banners/{banner_id}")
async def delete_ad_banner(
    banner_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Super admin deletes an ad banner."""
    _super_admin_guard(current_user)
    db = get_database()
    try:
        result = await db.ad_banners.delete_one({"_id": ObjectId(banner_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid banner ID")
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Banner not found")
    return {"message": "Banner deleted successfully"}


# ─── DYNAMIC FILTER CONFIG ────────────────────────────────────────────────────

# Built-in defaults per page — super_admin can override in DB.
_DEFAULT_FILTERS = {
    "venues": [
        {"key": "city",           "label": "City",         "type": "single_select", "options": []},
        {"key": "sport",          "label": "Sport",        "type": "single_select", "options": []},
        {"key": "indoor_outdoor", "label": "Type",         "type": "single_select", "options": ["Indoor", "Outdoor", "Both"]},
        {"key": "min_price",      "label": "Min Price",    "type": "number"},
        {"key": "max_price",      "label": "Max Price",    "type": "number"},
        {"key": "min_rating",     "label": "Min Rating",   "type": "number"},
        {"key": "amenities",      "label": "Amenities",    "type": "multi_select",  "options": []},
    ],
    "tournaments": [
        {"key": "city",            "label": "City",         "type": "single_select", "options": []},
        {"key": "sport_type",      "label": "Sport",        "type": "single_select", "options": []},
        {"key": "status",          "label": "Status",       "type": "single_select", "options": ["upcoming", "ongoing", "completed"]},
        {"key": "age_category",    "label": "Age Category", "type": "single_select", "options": []},
        {"key": "gender_category", "label": "Gender",       "type": "single_select", "options": ["Male", "Female", "Mixed"]},
        {"key": "skill_level",     "label": "Skill Level",  "type": "single_select", "options": ["Beginner", "Intermediate", "Advanced", "Open"]},
    ],
    "jobs": [
        {"key": "city",            "label": "City",         "type": "single_select", "options": []},
        {"key": "job_type",        "label": "Job Type",     "type": "single_select", "options": []},
        {"key": "sport_type",      "label": "Sport",        "type": "single_select", "options": []},
        {"key": "employment_type", "label": "Employment",   "type": "single_select", "options": ["Full-time", "Part-time", "Contract", "Per Match"]},
    ],
    "professionals": [
        {"key": "city",              "label": "City",       "type": "single_select", "options": []},
        {"key": "professional_type", "label": "Type",       "type": "single_select", "options": ["Umpire", "Coach", "Trainer", "Venue Owner", "Sports Manager"]},
        {"key": "sport_type",        "label": "Sport",      "type": "single_select", "options": []},
        {"key": "can_coach",         "label": "Can Coach",  "type": "boolean"},
        {"key": "can_umpire",        "label": "Can Umpire", "type": "boolean"},
    ],
    "shops": [
        {"key": "city",     "label": "City",     "type": "single_select", "options": []},
        {"key": "category", "label": "Category", "type": "single_select", "options": []},
    ],
    "academies": [
        {"key": "city",       "label": "City",  "type": "single_select", "options": []},
        {"key": "sport_type", "label": "Sport", "type": "single_select", "options": []},
    ],
}


@router.get("/config/filters/{page}")
async def get_filter_config(page: str):
    """
    Flutter calls this on page load to build dynamic search/filter chips.
    Falls back to built-in defaults if super_admin hasn't customised this page.
    City / sport / amenity / category option lists are populated live from DB.
    """
    db         = get_database()
    config_doc = await db.filter_configs.find_one({"page": page})

    if config_doc:
        filters    = config_doc.get("filters", [])
        updated_at = config_doc.get("updated_at", datetime.utcnow())
    else:
        filters    = _DEFAULT_FILTERS.get(page, [])
        updated_at = datetime.utcnow()

    filters = await _enrich_filter_options(db, page, filters)
    return {"page": page, "filters": filters, "updated_at": updated_at}


async def _enrich_filter_options(db, page: str, filters: list) -> list:
    """
    Dynamically populate city / sport / amenity / category option lists
    from live DB so Flutter never has hard-coded lists.
    """
    enriched = []
    for f in filters:
        f   = dict(f)
        key = f.get("key")

        if key == "city":
            coll = {"venues": "venues", "tournaments": "tournaments",
                    "jobs": "jobs", "professionals": "users",
                    "shops": "shops", "academies": "academies"}.get(page, "venues")
            cities = await db[coll].distinct("city", {"is_active": True})
            f["options"] = sorted([c for c in cities if c])

        elif key in ("sport", "sport_type"):
            coll  = {"venues": "venues", "tournaments": "tournaments",
                     "jobs": "jobs", "professionals": "professional_availabilities",
                     "shops": "shops", "academies": "academies"}.get(page, "venues")
            field = "sports_available" if coll == "venues" else "sport_type"
            sports = await db[coll].distinct(field)
            if isinstance(sports[0] if sports else None, list):
                # flatten nested lists (venues.sports_available)
                flat = []
                for s in sports:
                    (flat.extend(s) if isinstance(s, list) else flat.append(s))
                sports = flat
            f["options"] = sorted(list(set(s for s in sports if s)))

        elif key == "amenities" and page == "venues":
            amenities = await db.venues.distinct("amenities")
            flat = []
            for a in amenities:
                (flat.extend(a) if isinstance(a, list) else (flat.append(a) if a else None))
            f["options"] = sorted(list(set(flat)))

        elif key == "category" and page == "shops":
            cats = await db.shops.distinct("category", {"is_active": True})
            f["options"] = sorted([c for c in cats if c])

        elif key == "age_category" and page == "tournaments":
            cats = await db.tournaments.distinct("age_category", {"is_active": True})
            f["options"] = sorted([c for c in cats if c])

        elif key == "job_type" and page == "jobs":
            types = await db.jobs.distinct("job_type", {"is_active": True})
            f["options"] = sorted([t for t in types if t])

        enriched.append(f)
    return enriched


@router.put("/config/filters/{page}")
async def update_filter_config(
    page: str,
    filters: List[dict],
    current_user: dict = Depends(get_current_user),
):
    """Super admin customises the filter chips shown on a given page."""
    _super_admin_guard(current_user)
    db  = get_database()
    now = datetime.utcnow()
    await db.filter_configs.update_one(
        {"page": page},
        {"$set": {"filters": filters, "updated_at": now}},
        upsert=True,
    )
    return {"page": page, "filters": filters, "updated_at": now}


# ─── GENERIC APP CONFIG ───────────────────────────────────────────────────────

@router.get("/config/{key}")
async def get_config(key: str):
    """Read a generic app-wide config value (e.g. 'sports_list', 'cities_list')."""
    db  = get_database()
    doc = await db.app_configs.find_one({"key": key})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Config key '{key}' not found")
    return {"key": doc["key"], "value": doc["value"], "updated_at": doc.get("updated_at")}


@router.put("/config/{key}")
async def set_config(
    key: str,
    payload: dict,          # {"value": <anything>}
    current_user: dict = Depends(get_current_user),
):
    """Super admin sets a generic config value."""
    _super_admin_guard(current_user)
    db    = get_database()
    value = payload.get("value")
    now   = datetime.utcnow()
    await db.app_configs.update_one(
        {"key": key},
        {"$set": {"value": value, "updated_at": now, "updated_by": str(current_user["_id"])}},
        upsert=True,
    )
    return {"key": key, "value": value, "updated_at": now}


# ─── MEDIA GALLERY ────────────────────────────────────────────────────────────

@router.get("/gallery/{entity_type}/{entity_id}")
async def get_entity_gallery(entity_type: str, entity_id: str):
    """Return all media assets uploaded for a specific entity (venue, shop, tournament…)."""
    db     = get_database()
    cursor = db.media_assets.find(
        {"entity_type": entity_type, "entity_id": entity_id, "is_active": True}
    ).sort("created_at", -1)
    assets = await cursor.to_list(length=200)
    for a in assets:
        a["id"] = str(a["_id"])
        del a["_id"]
    return {"assets": assets, "count": len(assets)}
