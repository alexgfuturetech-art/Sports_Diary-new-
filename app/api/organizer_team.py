from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
import random
from pydantic import BaseModel

from app.core.database import get_database
from app.core.security import get_current_user
from app.schemas.schemas import (
    OrganizerManagerCreate, OrganizerManagerUpdate, OrganizerManagerResponse,
    OrganizerManagerAddExisting
)

router = APIRouter(tags=["organizer_team"])


# ==================== REQUEST MODELS ====================

class SendInvitationRequest(BaseModel):
    user_id: str
    permissions: List[str]
    role_description: str = "Team Member"


# ==================== TEAM INVITATION ENDPOINTS ====================

@router.post("/invitations/send")
async def send_team_invitation(
    request: SendInvitationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Send invitation to user to join organizer's team"""
    db = get_database()
    
    user_id = request.user_id
    permissions = request.permissions
    role_description = request.role_description
    
    # Check if current user is organizer
    if current_user.get("role") != "organizer":
        raise HTTPException(status_code=403, detail="Only organizers can send invitations")
    
    # Check if target user exists
    try:
        target_user = await db.users.find_one({"_id": ObjectId(user_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Can't invite yourself
    if user_id == str(current_user["_id"]):
        raise HTTPException(status_code=400, detail="Cannot invite yourself")
    
    # Check if user is already in team
    existing_manager = await db.organizer_managers.find_one({
        "organizer_id": str(current_user["_id"]),
        "manager_user_id": user_id,
        "is_active": True
    })
    
    if existing_manager:
        raise HTTPException(status_code=400, detail="This user is already in your team")
    
    # Check if invitation already exists and is pending
    existing_invitation = await db.team_invitations.find_one({
        "organizer_id": str(current_user["_id"]),
        "user_id": user_id,
        "status": "pending"
    })
    
    if existing_invitation:
        raise HTTPException(status_code=400, detail="Invitation already sent to this user")
    
    # Ensure edit_tournament is always included
    permissions_to_send = list(set([*permissions, "edit_tournament"]))
    
    # Create invitation
    invitation = {
        "organizer_id": str(current_user["_id"]),
        "organizer_name": current_user.get("name", "Organizer"),
        "user_id": user_id,
        "user_name": target_user.get("name"),
        "user_phone": target_user.get("phone"),
        "role_description": role_description,
        "permissions": permissions_to_send,
        "status": "pending",  # pending, accepted, rejected
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(days=7)  # Invitation expires in 7 days
    }
    
    result = await db.team_invitations.insert_one(invitation)
    created_invitation = await db.team_invitations.find_one({"_id": result.inserted_id})
    created_invitation["id"] = str(created_invitation["_id"])
    del created_invitation["_id"]
    
    print(f"[TEAM_INVITATION] Invitation sent:")
    print(f"  - From: {current_user.get('name')} ({current_user.get('phone')})")
    print(f"  - To: {target_user.get('name')} ({target_user.get('phone')})")
    print(f"  - Permissions: {permissions_to_send}")
    
    return created_invitation


@router.get("/invitations/pending")
async def get_pending_invitations(
    current_user: dict = Depends(get_current_user)
):
    """Get all pending invitations for current user"""
    db = get_database()
    
    # Find all pending invitations for this user
    invitations_cursor = db.team_invitations.find({
        "user_id": str(current_user["_id"]),
        "status": "pending",
        "expires_at": {"$gt": datetime.utcnow()}  # Not expired
    }).sort([("created_at", -1)])
    
    invitations = await invitations_cursor.to_list(length=100)
    
    for invitation in invitations:
        invitation["id"] = str(invitation["_id"])
        del invitation["_id"]
    
    return invitations


@router.post("/invitations/{invitation_id}/accept")
async def accept_team_invitation(
    invitation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Accept team invitation"""
    db = get_database()
    
    try:
        invitation = await db.team_invitations.find_one({"_id": ObjectId(invitation_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid invitation ID")
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    # Check if invitation is for current user
    if invitation["user_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="This invitation is not for you")
    
    # Check if invitation is still pending
    if invitation["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Invitation already {invitation['status']}")
    
    # Check if invitation has expired
    if invitation.get("expires_at") and invitation["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invitation has expired")
    
    # Create manager entry
    manager_dict = {
        "organizer_id": invitation["organizer_id"],
        "organizer_name": invitation["organizer_name"],
        "manager_user_id": str(current_user["_id"]),
        "name": current_user.get("name"),
        "phone": current_user.get("phone"),
        "email": current_user.get("email"),
        "role_description": invitation["role_description"],
        "permissions": invitation["permissions"],
        "is_active": True,
        "is_verified": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_active": None
    }
    
    result = await db.organizer_managers.insert_one(manager_dict)
    
    # Update invitation status
    await db.team_invitations.update_one(
        {"_id": ObjectId(invitation_id)},
        {"$set": {
            "status": "accepted",
            "updated_at": datetime.utcnow()
        }}
    )
    
    created_manager = await db.organizer_managers.find_one({"_id": result.inserted_id})
    created_manager["id"] = str(created_manager["_id"])
    del created_manager["_id"]
    
    print(f"[TEAM_INVITATION] Invitation accepted:")
    print(f"  - User: {current_user.get('name')} ({current_user.get('phone')})")
    print(f"  - Organizer: {invitation['organizer_name']}")
    print(f"  - Permissions: {invitation['permissions']}")
    
    return created_manager


@router.post("/invitations/{invitation_id}/reject")
async def reject_team_invitation(
    invitation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Reject team invitation"""
    db = get_database()
    
    try:
        invitation = await db.team_invitations.find_one({"_id": ObjectId(invitation_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid invitation ID")
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    # Check if invitation is for current user
    if invitation["user_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="This invitation is not for you")
    
    # Check if invitation is still pending
    if invitation["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Invitation already {invitation['status']}")
    
    # Update invitation status
    await db.team_invitations.update_one(
        {"_id": ObjectId(invitation_id)},
        {"$set": {
            "status": "rejected",
            "updated_at": datetime.utcnow()
        }}
    )
    
    return {"message": "Invitation rejected"}


@router.get("/invitations/sent")
async def get_sent_invitations(
    current_user: dict = Depends(get_current_user)
):
    """Get all invitations sent by current organizer"""
    db = get_database()
    
    # Check if current user is organizer
    if current_user.get("role") != "organizer":
        raise HTTPException(status_code=403, detail="Only organizers can view sent invitations")
    
    # Find all invitations sent by this organizer
    invitations_cursor = db.team_invitations.find({
        "organizer_id": str(current_user["_id"])
    }).sort([("created_at", -1)])
    
    invitations = await invitations_cursor.to_list(length=100)
    
    for invitation in invitations:
        invitation["id"] = str(invitation["_id"])
        del invitation["_id"]
    
    return invitations


# ==================== ORGANIZER TEAM MANAGEMENT ENDPOINTS ====================

@router.post("/managers/add-existing")
async def add_existing_user_as_manager(
    manager_data: OrganizerManagerAddExisting,
    current_user: dict = Depends(get_current_user)
):
    """Add an existing registered user as a manager"""
    db = get_database()
    
    # Check if current user is organizer
    if current_user.get("role") != "organizer":
        raise HTTPException(status_code=403, detail="Only organizers can add team members")
    
    # Check if user exists
    try:
        user = await db.users.find_one({"_id": ObjectId(manager_data.user_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if this user is already a manager for this organizer
    existing_manager = await db.organizer_managers.find_one({
        "organizer_id": str(current_user["_id"]),
        "manager_user_id": manager_data.user_id,
        "is_active": True
    })
    
    if existing_manager:
        raise HTTPException(status_code=400, detail="This user is already in your team")
    
    # Create manager entry
    manager_dict = {
        "organizer_id": str(current_user["_id"]),
        "organizer_name": current_user.get("name", "Organizer"),
        "manager_user_id": manager_data.user_id,
        "name": user.get("name"),
        "phone": user.get("phone"),
        "email": user.get("email"),
        "role_description": manager_data.role_description or "Team Member",
        "permissions": manager_data.permissions,
        "is_active": True,
        "is_verified": True,  # Already a registered user
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_active": None
    }
    
    result = await db.organizer_managers.insert_one(manager_dict)
    created_manager = await db.organizer_managers.find_one({"_id": result.inserted_id})
    created_manager["id"] = str(created_manager["_id"])
    del created_manager["_id"]
    
    print(f"[ORGANIZER_TEAM] Added existing user as manager:")
    print(f"  - User: {user.get('name')} ({user.get('phone')})")
    print(f"  - Organizer: {current_user.get('name')}")
    print(f"  - Permissions: {manager_data.permissions}")
    
    return created_manager


@router.get("/search-users")
async def search_users_for_team(
    query: str,
    current_user: dict = Depends(get_current_user),
    limit: int = 10
):
    """Search for registered users to add to team"""
    db = get_database()
    
    # Check if current user is organizer
    if current_user.get("role") != "organizer":
        raise HTTPException(status_code=403, detail="Only organizers can search for team members")
    
    # Search by name or phone
    search_query = {
        "$or": [
            {"name": {"$regex": query, "$options": "i"}},
            {"phone": {"$regex": query, "$options": "i"}}
        ],
        "is_verified": True,  # Only verified users
        "onboarding_completed": True  # Only users who completed profile
    }
    
    users_cursor = db.users.find(search_query).limit(limit)
    users = await users_cursor.to_list(length=limit)
    
    # Get list of current team members to mark them
    current_team = await db.organizer_managers.find({
        "organizer_id": str(current_user["_id"]),
        "is_active": True
    }).to_list(length=100)
    
    current_team_user_ids = [m.get("manager_user_id") for m in current_team]
    
    # Format results
    results = []
    for user in users:
        user_id = str(user["_id"])
        
        # Skip if user is the organizer themselves
        if user_id == str(current_user["_id"]):
            continue
        
        results.append({
            "id": user_id,
            "name": user.get("name"),
            "phone": user.get("phone"),
            "email": user.get("email"),
            "role": user.get("role"),
            "city": user.get("city"),
            "state": user.get("state"),
            "avatar": user.get("avatar"),
            "is_verified": user.get("is_verified", False),
            "already_in_team": user_id in current_team_user_ids
        })
    
    return results


@router.post("/managers")
async def create_manager(
    manager_data: OrganizerManagerCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a manager/staff account with full profile for organizer"""
    db = get_database()
    
    # Check if current user is organizer
    if current_user.get("role") != "organizer":
        raise HTTPException(status_code=403, detail="Only organizers can create manager accounts")
    
    # Check if phone already exists as a manager for this organizer
    existing_manager = await db.organizer_managers.find_one({
        "organizer_id": str(current_user["_id"]),
        "phone": manager_data.phone,
        "is_active": True
    })
    
    if existing_manager:
        raise HTTPException(status_code=400, detail="Manager with this phone already exists in your team")
    
    # Check if this phone already has a user account
    existing_user = await db.users.find_one({"phone": manager_data.phone})
    
    if existing_user:
        # User already exists, just link them as manager
        manager_user_id = str(existing_user["_id"])
    else:
        # Check if email already exists (if provided)
        if manager_data.email and manager_data.email.strip():
            email_exists = await db.users.find_one({"email": manager_data.email})
            if email_exists:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Email {manager_data.email} is already registered. Please use a different email or leave it empty."
                )
        
        # Create a new user account with complete profile
        new_user = {
            "phone": manager_data.phone,
            "name": manager_data.name,
            "role": "organizer",  # Manager role is "organizer" since they create tournaments
            "city": manager_data.city or current_user.get("city"),
            "state": manager_data.state or current_user.get("state", "Gujarat"),
            "bio": manager_data.bio or f"Tournament Manager for {current_user.get('name', 'Organizer')}",
            "sports_interests": manager_data.sports_interests or [],
            "avatar": None,
            "is_verified": True,  # Pre-verified by organizer
            "is_active": True,  # Active user
            "onboarding_completed": True,  # Skip onboarding!
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "latitude": current_user.get("latitude"),
            "longitude": current_user.get("longitude")
        }
        
        # Only add optional fields if they have values
        if manager_data.email and manager_data.email.strip():
            new_user["email"] = manager_data.email
        if manager_data.age:
            new_user["age"] = manager_data.age
        if manager_data.gender:
            new_user["gender"] = manager_data.gender
        
        print(f"[ORGANIZER_TEAM] Creating manager user account:")
        print(f"  - phone: {manager_data.phone}")
        print(f"  - name: {manager_data.name}")
        print(f"  - email: {manager_data.email or 'not provided'}")
        print(f"  - role: organizer")
        print(f"  - onboarding_completed: True")
        print(f"  - is_verified: True")
        print(f"  - is_active: True")
        
        # Insert the new user
        try:
            user_result = await db.users.insert_one(new_user)
            manager_user_id = str(user_result.inserted_id)
            print(f"[ORGANIZER_TEAM] Manager user created with ID: {manager_user_id}")
        except Exception as e:
            print(f"[ORGANIZER_TEAM] Error creating manager user: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to create manager account. Please try again."
            )
    
    # Default permissions if not provided
    default_permissions = ["create_tournament", "edit_tournament", "view_registrations"]
    
    # Create manager entry in organizer_managers collection
    manager_dict = {
        "organizer_id": str(current_user["_id"]),
        "organizer_name": current_user.get("name", "Organizer"),
        "manager_user_id": manager_user_id,
        "name": manager_data.name,
        "phone": manager_data.phone,
        "email": manager_data.email,
        "role_description": manager_data.role_description,
        "permissions": manager_data.permissions or default_permissions,
        "is_active": True,
        "is_verified": True,  # Always verified when created by organizer
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_active": None
    }
    
    result = await db.organizer_managers.insert_one(manager_dict)
    created_manager = await db.organizer_managers.find_one({"_id": result.inserted_id})
    created_manager["id"] = str(created_manager["_id"])
    del created_manager["_id"]
    
    return created_manager


@router.get("/managers")
async def get_my_managers(
    current_user: dict = Depends(get_current_user),
    include_inactive: bool = False
):
    """Get all managers for current organizer"""
    db = get_database()
    
    # Check if current user is organizer
    if current_user.get("role") != "organizer":
        raise HTTPException(status_code=403, detail="Only organizers can view their team")
    
    query = {"organizer_id": str(current_user["_id"])}
    if not include_inactive:
        query["is_active"] = True
    
    managers_cursor = db.organizer_managers.find(query).sort([("created_at", -1)])
    managers = await managers_cursor.to_list(length=100)
    
    for manager in managers:
        manager["id"] = str(manager["_id"])
        del manager["_id"]
    
    return managers


@router.get("/managers/{manager_id}")
async def get_manager(
    manager_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get manager details"""
    db = get_database()
    
    try:
        manager = await db.organizer_managers.find_one({"_id": ObjectId(manager_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid manager ID")
    
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    
    # Check authorization
    if str(manager["organizer_id"]) != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    manager["id"] = str(manager["_id"])
    del manager["_id"]
    
    return manager


@router.put("/managers/{manager_id}")
async def update_manager(
    manager_id: str,
    manager_data: OrganizerManagerUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update manager details"""
    db = get_database()
    
    try:
        manager = await db.organizer_managers.find_one({"_id": ObjectId(manager_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid manager ID")
    
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    
    # Check if user is the organizer
    if str(manager["organizer_id"]) != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {k: v for k, v in manager_data.dict(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.organizer_managers.update_one(
        {"_id": ObjectId(manager_id)},
        {"$set": update_data}
    )
    
    updated_manager = await db.organizer_managers.find_one({"_id": ObjectId(manager_id)})
    updated_manager["id"] = str(updated_manager["_id"])
    del updated_manager["_id"]
    
    return updated_manager


@router.delete("/managers/{manager_id}")
async def remove_manager(
    manager_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove manager from organizer's team"""
    db = get_database()
    
    try:
        manager = await db.organizer_managers.find_one({"_id": ObjectId(manager_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid manager ID")
    
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    
    # Check if user is the organizer
    if str(manager["organizer_id"]) != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Soft delete
    await db.organizer_managers.update_one(
        {"_id": ObjectId(manager_id)},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Manager removed successfully"}


# ==================== HELPER FUNCTIONS ====================

async def check_tournament_permission(db, user_id: str, tournament_id: str = None, permission: str = "create_tournament"):
    """
    Check if user has permission to create/edit tournaments
    Returns: (has_permission: bool, organizer_id: str)
    """
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        return False, None
    
    # If user is organizer, they have all permissions
    if user.get("role") == "organizer":
        return True, str(user["_id"])
    
    # Check if user is a manager
    manager = await db.organizer_managers.find_one({
        "manager_user_id": user_id,
        "is_active": True
    })
    
    if not manager:
        return False, None
    
    # Check if manager has the required permission
    permissions = manager.get("permissions", [])
    if permission not in permissions:
        return False, None
    
    # If checking for edit permission, verify the tournament belongs to the organizer
    if tournament_id and permission == "edit_tournament":
        tournament = await db.tournaments.find_one({"_id": ObjectId(tournament_id)})
        if not tournament or str(tournament["organizer_id"]) != str(manager["organizer_id"]):
            return False, None
    
    # Return permission granted and the organizer_id
    return True, str(manager["organizer_id"])


@router.get("/check-permission")
async def check_my_permissions(
    current_user: dict = Depends(get_current_user)
):
    """Check current user's organizer permissions"""
    db = get_database()
    
    user_id = str(current_user["_id"])
    user_name = current_user.get("name", "Unknown")
    
    print(f"[CHECK_PERMISSION] Checking permissions for user: {user_name} ({user_id})")
    
    # First check if user is a manager
    manager = await db.organizer_managers.find_one({
        "manager_user_id": user_id,
        "is_active": True
    })
    
    if manager:
        # User is a manager - return parent organizer's info
        org_id = str(manager["organizer_id"])
        permissions = manager.get("permissions", [])
        
        print(f"[CHECK_PERMISSION] User is manager")
        print(f"  - Organizer ID: {org_id}")
        print(f"  - Permissions: {permissions}")
        
        return {
            "is_organizer": False,
            "is_manager": True,
            "organizer_id": org_id,
            "organizer_name": manager.get("organizer_name"),
            "permissions": permissions
        }
    
    # If not a manager, check if user is an organizer
    if current_user.get("role") == "organizer":
        print(f"[CHECK_PERMISSION] User is organizer")
        return {
            "is_organizer": True,
            "is_manager": False,
            "organizer_id": user_id,
            "permissions": ["create_tournament", "edit_tournament", "view_registrations", "manage_team"]
        }
    
    print(f"[CHECK_PERMISSION] User is neither organizer nor manager")
    return {
        "is_organizer": False,
        "is_manager": False,
        "organizer_id": None,
        "permissions": []
    }

