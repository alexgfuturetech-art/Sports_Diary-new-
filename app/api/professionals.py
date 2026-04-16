from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
import uuid

from app.core.database import get_database
from app.core.security import get_current_user
from app.schemas.schemas import (
    ProfessionalAvailabilityCreate, ProfessionalAvailabilityUpdate, ProfessionalAvailabilityResponse,
    ProfessionalBookingCreate, ProfessionalBookingUpdate, ProfessionalBookingResponse
)

router = APIRouter(tags=["professionals"])


# ==================== PROFESSIONAL AVAILABILITY ENDPOINTS ====================

@router.post("/availability")
async def create_availability(
    availability_data: ProfessionalAvailabilityCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create professional availability for matches"""
    db = get_database()
    
    # Allow both professionals and players to create availability
    if current_user.get("role") not in ["professional", "player"]:
        raise HTTPException(status_code=403, detail="Only professionals and players can create availability")
    
    availability_dict = availability_data.dict()
    availability_dict["professional_id"] = str(current_user["_id"])
    availability_dict["professional_name"] = current_user.get("name", "Professional")
    availability_dict["professional_type"] = current_user.get("professional_type", "")
    availability_dict["city"] = current_user.get("city", "")
    availability_dict["state"] = current_user.get("state", "Gujarat")
    availability_dict["latitude"] = current_user.get("latitude")
    availability_dict["longitude"] = current_user.get("longitude")
    availability_dict["created_at"] = datetime.utcnow()
    availability_dict["updated_at"] = datetime.utcnow()
    availability_dict["rating"] = 0.0
    availability_dict["total_bookings"] = 0
    availability_dict["total_reviews"] = 0
    availability_dict["is_active"] = True
    availability_dict["is_verified"] = False
    
    result = await db.professional_availability.insert_one(availability_dict)
    created = await db.professional_availability.find_one({"_id": result.inserted_id})
    created["id"] = str(created["_id"])
    del created["_id"]
    
    return created


@router.get("/availability")
async def get_my_availability(
    current_user: dict = Depends(get_current_user)
):
    """Get current user's professional availability"""
    db = get_database()
    
    # Allow both professionals and players to view their availability
    if current_user.get("role") not in ["professional", "player"]:
        raise HTTPException(status_code=403, detail="Only professionals and players can view availability")
    
    availability_cursor = db.professional_availability.find({
        "professional_id": str(current_user["_id"])
    }).sort([("created_at", -1)])
    
    availabilities = await availability_cursor.to_list(length=None)
    
    for avail in availabilities:
        avail["id"] = str(avail["_id"])
        del avail["_id"]
    
    return availabilities


@router.get("/availability/search")
async def search_professionals(
    sport_type: Optional[str] = None,
    city: Optional[str] = None,
    professional_type: Optional[str] = None,
    can_play: Optional[bool] = None,
    can_coach: Optional[bool] = None,
    can_umpire: Optional[bool] = None,
    max_fee: Optional[float] = None,
    skip: int = 0,
    limit: int = 50
):
    """Search for available professionals"""
    db = get_database()
    
    # Get current time
    now = datetime.utcnow()
    
    # Query for active professionals with valid availability
    query = {
        "is_active": True,
        "$or": [
            # Available until date is None (no end date) OR in the future
            {"available_to_date": None},
            {"available_to_date": {"$gte": now}}
        ]
    }
    
    if sport_type:
        query["sport_type"] = sport_type
    if city:
        query["city"] = city
    if professional_type:
        query["professional_type"] = professional_type
    if can_play is not None:
        query["can_play"] = can_play
    if can_coach is not None:
        query["can_coach"] = can_coach
    if can_umpire is not None:
        query["can_umpire"] = can_umpire
    if max_fee is not None:
        query["per_match_fee"] = {"$lte": max_fee}
    
    print(f"[SEARCH] Query: {query}")
    
    professionals_cursor = db.professional_availability.find(query).skip(skip).limit(limit).sort([
        ("rating", -1),
        ("total_bookings", -1)
    ])
    
    professionals = await professionals_cursor.to_list(length=limit)

    print(f"[SEARCH] Found {len(professionals)} professionals")

    # Batch-fetch user profiles to embed avatar, bio, experience_years
    if professionals:
        user_ids = []
        for p in professionals:
            try:
                user_ids.append(ObjectId(p["professional_id"]))
            except Exception:
                pass
        if user_ids:
            users_cursor = db.users.find(
                {"_id": {"$in": user_ids}},
                {"_id": 1, "avatar": 1, "bio": 1, "experience_years": 1},
            )
            user_map = {str(u["_id"]): u async for u in users_cursor}
        else:
            user_map = {}
    else:
        user_map = {}

    for prof in professionals:
        prof["id"] = str(prof["_id"])
        del prof["_id"]
        u = user_map.get(prof.get("professional_id", ""), {})
        prof["avatar"] = u.get("avatar") or prof.get("avatar")
        prof["bio"] = u.get("bio") or prof.get("bio")
        prof["experience_years"] = u.get("experience_years") or prof.get("experience_years")

    return professionals


@router.get("/availability/{availability_id}/booked-dates")
async def get_booked_dates(availability_id: str):
    """
    Public endpoint — returns the list of match dates that already have a
    confirmed or pending booking for this availability slot.
    The Flutter calendar uses this to grey-out / mark dates as 'Slot Booked'.
    """
    db = get_database()

    # Validate ID format early so we return 400 instead of an empty list
    try:
        ObjectId(availability_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid availability ID")

    cursor = db.professional_bookings.find(
        {
            "professional_id": availability_id,
            "status": {"$in": ["confirmed", "pending"]},
        },
        {"match_date": 1, "_id": 0},
    )
    bookings = await cursor.to_list(length=500)

    # match_date is stored as a BSON datetime (Python datetime object).
    # Convert to "YYYY-MM-DD" string regardless of whether it comes back as
    # a datetime object or a legacy ISO string.
    def _to_date_str(val) -> str | None:
        if val is None:
            return None
        if hasattr(val, "strftime"):          # datetime / date object
            return val.strftime("%Y-%m-%d")
        return str(val)[:10]                  # fallback: ISO string slice

    booked_dates = sorted({
        s for b in bookings
        if (s := _to_date_str(b.get("match_date"))) is not None
    })

    return {"booked_dates": booked_dates}


@router.get("/availability/{availability_id}")
async def get_availability(availability_id: str):
    """Get professional availability details"""
    db = get_database()
    
    try:
        availability = await db.professional_availability.find_one({"_id": ObjectId(availability_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid availability ID")
    
    if not availability:
        raise HTTPException(status_code=404, detail="Availability not found")
    
    availability["id"] = str(availability["_id"])
    del availability["_id"]
    
    return availability


@router.put("/availability/{availability_id}")
async def update_availability(
    availability_id: str,
    availability_data: ProfessionalAvailabilityUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update professional availability"""
    db = get_database()
    
    try:
        availability = await db.professional_availability.find_one({"_id": ObjectId(availability_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid availability ID")
    
    if not availability:
        raise HTTPException(status_code=404, detail="Availability not found")
    
    # Check authorization
    if str(availability["professional_id"]) != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {k: v for k, v in availability_data.dict(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.professional_availability.update_one(
        {"_id": ObjectId(availability_id)},
        {"$set": update_data}
    )
    
    updated = await db.professional_availability.find_one({"_id": ObjectId(availability_id)})
    updated["id"] = str(updated["_id"])
    del updated["_id"]
    
    return updated


@router.delete("/availability/{availability_id}")
async def delete_availability(
    availability_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete professional availability"""
    db = get_database()
    
    try:
        availability = await db.professional_availability.find_one({"_id": ObjectId(availability_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid availability ID")
    
    if not availability:
        raise HTTPException(status_code=404, detail="Availability not found")
    
    # Check authorization
    if str(availability["professional_id"]) != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.professional_availability.delete_one({"_id": ObjectId(availability_id)})
    
    return {"message": "Availability deleted successfully"}


# ==================== PROFESSIONAL BOOKING ENDPOINTS ====================

@router.post("/bookings")
async def create_booking(
    booking_data: ProfessionalBookingCreate,
    current_user: dict = Depends(get_current_user)
):
    """Book a professional for a match"""
    db = get_database()
    
    # Get professional availability
    try:
        availability = await db.professional_availability.find_one({
            "_id": ObjectId(booking_data.professional_id)
        })
    except:
        raise HTTPException(status_code=400, detail="Invalid professional ID")
    
    if not availability:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    # Check if professional is available
    if not availability.get("is_active"):
        raise HTTPException(status_code=400, detail="Professional is not available")
    
    # Check for duplicate umpire booking in same tournament
    if booking_data.tournament_id and booking_data.role == "Umpire":
        existing_booking = await db.professional_bookings.find_one({
            "tournament_id": booking_data.tournament_id,
            "professional_id": booking_data.professional_id,
            "role": "Umpire",
            "status": {"$in": ["confirmed", "accepted"]}
        })
        
        if existing_booking:
            raise HTTPException(
                status_code=400, 
                detail=f"This umpire is already booked for this tournament. Booking ID: {existing_booking.get('booking_number', 'N/A')}"
            )
    
    # Generate booking number
    booking_number = f"PROF-{uuid.uuid4().hex[:8].upper()}"
    
    booking_dict = booking_data.dict()
    booking_dict["booking_number"] = booking_number
    booking_dict["booked_by"] = str(current_user["_id"])
    booking_dict["professional_id"] = booking_data.professional_id
    booking_dict["per_match_fee"] = availability.get("per_match_fee", 0)
    booking_dict["total_amount"] = availability.get("per_match_fee", 0)
    booking_dict["currency"] = availability.get("currency", "INR")
    booking_dict["payment_status"] = "pending"
    booking_dict["status"] = "confirmed"
    booking_dict["created_at"] = datetime.utcnow()
    booking_dict["updated_at"] = datetime.utcnow()
    
    result = await db.professional_bookings.insert_one(booking_dict)
    created = await db.professional_bookings.find_one({"_id": result.inserted_id})
    created["id"] = str(created["_id"])
    del created["_id"]
    
    # Update professional's total bookings
    await db.professional_availability.update_one(
        {"_id": ObjectId(booking_data.professional_id)},
        {"$inc": {"total_bookings": 1}}
    )
    
    return created


@router.get("/bookings")
async def get_my_bookings(
    current_user: dict = Depends(get_current_user),
    role: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    """Get bookings for current user (as professional or as booker)"""
    db = get_database()
    
    if role == "professional":
        # professional_id on bookings stores the availability slot _id, not the user id.
        # Two-step: find all slot ids owned by this user, then filter bookings by those ids.
        slot_ids = await db.professional_availability.distinct(
            "_id", {"professional_id": str(current_user["_id"])}
        )
        slot_id_strs = [str(s) for s in slot_ids]
        query = {"professional_id": {"$in": slot_id_strs}}
    else:
        # Get bookings where user is the one who booked
        query = {"booked_by": str(current_user["_id"])}
    
    bookings_cursor = db.professional_bookings.find(query).skip(skip).limit(limit).sort([
        ("match_date", 1)
    ])
    
    bookings = await bookings_cursor.to_list(length=limit)
    
    for booking in bookings:
        booking["id"] = str(booking["_id"])
        del booking["_id"]
    
    return bookings


@router.get("/bookings/check-duplicate/{tournament_id}/{professional_id}")
async def check_duplicate_umpire(
    tournament_id: str,
    professional_id: str,
    role: str = "Umpire"
):
    """Check if an umpire is already booked for a tournament"""
    db = get_database()
    
    try:
        existing_booking = await db.professional_bookings.find_one({
            "tournament_id": tournament_id,
            "professional_id": professional_id,
            "role": role,
            "status": {"$in": ["confirmed", "accepted"]}
        })
        
        return {
            "is_booked": existing_booking is not None,
            "booking_number": existing_booking.get("booking_number") if existing_booking else None,
            "message": f"This {role.lower()} is already booked for this tournament" if existing_booking else None
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/bookings/{booking_id}")
async def get_booking(booking_id: str):
    """Get booking details"""
    db = get_database()
    
    try:
        booking = await db.professional_bookings.find_one({"_id": ObjectId(booking_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid booking ID")
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking["id"] = str(booking["_id"])
    del booking["_id"]
    
    return booking


@router.put("/bookings/{booking_id}")
async def update_booking(
    booking_id: str,
    booking_data: ProfessionalBookingUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update booking status"""
    db = get_database()
    
    try:
        booking = await db.professional_bookings.find_one({"_id": ObjectId(booking_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid booking ID")
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check authorization.
    # booking.professional_id stores an availability slot _id, not a user id,
    # so we must look up the slot to identify the owning professional.
    user_id = str(current_user["_id"])
    is_organizer = str(booking.get("booked_by", "")) == user_id

    is_professional = False
    slot_id = booking.get("professional_id")
    if slot_id:
        try:
            slot = await db.professional_availability.find_one({"_id": ObjectId(slot_id)})
            if slot and str(slot.get("professional_id", "")) == user_id:
                is_professional = True
        except Exception:
            pass

    if not (is_organizer or is_professional):
        raise HTTPException(status_code=403, detail="Not authorized")

    # Per-role status restrictions
    new_status = booking_data.status
    if new_status:
        if is_professional and not is_organizer and new_status not in ("confirmed", "rejected"):
            raise HTTPException(status_code=403, detail="Professional can only confirm or reject bookings")
        if is_organizer and not is_professional and new_status not in ("cancelled",):
            raise HTTPException(status_code=403, detail="Organizer can only cancel bookings")

    update_data = {k: v for k, v in booking_data.dict(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()

    if booking_data.status == "cancelled":
        update_data["cancelled_at"] = datetime.utcnow()
    
    await db.professional_bookings.update_one(
        {"_id": ObjectId(booking_id)},
        {"$set": update_data}
    )
    
    updated = await db.professional_bookings.find_one({"_id": ObjectId(booking_id)})
    updated["id"] = str(updated["_id"])
    del updated["_id"]
    
    return updated


@router.delete("/bookings/{booking_id}")
async def cancel_booking(
    booking_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel a booking"""
    db = get_database()
    
    try:
        booking = await db.professional_bookings.find_one({"_id": ObjectId(booking_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid booking ID")
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check authorization
    if (str(booking["professional_id"]) != str(current_user["_id"]) and 
        str(booking["booked_by"]) != str(current_user["_id"])):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.professional_bookings.update_one(
        {"_id": ObjectId(booking_id)},
        {"$set": {
            "status": "cancelled",
            "cancelled_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }}
    )
    
    return {"message": "Booking cancelled successfully"}
