from fastapi import APIRouter, Depends, Query
from typing import Optional, List
import math

from app.core.database import get_database
from app.core.security import get_current_user

router = APIRouter()

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula (in km)"""
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


@router.get("/venues")
async def get_nearby_venues(
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    radius_km: float = Query(50, description="Search radius in kilometers"),
    sport_type: Optional[str] = None,
    limit: int = Query(20, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get nearby venues based on user location"""
    db = get_database()
    
    # Use provided coordinates or fallback to user's stored location
    user_lat = latitude if latitude is not None else current_user.get("latitude")
    user_lon = longitude if longitude is not None else current_user.get("longitude")
    
    if user_lat is None or user_lon is None:
        # If no location available, return venues from user's city
        query = {"is_active": True}
        if current_user.get("city"):
            query["city"] = current_user["city"]
        if sport_type:
            query["sports_available"] = sport_type
        
        # Get total count before limiting
        total_count = await db.venues.count_documents(query)
        
        venues_cursor = db.venues.find(query).limit(limit)
        venues = await venues_cursor.to_list(length=limit)
        
        for venue in venues:
            venue["id"] = str(venue["_id"])
            del venue["_id"]  # Remove ObjectId
        
        return {"venues": venues, "using_location": False, "count": total_count}
    
    # Get all active venues with coordinates
    query = {
        "is_active": True,
        "latitude": {"$ne": None},
        "longitude": {"$ne": None}
    }
    
    if sport_type:
        query["sports_available"] = sport_type
    
    venues_cursor = db.venues.find(query)
    all_venues = await venues_cursor.to_list(length=None)
    
    # Calculate distances and filter by radius
    venues_with_distance = []
    for venue in all_venues:
        distance = calculate_distance(user_lat, user_lon, venue["latitude"], venue["longitude"])
        if distance <= radius_km:
            venue["id"] = str(venue["_id"])
            del venue["_id"]  # Remove ObjectId to avoid serialization issues
            venue["distance_km"] = round(distance, 1)
            venues_with_distance.append(venue)
    
    # Sort by distance
    venues_with_distance.sort(key=lambda x: x['distance_km'])
    
    return {
        "venues": venues_with_distance[:limit],
        "using_location": True,
        "user_location": {"latitude": user_lat, "longitude": user_lon},
        "count": len(venues_with_distance)
    }


