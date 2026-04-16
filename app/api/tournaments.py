from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel

from app.core.database import get_database
from app.core.security import get_current_user
from app.schemas.schemas import (
    TournamentCreate, TournamentUpdate, TournamentResponse,
    TeamCreate, TeamUpdate, TeamResponse,
    TournamentRegistrationCreate, TournamentRegistrationUpdate, TournamentRegistrationResponse,
    MatchCreate, MatchUpdate,
)

router = APIRouter(tags=["tournaments"])


# ==================== TOURNAMENT ENDPOINTS ====================

@router.get("")
async def get_tournaments(
    city: Optional[str] = None,
    sport_type: Optional[str] = None,
    status: Optional[str] = None,
    age_category: Optional[str] = None,
    gender_category: Optional[str] = None,
    skill_level: Optional[str] = None,
    entry_fee_min: Optional[float] = None,
    entry_fee_max: Optional[float] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    """Get list of tournaments with filters"""
    db = get_database()

    query = {"is_active": True}

    if city:
        query["city"] = city
    if sport_type:
        query["sport_type"] = sport_type
    if status:
        query["status"] = status
    if age_category:
        query["age_category"] = age_category
    if gender_category:
        query["gender_category"] = gender_category
    if skill_level:
        query["skill_level"] = skill_level
    if entry_fee_min is not None or entry_fee_max is not None:
        fee_filter = {}
        if entry_fee_min is not None:
            fee_filter["$gte"] = entry_fee_min
        if entry_fee_max is not None:
            fee_filter["$lte"] = entry_fee_max
        query["entry_fee"] = fee_filter
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    # Get total count before limiting
    total_count = await db.tournaments.count_documents(query)
    
    tournaments_cursor = db.tournaments.find(query).skip(skip).limit(limit).sort([("is_featured", -1), ("start_date", 1)])
    tournaments = await tournaments_cursor.to_list(length=limit)
    
    for tournament in tournaments:
        tournament["id"] = str(tournament["_id"])
        del tournament["_id"]  # Remove ObjectId
    
    return {"tournaments": tournaments, "count": total_count}


@router.get("/{tournament_id}")
async def get_tournament(tournament_id: str):
    """Get tournament details"""
    db = get_database()
    
    try:
        tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid tournament ID")
    
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Increment views count
    await db.tournaments.update_one(
        {"_id": ObjectId(tournament_id)},
        {"$inc": {"views_count": 1}}
    )
    
    tournament["id"] = str(tournament["_id"])
    
    # Fetch organizer details
    organizer_id = tournament.get("organizer_id")
    if organizer_id:
        try:
            organizer = await db.users.find_one({"_id": ObjectId(organizer_id)})
            if organizer:
                tournament["organizer"] = {
                    "id": str(organizer["_id"]),
                    "name": organizer.get("name", "Anonymous"),
                    "email": organizer.get("email"),
                    "role": organizer.get("role"),
                    "professional_type": organizer.get("professional_type"),
                    "city": organizer.get("city"),
                    "state": organizer.get("state"),
                    "bio": organizer.get("bio"),
                    "avatar": organizer.get("avatar"),
                    "is_verified": organizer.get("is_verified", False)
                }
        except:
            # If organizer fetch fails, just continue without organizer data
            pass
    
    del tournament["_id"]  # Remove ObjectId
    return tournament


@router.post("")
async def create_tournament(
    tournament_data: TournamentCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create new tournament (any authenticated user can create)"""
    db = get_database()
    
    user_id = str(current_user["_id"])
    organizer_id = user_id
    created_by_manager = False
    user_role = current_user.get("role", "player")
    
    print(f"[CREATE_TOURNAMENT] User creating tournament:")
    print(f"  - User ID: {user_id}")
    print(f"  - User Role: {user_role}")
    print(f"  - Tournament Name: {tournament_data.name}")
    
    # If user is not an organizer, check if they're a manager
    if user_role != "organizer":
        # Check if user is a manager
        manager = await db.organizer_managers.find_one({
            "manager_user_id": user_id,
            "is_active": True
        })
        
        if manager:
            # User is a manager - check permission
            permissions = manager.get("permissions", [])
            if "create_tournament" not in permissions:
                print(f"[CREATE_TOURNAMENT] Manager lacks create_tournament permission - DENIED")
                raise HTTPException(status_code=403, detail="You don't have permission to create tournaments")
            
            organizer_id = str(manager["organizer_id"])
            created_by_manager = True
            print(f"[CREATE_TOURNAMENT] User is manager for organizer: {organizer_id}")
        else:
            # User is not an organizer or manager - they can still create as themselves
            print(f"[CREATE_TOURNAMENT] User is {user_role} - creating as individual organizer")
            # User becomes their own organizer
            organizer_id = user_id
    
    tournament_dict = tournament_data.dict()
    tournament_dict["organizer_id"] = organizer_id
    tournament_dict["created_by"] = user_id
    tournament_dict["created_by_manager"] = created_by_manager
    tournament_dict["created_at"] = datetime.utcnow()
    tournament_dict["updated_at"] = datetime.utcnow()
    tournament_dict["current_teams"] = 0
    tournament_dict["views_count"] = 0
    tournament_dict["is_active"] = True
    tournament_dict["status"] = "upcoming"
    
    result = await db.tournaments.insert_one(tournament_dict)
    created_tournament = await db.tournaments.find_one({"_id": result.inserted_id})
    created_tournament["id"] = str(created_tournament["_id"])

    del created_tournament["_id"]  # Remove ObjectId
    
    print(f"[CREATE_TOURNAMENT] Tournament created successfully: {created_tournament['id']}")
    
    return created_tournament


@router.put("/{tournament_id}")
async def update_tournament(
    tournament_id: str,
    tournament_data: TournamentUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update tournament (organizers and their managers)"""
    db = get_database()
    
    try:
        tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid tournament ID")
    
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    user_id = str(current_user["_id"])
    tournament_org_id = str(tournament["organizer_id"])
    
    print(f"[UPDATE_TOURNAMENT] Permission check:")
    print(f"  - User ID: {user_id}")
    print(f"  - Tournament Organizer ID: {tournament_org_id}")
    print(f"  - Is Main Organizer: {user_id == tournament_org_id}")
    
    # Check if user is the organizer
    if user_id == tournament_org_id:
        # Organizer has full access
        print(f"[UPDATE_TOURNAMENT] User is main organizer - ALLOWED")
        pass
    else:
        # Check if user is a manager with permission
        print(f"[UPDATE_TOURNAMENT] Checking manager permissions...")
        
        manager = await db.organizer_managers.find_one({
            "manager_user_id": user_id,
            "organizer_id": tournament_org_id,
            "is_active": True
        })
        
        print(f"[UPDATE_TOURNAMENT] Manager found: {manager is not None}")
        
        if not manager:
            # Try alternative query with ObjectId
            try:
                manager = await db.organizer_managers.find_one({
                    "manager_user_id": user_id,
                    "organizer_id": ObjectId(tournament_org_id),
                    "is_active": True
                })
                print(f"[UPDATE_TOURNAMENT] Manager found (ObjectId query): {manager is not None}")
            except:
                pass
        
        if not manager:
            print(f"[UPDATE_TOURNAMENT] No manager record found - DENIED")
            raise HTTPException(status_code=403, detail="Not authorized to edit this tournament")
        
        # Check permission
        permissions = manager.get("permissions", [])
        print(f"[UPDATE_TOURNAMENT] Manager permissions: {permissions}")
        
        if "edit_tournament" not in permissions:
            print(f"[UPDATE_TOURNAMENT] Missing edit_tournament permission - DENIED")
            raise HTTPException(status_code=403, detail="You don't have permission to edit tournaments")
        
        print(f"[UPDATE_TOURNAMENT] Manager has edit_tournament permission - ALLOWED")
    
    # ── Status transition guard ────────────────────────────────────────────
    _VALID_TRANSITIONS: dict = {
        "upcoming":            {"registration_closed", "ongoing", "cancelled", "postponed"},
        "registration_closed": {"ongoing", "cancelled", "postponed"},
        "postponed":           {"upcoming", "registration_closed", "ongoing", "cancelled"},
        "ongoing":             {"completed", "cancelled"},
        "completed":           set(),   # terminal
        "cancelled":           set(),   # terminal
    }
    new_status = tournament_data.status
    if new_status:
        current_status = tournament.get("status", "upcoming")
        allowed = _VALID_TRANSITIONS.get(current_status, set())
        user_roles = current_user.get("roles", [])
        is_admin = any(r in user_roles for r in ("admin", "super_admin"))
        if not is_admin and new_status not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status transition: {current_status!r} → {new_status!r}"
            )

    update_data = {k: v for k, v in tournament_data.dict(exclude_unset=True).items() if v is not None}

    # Auto-stamp cancelled_at when status first moves to 'cancelled'
    if new_status == "cancelled" and "cancelled_at" not in update_data:
        update_data["cancelled_at"] = datetime.utcnow()

    update_data["updated_at"] = datetime.utcnow()

    await db.tournaments.update_one(
        {"_id": ObjectId(tournament_id)},
        {"$set": update_data}
    )

    updated_tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    updated_tournament["id"] = str(updated_tournament["_id"])

    del updated_tournament["_id"]  # Remove ObjectId
    
    return updated_tournament


@router.delete("/{tournament_id}")
async def delete_tournament(
    tournament_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete/deactivate tournament (organizers and their managers)"""
    db = get_database()
    
    try:
        tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid tournament ID")
    
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    user_id = str(current_user["_id"])
    
    # Check if user is the organizer
    if str(tournament["organizer_id"]) == user_id:
        # Organizer has full access
        pass
    else:
        # Check if user is a manager with permission
        manager = await db.organizer_managers.find_one({
            "manager_user_id": user_id,
            "organizer_id": str(tournament["organizer_id"]),
            "is_active": True
        })
        
        if not manager:
            raise HTTPException(status_code=403, detail="Not authorized to delete this tournament")
        
        # Check permission
        permissions = manager.get("permissions", [])
        if "edit_tournament" not in permissions:  # Using edit permission for delete
            raise HTTPException(status_code=403, detail="You don't have permission to delete tournaments")
    
    # Soft delete
    await db.tournaments.update_one(
        {"_id": ObjectId(tournament_id)},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Tournament deleted successfully"}


# ==================== TEAM ENDPOINTS ====================

@router.post("/teams")
async def create_team(
    team_data: TeamCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create new team"""
    db = get_database()
    try:
        team_dict = team_data.dict()
        team_dict["captain_id"] = str(current_user["_id"])
        team_dict["created_at"] = datetime.utcnow()
        team_dict["updated_at"] = datetime.utcnow()
        team_dict["total_players"] = len(team_dict.get("players") or [])
        team_dict["matches_played"] = 0
        team_dict["matches_won"] = 0
        team_dict["matches_lost"] = 0
        team_dict["matches_drawn"] = 0
        team_dict["is_active"] = True
        team_dict["is_verified"] = False

        result = await db.teams.insert_one(team_dict)
        created_team = await db.teams.find_one({"_id": result.inserted_id})

        if not created_team:
            raise HTTPException(status_code=500, detail="Failed to retrieve created team")

        created_team["id"] = str(created_team["_id"])
        del created_team["_id"]

        # Ensure ObjectId fields are serialized as strings
        for key in ["captain_id", "tournament_id"]:
            if created_team.get(key) is not None:
                created_team[key] = str(created_team[key])

        return created_team

    except HTTPException:
        raise
    except Exception as e:
        print(f"[TEAMS] Error creating team: {e}")
        raise HTTPException(status_code=500, detail=f"Team creation failed: {str(e)}")


@router.get("/teams")
async def get_user_teams(
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50
):
    """Get user's teams (teams where user is captain)"""
    db = get_database()
    
    try:
        user_id = str(current_user["_id"])
        
        # Find teams where user is captain
        teams_cursor = db.teams.find({"captain_id": user_id}).skip(skip).limit(limit)
        teams = await teams_cursor.to_list(length=limit)
        
        for team in teams:
            team["id"] = str(team["_id"])
            del team["_id"]
        
        print(f"[TOURNAMENTS] Found {len(teams)} teams for user {user_id}")
        return teams
    except Exception as e:
        print(f"[TOURNAMENTS] Error fetching teams: {e}")
        # Return empty list if there's any error
        return []


@router.get("/teams/{team_id}")
async def get_team(team_id: str):
    """Get team details"""
    db = get_database()
    
    try:
        team = await db.teams.find_one({"_id": ObjectId(team_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid team ID")
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    team["id"] = str(team["_id"])

    
    del team["_id"]  # Remove ObjectId
    return team


@router.put("/teams/{team_id}")
async def update_team(
    team_id: str,
    team_data: TeamUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update team"""
    db = get_database()
    
    try:
        team = await db.teams.find_one({"_id": ObjectId(team_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid team ID")
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check if user is captain
    if str(team["captain_id"]) != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {k: v for k, v in team_data.dict(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    # Update total_players if players list is updated
    if "players" in update_data:
        update_data["total_players"] = len(update_data["players"])
    
    await db.teams.update_one(
        {"_id": ObjectId(team_id)},
        {"$set": update_data}
    )
    
    updated_team = await db.teams.find_one({"_id": ObjectId(team_id)})
    updated_team["id"] = str(updated_team["_id"])

    del updated_team["_id"]  # Remove ObjectId
    
    return updated_team


# ==================== TOURNAMENT REGISTRATION ENDPOINTS ====================

@router.post("/{tournament_id}/register")
async def register_team(
    tournament_id: str,
    registration_data: TournamentRegistrationCreate,
    current_user: dict = Depends(get_current_user)
):
    """Register team for tournament"""
    db = get_database()
    
    # Verify tournament exists
    try:
        tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid tournament ID")
    
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Check if tournament is accepting registrations
    if tournament["current_teams"] >= tournament["max_teams"]:
        raise HTTPException(status_code=400, detail="Tournament is full")
    
    # Verify team exists
    try:
        team = await db.teams.find_one({"_id": ObjectId(registration_data.team_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid team ID")
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check if user is team captain
    if str(team["captain_id"]) != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Only team captain can register")
    
    # Check if team already registered
    existing_registration = await db.tournament_registrations.find_one({
        "tournament_id": tournament_id,
        "team_id": registration_data.team_id
    })
    
    if existing_registration:
        raise HTTPException(status_code=400, detail="Team already registered for this tournament")
    
    # Generate registration number
    reg_count = await db.tournament_registrations.count_documents({})
    registration_number = f"REG-TOUR{tournament_id[-3:]}-TEAM{reg_count + 1:04d}"
    
    registration_dict = registration_data.dict()
    registration_dict["tournament_id"] = tournament_id
    registration_dict["registered_by"] = str(current_user["_id"])
    registration_dict["registration_number"] = registration_number
    registration_dict["registration_date"] = datetime.utcnow()
    registration_dict["created_at"] = datetime.utcnow()
    registration_dict["updated_at"] = datetime.utcnow()
    registration_dict["status"] = "pending"
    registration_dict["payment_status"] = "pending"
    
    result = await db.tournament_registrations.insert_one(registration_dict)

    created_registration = await db.tournament_registrations.find_one({"_id": result.inserted_id})
    created_registration["id"] = str(created_registration["_id"])
    del created_registration["_id"]

    return created_registration


@router.get("/{tournament_id}/registrations")
async def get_tournament_registrations(
    tournament_id: str,
    skip: int = 0,
    limit: int = 50
):
    """Get tournament registrations with embedded team info."""
    db = get_database()

    registrations_cursor = db.tournament_registrations.find({"tournament_id": tournament_id}).skip(skip).limit(limit)
    registrations = await registrations_cursor.to_list(length=limit)

    # Batch-fetch team documents to avoid N+1 lookups on the frontend
    team_ids = []
    for r in registrations:
        tid = r.get("team_id")
        if tid:
            try:
                team_ids.append(ObjectId(tid))
            except Exception:
                pass

    team_map: dict = {}
    if team_ids:
        teams_cursor = db.teams.find(
            {"_id": {"$in": team_ids}},
            {"_id": 1, "name": 1, "short_name": 1, "city": 1, "state": 1, "logo": 1, "logo_image": 1},
        )
        async for t in teams_cursor:
            team_map[str(t["_id"])] = t

    for registration in registrations:
        registration["id"] = str(registration["_id"])
        del registration["_id"]
        team = team_map.get(registration.get("team_id", ""), {})
        if team:
            registration["team_name"]       = team.get("name")
            registration["team_short_name"] = team.get("short_name")
            registration["team_city"]       = team.get("city")
            registration["team_state"]      = team.get("state")
            registration["team_logo"]       = team.get("logo") or team.get("logo_image")

    return registrations


@router.put("/{tournament_id}/registrations/{registration_id}")
async def update_registration_status(
    tournament_id: str,
    registration_id: str,
    update_data: TournamentRegistrationUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Organizer approves / rejects a team registration.

    Approval atomically increments current_teams on the tournament.
    Rejecting/cancelling a previously-approved registration decrements it.
    """
    db = get_database()

    try:
        tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid tournament ID")
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    user_id = str(current_user["_id"])
    tournament_organizer_id = str(tournament.get("organizer_id"))

    is_authorized = user_id == tournament_organizer_id
    if not is_authorized:
        manager = await db.organizer_managers.find_one({
            "manager_user_id": user_id,
            "organizer_id": tournament_organizer_id,
            "is_active": True,
        })
        if manager and "edit_tournament" in manager.get("permissions", []):
            is_authorized = True

    if not is_authorized:
        raise HTTPException(status_code=403, detail="Not authorized to manage registrations for this tournament")

    try:
        registration = await db.tournament_registrations.find_one({
            "_id": ObjectId(registration_id),
            "tournament_id": tournament_id,
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid registration ID")
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    previous_status = registration.get("status")
    new_status = update_data.status

    patch = {k: v for k, v in update_data.dict(exclude_unset=True).items() if v is not None}
    patch["updated_at"] = datetime.utcnow()

    await db.tournament_registrations.update_one(
        {"_id": ObjectId(registration_id)},
        {"$set": patch},
    )

    # Atomically keep current_teams in sync
    if new_status and new_status != previous_status:
        if new_status == "approved" and previous_status != "approved":
            await db.tournaments.update_one(
                {"_id": ObjectId(tournament_id)},
                {"$inc": {"current_teams": 1}},
            )
        elif new_status in ("rejected", "cancelled") and previous_status == "approved":
            await db.tournaments.update_one(
                {"_id": ObjectId(tournament_id)},
                {"$inc": {"current_teams": -1}},
            )

    updated = await db.tournament_registrations.find_one({"_id": ObjectId(registration_id)})
    updated["id"] = str(updated["_id"])
    del updated["_id"]
    return updated


@router.get("/registrations/{registration_id}")
async def get_registration(
    registration_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get registration details"""
    db = get_database()
    
    try:
        registration = await db.tournament_registrations.find_one({"_id": ObjectId(registration_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid registration ID")
    
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    registration["id"] = str(registration["_id"])

    
    del registration["_id"]  # Remove ObjectId
    return registration


# ==================== ORGANIZER TEAM REGISTRATION ENDPOINTS ====================

class OrganizerAddTeamRequest(BaseModel):
    team_name: str
    captain_name: str
    captain_phone: str
    captain_email: Optional[str] = None
    player_count: int = 11
    notes: Optional[str] = None

@router.post("/{tournament_id}/add-team")
async def organizer_add_team(
    tournament_id: str,
    team_data: OrganizerAddTeamRequest,
    current_user: dict = Depends(get_current_user)
):
    """Organizer or admin adds a team to tournament manually"""
    db = get_database()
    
    user_id = str(current_user["_id"])
    
    # Verify tournament exists
    try:
        tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid tournament ID")
    
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    tournament_organizer_id = str(tournament.get("organizer_id"))
    
    # Check if user is the organizer
    is_authorized = False
    added_by_role = "organizer"
    
    if user_id == tournament_organizer_id:
        is_authorized = True
        added_by_role = "organizer"
    else:
        # Check if user is a manager with appropriate permission
        manager = await db.organizer_managers.find_one({
            "manager_user_id": user_id,
            "organizer_id": tournament_organizer_id,
            "is_active": True
        })
        
        if manager:
            # Check if manager has edit_tournament or a new add_team permission
            permissions = manager.get("permissions", [])
            if "edit_tournament" in permissions or "add_team" in permissions:
                is_authorized = True
                added_by_role = "admin"
    
    if not is_authorized:
        raise HTTPException(
            status_code=403, 
            detail="Only tournament organizers and their admins can add teams"
        )
    
    # Check if tournament is accepting registrations
    if tournament["current_teams"] >= tournament["max_teams"]:
        raise HTTPException(status_code=400, detail="Tournament is full")
    
    # Check if team with same name already registered
    existing_registration = await db.tournament_registrations.find_one({
        "tournament_id": tournament_id,
        "team_name": team_data.team_name
    })
    
    if existing_registration:
        raise HTTPException(status_code=400, detail=f"Team '{team_data.team_name}' is already registered")
    
    # Generate registration number
    reg_count = await db.tournament_registrations.count_documents({})
    registration_number = f"REG-TOUR{tournament_id[-3:]}-TEAM{reg_count + 1:04d}"
    
    # Create the registration
    registration_dict = {
        "tournament_id": tournament_id,
        "team_id": None,  # No team ID - manual entry
        "team_name": team_data.team_name,
        "captain_name": team_data.captain_name,
        "captain_phone": team_data.captain_phone,
        "captain_email": team_data.captain_email,
        "player_count": team_data.player_count,
        "notes": team_data.notes,
        "registered_by": user_id,
        "added_by_organizer": True,
        "added_by_role": added_by_role,
        "registration_number": registration_number,
        "registration_date": datetime.utcnow(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "status": "confirmed",  # Auto-confirm when added by organizer
        "payment_status": "paid"  # Organizer handles payment offline
    }
    
    result = await db.tournament_registrations.insert_one(registration_dict)
    
    # Increment tournament's current_teams count
    await db.tournaments.update_one(
        {"_id": ObjectId(tournament_id)},
        {"$inc": {"current_teams": 1}}
    )
    
    created_registration = await db.tournament_registrations.find_one({"_id": result.inserted_id})
    created_registration["id"] = str(created_registration["_id"])
    del created_registration["_id"]
    
    print(f"[TOURNAMENT] Team added by {added_by_role}:")
    print(f"  - Tournament: {tournament.get('name')}")
    print(f"  - Team: {team_data.team_name}")
    print(f"  - Added by: {current_user.get('name')}")
    
    return created_registration


@router.delete("/{tournament_id}/registrations/{registration_id}")
async def remove_team_registration(
    tournament_id: str,
    registration_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove a team registration from tournament (organizer/admin only)"""
    db = get_database()
    
    user_id = str(current_user["_id"])
    
    # Verify tournament exists
    try:
        tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid tournament ID")
    
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    tournament_organizer_id = str(tournament.get("organizer_id"))
    
    # Check authorization
    is_authorized = False
    
    if user_id == tournament_organizer_id:
        is_authorized = True
    else:
        # Check if user is a manager with appropriate permission
        manager = await db.organizer_managers.find_one({
            "manager_user_id": user_id,
            "organizer_id": tournament_organizer_id,
            "is_active": True
        })
        
        if manager:
            permissions = manager.get("permissions", [])
            if "edit_tournament" in permissions:
                is_authorized = True
    
    if not is_authorized:
        raise HTTPException(
            status_code=403, 
            detail="Only tournament organizers and their admins can remove teams"
        )
    
    # Verify registration exists
    try:
        registration = await db.tournament_registrations.find_one({
            "_id": ObjectId(registration_id),
            "tournament_id": tournament_id
        })
    except:
        raise HTTPException(status_code=400, detail="Invalid registration ID")
    
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    # Delete the registration
    await db.tournament_registrations.delete_one({"_id": ObjectId(registration_id)})
    
    # Decrement tournament's current_teams count
    await db.tournaments.update_one(
        {"_id": ObjectId(tournament_id)},
        {"$inc": {"current_teams": -1}}
    )
    
    return {"message": "Team registration removed successfully"}


# ==================== MATCH SCHEDULING & RESULTS (new) ====================

@router.post("/{tournament_id}/matches")
async def create_match(
    tournament_id: str,
    data: MatchCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Organiser schedules a match/fixture in a tournament.
    Also allowed for organizer_managers with create_tournament permission.
    """
    db = get_database()
    try:
        tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid tournament ID")
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    roles   = current_user.get("roles", [])
    user_id = str(current_user["_id"])
    is_admin = any(r in roles for r in ("admin", "super_admin"))
    is_organizer = tournament.get("organizer_id") == user_id

    # Check if manager
    if not is_admin and not is_organizer:
        manager = await db.organizer_managers.find_one({
            "organizer_id": tournament.get("organizer_id"),
            "manager_user_id": user_id,
            "is_active": True,
        })
        if not manager:
            raise HTTPException(status_code=403, detail="Not authorized to schedule matches for this tournament")

    # Resolve team names from IDs if not provided
    team1_name = data.team1_name
    team2_name = data.team2_name
    if data.team1_id and not team1_name:
        t1 = await db.teams.find_one({"_id": ObjectId(data.team1_id)})
        if t1:
            team1_name = t1.get("name")
    if data.team2_id and not team2_name:
        t2 = await db.teams.find_one({"_id": ObjectId(data.team2_id)})
        if t2:
            team2_name = t2.get("name")

    match_dict = {
        **data.dict(),
        "tournament_id": tournament_id,
        "team1_name":    team1_name,
        "team2_name":    team2_name,
        "winner_id":     None,
        "team1_score":   None,
        "team2_score":   None,
        "result_summary":None,
        "status":        "scheduled",
        "completed_at":  None,
        "recorded_by":   None,
        "created_at":    datetime.utcnow(),
        "updated_at":    datetime.utcnow(),
    }
    result = await db.matches.insert_one(match_dict)
    created = await db.matches.find_one({"_id": result.inserted_id})
    created["id"] = str(created["_id"])
    del created["_id"]
    return created


@router.get("/{tournament_id}/matches")
async def get_tournament_matches(
    tournament_id: str,
    round_number: Optional[int] = None,
    status: Optional[str] = None,
):
    """Get all scheduled matches / fixtures for a tournament."""
    db = get_database()
    query = {"tournament_id": tournament_id}
    if round_number is not None:
        query["round_number"] = round_number
    if status:
        query["status"] = status
    cursor  = db.matches.find(query).sort([("round_number", 1), ("match_number", 1)])
    matches = await cursor.to_list(length=500)
    for m in matches:
        m["id"] = str(m["_id"])
        del m["_id"]
    return {"matches": matches, "total": len(matches)}


@router.put("/{tournament_id}/matches/{match_id}")
async def update_match(
    tournament_id: str,
    match_id: str,
    data: MatchUpdate,
    current_user: dict = Depends(get_current_user),
):
    """
    Organiser updates match schedule or records results.
    If status is set to 'completed', winner_id, team1_score, team2_score are saved
    and team stats are automatically updated.
    """
    db = get_database()
    try:
        match = await db.matches.find_one({"_id": ObjectId(match_id), "tournament_id": tournament_id})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid match ID")
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    roles   = current_user.get("roles", [])
    user_id = str(current_user["_id"])
    is_admin = any(r in roles for r in ("admin", "super_admin"))
    is_org   = tournament and tournament.get("organizer_id") == user_id
    if not is_admin and not is_org:
        manager = await db.organizer_managers.find_one({
            "organizer_id": tournament.get("organizer_id") if tournament else None,
            "manager_user_id": user_id,
            "is_active": True,
        })
        if not manager:
            raise HTTPException(status_code=403, detail="Not authorized")

    update = {k: v for k, v in data.dict(exclude_unset=True).items() if v is not None}
    update["updated_at"] = datetime.utcnow()

    # When completing a match, record result metadata
    if data.status == "completed":
        update["completed_at"] = datetime.utcnow()
        update["recorded_by"]  = user_id
        # Auto-update team win/loss counts
        team1_id  = match.get("team1_id")
        team2_id  = match.get("team2_id")
        winner_id = data.winner_id
        if team1_id and team2_id:
            # Both teams played
            await db.teams.update_one({"_id": ObjectId(team1_id)}, {"$inc": {"matches_played": 1}})
            await db.teams.update_one({"_id": ObjectId(team2_id)}, {"$inc": {"matches_played": 1}})
            if winner_id == team1_id:
                await db.teams.update_one({"_id": ObjectId(team1_id)}, {"$inc": {"matches_won": 1}})
                await db.teams.update_one({"_id": ObjectId(team2_id)}, {"$inc": {"matches_lost": 1}})
            elif winner_id == team2_id:
                await db.teams.update_one({"_id": ObjectId(team2_id)}, {"$inc": {"matches_won": 1}})
                await db.teams.update_one({"_id": ObjectId(team1_id)}, {"$inc": {"matches_lost": 1}})
            else:
                # Draw / no winner recorded
                await db.teams.update_one({"_id": ObjectId(team1_id)}, {"$inc": {"matches_drawn": 1}})
                await db.teams.update_one({"_id": ObjectId(team2_id)}, {"$inc": {"matches_drawn": 1}})

    await db.matches.update_one({"_id": ObjectId(match_id)}, {"$set": update})
    updated = await db.matches.find_one({"_id": ObjectId(match_id)})
    updated["id"] = str(updated["_id"])
    del updated["_id"]
    return updated


@router.delete("/{tournament_id}/matches/{match_id}")
async def delete_match(
    tournament_id: str,
    match_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Cancel / delete a scheduled match."""
    db = get_database()
    try:
        match = await db.matches.find_one({"_id": ObjectId(match_id), "tournament_id": tournament_id})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid match ID")
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
    roles   = current_user.get("roles", [])
    user_id = str(current_user["_id"])
    is_admin = any(r in roles for r in ("admin", "super_admin"))
    is_org   = tournament and tournament.get("organizer_id") == user_id
    if not is_admin and not is_org:
        raise HTTPException(status_code=403, detail="Not authorized")

    await db.matches.update_one(
        {"_id": ObjectId(match_id)},
        {"$set": {"status": "cancelled", "updated_at": datetime.utcnow()}},
    )
    return {"message": "Match cancelled"}


@router.get("/{tournament_id}/standings")
async def get_tournament_standings(tournament_id: str):
    """
    Return team standings (points table) for a tournament based on completed matches.
    Points: Win=3, Draw=1, Loss=0.
    """
    db = get_database()
    # Fetch all registrations to get the team list
    reg_cursor = db.tournament_registrations.find({
        "tournament_id": tournament_id,
        "status": {"$in": ["approved", "pending"]},
    })
    regs = await reg_cursor.to_list(length=200)

    standings = []
    for reg in regs:
        team_id = reg.get("team_id")
        if not team_id:
            continue
        try:
            team = await db.teams.find_one({"_id": ObjectId(team_id)})
        except Exception:
            continue
        if not team:
            continue
        played = team.get("matches_played", 0)
        won    = team.get("matches_won",    0)
        lost   = team.get("matches_lost",   0)
        drawn  = team.get("matches_drawn",  0)
        points = won * 3 + drawn * 1
        standings.append({
            "team_id":   team_id,
            "team_name": team.get("name"),
            "logo":      team.get("logo"),
            "played":    played,
            "won":       won,
            "lost":      lost,
            "drawn":     drawn,
            "points":    points,
        })
    # Sort: points desc, then won desc
    standings.sort(key=lambda x: (-x["points"], -x["won"]))
    for i, s in enumerate(standings):
        s["position"] = i + 1
    return {"tournament_id": tournament_id, "standings": standings}
