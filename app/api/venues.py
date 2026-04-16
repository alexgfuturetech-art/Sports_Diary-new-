from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
import math

from app.core.database import get_database
from app.core.security import get_current_user
from app.schemas.schemas import (
    VenueCreate, VenueUpdate, VenueResponse,
    BookingCreate, BookingResponse, SplitPaymentRequest,
    ReviewCreate, ReviewResponse
)

router = APIRouter()

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in kilometers using Haversine formula"""
    R = 6371  # Earth's radius in kilometers
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

@router.get("")
async def get_venues(
    city: Optional[str] = None,
    sport: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    amenities: Optional[str] = Query(None),
    indoor_outdoor: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: Optional[float] = 10.0,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    """
    Smart Search & Filter Venues
    - Search by sport, location, price range
    - Filter by amenities, rating, indoor/outdoor
    - Nearby search using lat/long
    """
    db = get_database()
    
    # Build MongoDB query
    query = {"is_active": True}
    
    # City filter
    if city:
        query["city"] = city
    
    # Sport filter
    if sport:
        query["sports_available"] = sport
    
    # Price range filter
    if min_price:
        query["price_per_hour"] = query.get("price_per_hour", {})
        query["price_per_hour"]["$gte"] = min_price
    if max_price:
        query["price_per_hour"] = query.get("price_per_hour", {})
        query["price_per_hour"]["$lte"] = max_price
    
    # Rating filter
    if min_rating:
        query["rating"] = {"$gte": min_rating}
    
    # Amenities filter
    if amenities:
        amenity_list = [a.strip() for a in amenities.split(',')]
        query["amenities"] = {"$all": amenity_list}
    
    # Indoor/Outdoor filter
    if indoor_outdoor:
        query["indoor_outdoor"] = indoor_outdoor
    
    # Search by name, description, landmark
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"landmark": {"$regex": search, "$options": "i"}}
        ]
    
    # Nearby search
    if latitude and longitude:
        query["latitude"] = {"$ne": None}
        query["longitude"] = {"$ne": None}
    
    # Get total count before limiting
    total_count = await db.venues.count_documents(query)
    
    # Execute query
    venues_cursor = db.venues.find(query).skip(skip).limit(limit)
    venues = await venues_cursor.to_list(length=limit)
    
    # Calculate distance if coordinates provided
    if latitude and longitude:
        for venue in venues:
            if venue.get("latitude") and venue.get("longitude"):
                distance = calculate_distance(
                    latitude, longitude,
                    venue["latitude"], venue["longitude"]
                )
                venue["distance_km"] = round(distance, 2)
            else:
                venue["distance_km"] = None
        
        # Filter by radius
        venues = [v for v in venues if v.get("distance_km") is not None and v["distance_km"] <= radius_km]
        
        # Sort by distance
        venues.sort(key=lambda x: x.get("distance_km", float('inf')))
    
    # Convert ObjectId to string
    for venue in venues:
        venue["id"] = str(venue["_id"])
        del venue["_id"]  # Remove ObjectId
    
    return {"venues": venues, "count": total_count}

@router.get("/{venue_id}")
async def get_venue(venue_id: str):
    """Get venue by ID"""
    db = get_database()
    
    try:
        venue = await db.venues.find_one({"_id": ObjectId(venue_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid venue ID")
    
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    venue["id"] = str(venue["_id"])
    del venue["_id"]  # Remove ObjectId
    return venue

@router.post("")
async def create_venue(
    venue: VenueCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create new venue"""
    db = get_database()
    
    venue_data = venue.dict()
    venue_data["owner_id"] = str(current_user["_id"])
    venue_data["created_at"] = datetime.utcnow()
    venue_data["updated_at"] = datetime.utcnow()
    venue_data["is_active"] = True
    venue_data["rating"] = 0.0
    venue_data["total_reviews"] = 0
    venue_data["total_bookings"] = 0
    
    result = await db.venues.insert_one(venue_data)
    created_venue = await db.venues.find_one({"_id": result.inserted_id})
    created_venue["id"] = str(created_venue["_id"])

    del created_venue["_id"]  # Remove ObjectId
    
    return created_venue