@router.get("/tournaments")
async def get_nearby_tournaments(
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    radius_km: float = Query(50, description="Search radius in kilometers"),
    sport_type: Optional[str] = None,
    limit: int = Query(20, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get nearby tournaments based on user location"""
    db = get_database()
    
    user_lat = latitude if latitude is not None else current_user.get("latitude")
    user_lon = longitude if longitude is not None else current_user.get("longitude")
    
    if user_lat is None or user_lon is None:
        query = {"is_active": True, "status": "upcoming"}
        if current_user.get("city"):
            query["city"] = current_user["city"]
        if sport_type:
            query["sport_type"] = sport_type
        
        # Get total count before limiting
        total_count = await db.tournaments.count_documents(query)
        
        tournaments_cursor = db.tournaments.find(query).limit(limit)
        tournaments = await tournaments_cursor.to_list(length=limit)
        
        for tournament in tournaments:
            tournament["id"] = str(tournament["_id"])
            del tournament["_id"]  # Remove ObjectId
        
        return {"tournaments": tournaments, "using_location": False, "count": total_count}
    
    query = {
        "is_active": True,
        "status": "upcoming",
        "latitude": {"$ne": None},
        "longitude": {"$ne": None}
    }
    
    if sport_type:
        query["sport_type"] = sport_type
    
    tournaments_cursor = db.tournaments.find(query)
    all_tournaments = await tournaments_cursor.to_list(length=None)
    
    tournaments_with_distance = []
    for tournament in all_tournaments:
        distance = calculate_distance(user_lat, user_lon, tournament["latitude"], tournament["longitude"])
        if distance <= radius_km:
            tournament["id"] = str(tournament["_id"])
            del tournament["_id"]  # Remove ObjectId
            tournament["distance_km"] = round(distance, 1)
            tournaments_with_distance.append(tournament)
    
    tournaments_with_distance.sort(key=lambda x: x['distance_km'])
    
    return {
        "tournaments": tournaments_with_distance[:limit],
        "using_location": True,
        "user_location": {"latitude": user_lat, "longitude": user_lon},
        "count": len(tournaments_with_distance)
    }


@router.get("/shops")
async def get_nearby_shops(
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    radius_km: float = Query(50, description="Search radius in kilometers"),
    category: Optional[str] = None,
    limit: int = Query(20, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get nearby sports shops based on user location"""
    db = get_database()
    
    user_lat = latitude if latitude is not None else current_user.get("latitude")
    user_lon = longitude if longitude is not None else current_user.get("longitude")
    
    if user_lat is None or user_lon is None:
        query = {"is_active": True}
        if current_user.get("city"):
            query["city"] = current_user["city"]
        if category:
            query["category"] = category
        
        # Get total count before limiting
        total_count = await db.shops.count_documents(query)
        
        shops_cursor = db.shops.find(query).limit(limit)
        shops = await shops_cursor.to_list(length=limit)
        
        for shop in shops:
            shop["id"] = str(shop["_id"])
            del shop["_id"]  # Remove ObjectId
        
        return {"shops": shops, "using_location": False, "count": total_count}
    
    query = {
        "is_active": True,
        "latitude": {"$ne": None},
        "longitude": {"$ne": None}
    }
    
    if category:
        query["category"] = category
    
    shops_cursor = db.shops.find(query)
    all_shops = await shops_cursor.to_list(length=None)
    
    shops_with_distance = []
    for shop in all_shops:
        distance = calculate_distance(user_lat, user_lon, shop["latitude"], shop["longitude"])
        if distance <= radius_km:
            shop["id"] = str(shop["_id"])
            del shop["_id"]  # Remove ObjectId
            shop["distance_km"] = round(distance, 1)
            shops_with_distance.append(shop)
    
    shops_with_distance.sort(key=lambda x: x['distance_km'])
    
    return {
        "shops": shops_with_distance[:limit],
        "using_location": True,
        "user_location": {"latitude": user_lat, "longitude": user_lon},
        "count": len(shops_with_distance)
    }


@router.get("/jobs")
async def get_nearby_jobs(
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    radius_km: float = Query(100, description="Search radius in kilometers"),
    job_type: Optional[str] = None,
    limit: int = Query(20, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get nearby jobs based on user location (for professionals)"""
    db = get_database()
    
    user_lat = latitude if latitude is not None else current_user.get("latitude")
    user_lon = longitude if longitude is not None else current_user.get("longitude")
    
    if user_lat is None or user_lon is None:
        query = {"status": "active"}
        if current_user.get("city"):
            query["city"] = current_user["city"]
        if job_type:
            query["job_type"] = job_type
        
        # Get total count before limiting
        total_count = await db.jobs.count_documents(query)
        
        jobs_cursor = db.jobs.find(query).limit(limit)
        jobs = await jobs_cursor.to_list(length=limit)
        
        for job in jobs:
            job["id"] = str(job["_id"])
            del job["_id"]  # Remove ObjectId
        
        return {"jobs": jobs, "using_location": False, "count": total_count}
    
    query = {"status": "active"}
    
    if job_type:
        query["job_type"] = job_type
    
    jobs_cursor = db.jobs.find(query)
    all_jobs = await jobs_cursor.to_list(length=None)
    
    jobs_with_distance = []
    for job in all_jobs:
        if job.get("latitude") and job.get("longitude"):
            distance = calculate_distance(user_lat, user_lon, job["latitude"], job["longitude"])
        else:
            # Estimate distance based on city match
            distance = 0 if job.get("city") == current_user.get("city") else 999
        
        if distance <= radius_km:
            job["id"] = str(job["_id"])
            del job["_id"]  # Remove ObjectId
            job["distance_km"] = round(distance, 1) if distance < 999 else None
            jobs_with_distance.append(job)
    
    jobs_with_distance.sort(key=lambda x: x['distance_km'] if x['distance_km'] is not None else 999)
    
    return {
        "jobs": jobs_with_distance[:limit],
        "using_location": True,
        "user_location": {"latitude": user_lat, "longitude": user_lon},
        "count": len(jobs_with_distance)
    }


@router.get("/academies")
async def get_nearby_academies(
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    radius_km: float = Query(50, description="Search radius in kilometers"),
    sport: Optional[str] = None,
    city: Optional[str] = None,
    limit: int = Query(20, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    Get nearby sports academies.
    Reads from the `academies` collection which contains both:
      - Documents migrated from the old `dictionary` collection (with term/sport fields)
      - New documents created via POST /api/admin/academies/create (with name/sport_type)
    Both field variants are handled transparently.
    """
    db = get_database()

    user_lat = latitude if latitude is not None else current_user.get("latitude")
    user_lon = longitude if longitude is not None else current_user.get("longitude")

    # Build base query — works on both old and new field names
    query: dict = {"is_active": True}
    if sport:
        # sport_type (new) OR sport (old)
        query["$or"] = [
            {"sport_type": {"$regex": sport, "$options": "i"}},
            {"sport":      {"$regex": sport, "$options": "i"}},
        ]

    def _normalise(doc: dict) -> dict:
        """Ensure every response has consistent name/sport_type fields."""
        doc["id"] = str(doc["_id"]); del doc["_id"]
        # Back-fill display fields from aliases
        if not doc.get("name"):
            doc["name"] = doc.get("term", "")
        if not doc.get("sport_type"):
            doc["sport_type"] = doc.get("sport", "")
        if not doc.get("description"):
            defn = doc.get("definition", "")
            expl = doc.get("explanation", "")
            doc["description"] = f"{defn}. {expl}".strip(". ") if expl else defn
        return doc

    # ── No location available → fall back to city/all listing ────────────────
    if user_lat is None or user_lon is None:
        if city:
            query["city"] = {"$regex": city, "$options": "i"}
        elif current_user.get("city"):
            query["city"] = current_user["city"]

        total_count      = await db.academies.count_documents(query)
        academies_cursor = db.academies.find(query).sort("is_featured", -1).limit(limit)
        academies        = await academies_cursor.to_list(length=limit)
        academies        = [_normalise(a) for a in academies]

        return {
            "academies":     academies,
            "using_location": False,
            "count":         total_count,
        }

    # ── Location available → Haversine radius filter ──────────────────────────
    geo_query = {**query, "latitude": {"$ne": None}, "longitude": {"$ne": None}}
    all_docs  = await db.academies.find(geo_query).to_list(length=None)

    academies_with_distance = []
    for doc in all_docs:
        lat = doc.get("latitude")
        lon = doc.get("longitude")
        if lat is None or lon is None:
            continue
        distance = calculate_distance(user_lat, user_lon, lat, lon)
        if distance <= radius_km:
            doc = _normalise(doc)
            doc["distance_km"] = round(distance, 1)
            academies_with_distance.append(doc)

    academies_with_distance.sort(key=lambda x: x["distance_km"])
    result = academies_with_distance[:limit]

    return {
        "academies":     result,
        "using_location": True,
        "user_location":  {"latitude": user_lat, "longitude": user_lon},
        "count":         len(result),
    }


@router.get("/all")
async def get_all_nearby(
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    radius_km: float = Query(50, description="Search radius in kilometers"),
    current_user: dict = Depends(get_current_user)
):
    """Get counts of all nearby items"""
    # Get counts for all categories
    venues_result = await get_nearby_venues(latitude, longitude, radius_km, None, 100, current_user)
    tournaments_result = await get_nearby_tournaments(latitude, longitude, radius_km, None, 100, current_user)
    shops_result = await get_nearby_shops(latitude, longitude, radius_km, None, 100, current_user)
    jobs_result = await get_nearby_jobs(latitude, longitude, radius_km, None, 100, current_user)
    academies_result = await get_nearby_academies(latitude, longitude, radius_km, None, 100, current_user)
    
    return {
        "using_location": venues_result.get("using_location", False),
        "user_location": venues_result.get("user_location"),
        "radius_km": radius_km,
        "counts": {
            "venues": venues_result.get("count", len(venues_result.get("venues", []))),
            "tournaments": tournaments_result.get("count", len(tournaments_result.get("tournaments", []))),
            "shops": shops_result.get("count", len(shops_result.get("shops", []))),
            "jobs": jobs_result.get("count", len(jobs_result.get("jobs", []))),
            "academies": academies_result.get("count", len(academies_result.get("academies", [])))
        }
    }


# ── Public Academy Listing (no auth required) ─────────────────────────────────

@router.get("/academies/list")
async def list_all_academies(
    sport_type: Optional[str] = None,
    city: Optional[str] = None,
    search: Optional[str] = None,
    featured_only: bool = False,
    skip: int = 0,
    limit: int = Query(50, le=200),
):
    """
    Public endpoint to list/search all academies without requiring location.
    Returns academies from the `academies` collection with normalised fields
    (name, sport_type, description) so both old dictionary-seeded docs and
    new admin-created docs look identical to the Flutter app.
    """
    db    = get_database()
    query: dict = {"is_active": True}

    if sport_type:
        query["$or"] = [
            {"sport_type": {"$regex": sport_type, "$options": "i"}},
            {"sport":      {"$regex": sport_type, "$options": "i"}},
        ]
    if city:
        query["city"] = {"$regex": city, "$options": "i"}
    if search:
        search_or = [
            {"name":        {"$regex": search, "$options": "i"}},
            {"term":        {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"definition":  {"$regex": search, "$options": "i"}},
        ]
        if "$or" in query:
            # Already have a sport $or — wrap both in $and
            query = {"$and": [{"$or": query.pop("$or")}, {"$or": search_or}, query]}
        else:
            query["$or"] = search_or
    if featured_only:
        query["is_featured"] = True

    total = await db.academies.count_documents(query)
    cursor = db.academies.find(query).sort(
        [("is_featured", -1), ("rating", -1), ("views_count", -1)]
    ).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)

    result = []
    for doc in docs:
        doc["id"] = str(doc["_id"]); del doc["_id"]
        # Normalise field names
        if not doc.get("name"):
            doc["name"] = doc.get("term", "")
        if not doc.get("sport_type"):
            doc["sport_type"] = doc.get("sport", "")
        if not doc.get("description"):
            defn = doc.get("definition", "")
            expl = doc.get("explanation", "")
            doc["description"] = f"{defn}. {expl}".strip(". ") if expl else defn
        result.append(doc)

    return {
        "academies": result,
        "total":     total,
        "skip":      skip,
        "limit":     limit,
    }