@router.put("/{venue_id}")
async def update_venue(
    venue_id: str,
    venue: VenueUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update venue"""
    db = get_database()
    
    try:
        existing_venue = await db.venues.find_one({"_id": ObjectId(venue_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid venue ID")
    
    if not existing_venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    # Check ownership
    if str(existing_venue.get("owner_id")) != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {k: v for k, v in venue.dict(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.venues.update_one(
        {"_id": ObjectId(venue_id)},
        {"$set": update_data}
    )
    
    updated_venue = await db.venues.find_one({"_id": ObjectId(venue_id)})
    updated_venue["id"] = str(updated_venue["_id"])

    del updated_venue["_id"]  # Remove ObjectId
    
    return updated_venue

@router.delete("/{venue_id}")
async def delete_venue(
    venue_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete/deactivate venue"""
    db = get_database()
    
    try:
        venue = await db.venues.find_one({"_id": ObjectId(venue_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid venue ID")
    
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    # Check ownership
    if str(venue.get("owner_id")) != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Soft delete
    await db.venues.update_one(
        {"_id": ObjectId(venue_id)},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Venue deleted successfully"}

# Bookings endpoints
@router.post("/bookings")
async def create_booking(
    booking: BookingCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create venue booking"""
    db = get_database()
    
    # Verify venue exists
    try:
        venue = await db.venues.find_one({"_id": ObjectId(booking.venue_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid venue ID")
    
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    # Generate booking number
    booking_count = await db.bookings.count_documents({})
    booking_number = f"BK-{datetime.now().strftime('%Y%m%d')}-{booking_count + 1:04d}"
    
    booking_data = booking.dict()
    booking_data["user_id"] = str(current_user["_id"])
    booking_data["booking_number"] = booking_number
    booking_data["created_at"] = datetime.utcnow()
    booking_data["updated_at"] = datetime.utcnow()
    booking_data["status"] = "confirmed"
    booking_data["payment_status"] = "pending"
    
    result = await db.bookings.insert_one(booking_data)
    
    # Update venue booking count
    await db.venues.update_one(
        {"_id": ObjectId(booking.venue_id)},
        {"$inc": {"total_bookings": 1}}
    )
    
    created_booking = await db.bookings.find_one({"_id": result.inserted_id})
    created_booking["id"] = str(created_booking["_id"])

    del created_booking["_id"]  # Remove ObjectId
    
    return created_booking

@router.get("/bookings")
async def get_user_bookings(
    current_user: dict = Depends(get_current_user),
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    """Get user's bookings"""
    db = get_database()
    
    query = {"user_id": str(current_user["_id"])}
    
    if status:
        query["status"] = status
    
    bookings_cursor = db.bookings.find(query).skip(skip).limit(limit).sort("created_at", -1)
    bookings = await bookings_cursor.to_list(length=limit)
    
    for booking in bookings:
        booking["id"] = str(booking["_id"])

        del booking["_id"]  # Remove ObjectId
    
    return bookings

@router.get("/bookings/{booking_id}")
async def get_booking(
    booking_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get booking by ID"""
    db = get_database()
    
    try:
        booking = await db.bookings.find_one({"_id": ObjectId(booking_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid booking ID")
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check if user owns this booking or owns the venue
    venue = await db.venues.find_one({"_id": ObjectId(booking["venue_id"])})
    
    if (str(booking["user_id"]) != str(current_user["_id"]) and 
        (not venue or str(venue.get("owner_id")) != str(current_user["_id"]))):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    booking["id"] = str(booking["_id"])

    
    del booking["_id"]  # Remove ObjectId
    return booking

@router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(
    booking_id: str,
    current_user: dict = Depends(get_current_user),
    reason: Optional[str] = None
):
    """Cancel booking"""
    db = get_database()
    
    try:
        booking = await db.bookings.find_one({"_id": ObjectId(booking_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid booking ID")
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if str(booking["user_id"]) != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.bookings.update_one(
        {"_id": ObjectId(booking_id)},
        {"$set": {
            "status": "cancelled",
            "cancellation_reason": reason,
            "cancelled_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }}
    )
    
    return {"message": "Booking cancelled successfully"}

# Reviews endpoints
@router.post("/{venue_id}/reviews")
async def create_review(
    venue_id: str,
    review: ReviewCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create venue review"""
    db = get_database()
    
    try:
        venue = await db.venues.find_one({"_id": ObjectId(venue_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid venue ID")
    
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    review_data = review.dict()
    review_data["venue_id"] = venue_id
    review_data["user_id"] = str(current_user["_id"])
    review_data["created_at"] = datetime.utcnow()
    review_data["updated_at"] = datetime.utcnow()
    review_data["is_verified"] = False
    review_data["helpful_count"] = 0
    
    result = await db.venue_reviews.insert_one(review_data)
    
    # Update venue rating
    reviews_cursor = db.venue_reviews.find({"venue_id": venue_id})
    reviews = await reviews_cursor.to_list(length=None)
    
    if reviews:
        avg_rating = sum(r["rating"] for r in reviews) / len(reviews)
        await db.venues.update_one(
            {"_id": ObjectId(venue_id)},
            {"$set": {
                "rating": round(avg_rating, 2),
                "total_reviews": len(reviews)
            }}
        )
    
    created_review = await db.venue_reviews.find_one({"_id": result.inserted_id})
    created_review["id"] = str(created_review["_id"])

    del created_review["_id"]  # Remove ObjectId
    
    return created_review

@router.get("/{venue_id}/reviews")
async def get_venue_reviews(
    venue_id: str,
    skip: int = 0,
    limit: int = 20
):
    """Get venue reviews"""
    db = get_database()
    
    reviews_cursor = db.venue_reviews.find({"venue_id": venue_id}).skip(skip).limit(limit).sort("created_at", -1)
    reviews = await reviews_cursor.to_list(length=limit)
    
    for review in reviews:
        review["id"] = str(review["_id"])

        del review["_id"]  # Remove ObjectId
    
    return reviews

