"""
auth.py – Authentication + User Profile endpoints

Key changes (v2 → v3)
---------------------
• Email OTP login added (send-email-otp / verify-email-otp) using
  Python's built-in smtplib with any free SMTP relay (Gmail app-password or
  Brevo free tier). Falls back to printing the OTP in console when no
  SMTP is configured — zero external dependency required.
• roles field is now a List[str]; role (single string) kept for
  backwards compat and always mirrors roles[0].
• Organiser role requires admin approval:
    POST /api/auth/request-organizer-role  → sets status "pending"
    Admin approves via POST /api/admin/approve-organizer/{user_id}
• Professional role requires a one-time fee acknowledgement flag:
    POST /api/auth/request-professional-role  → marks pending_payment
    Admin confirms payment via POST /api/admin/confirm-professional-fee/{user_id}
    (In production wire this to a real payment callback; for now admin confirms.)
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from datetime import timedelta, datetime
from bson import ObjectId
from typing import Optional, List
import smtplib
import os
import random
import string
from email.mime.text import MIMEText

from app.core.database import get_database
from app.core.config import settings
from app.core.security import (
    generate_otp, store_otp, verify_otp,
    create_access_token, get_current_user, otp_storage,
)
from app.models.models import User
from app.schemas.schemas import (
    OTPRequest, OTPVerify, EmailOTPRequest, EmailOTPVerify,
    Token, UserResponse,
    UserProfileCreate, UserProfileUpdate, LocationUpdate,
    RoleRequest,
)

router = APIRouter()

# ─── In-memory email OTP store (same pattern as phone OTP) ────────────────────
email_otp_storage: dict = {}


# ─── helpers ──────────────────────────────────────────────────────────────────

def _user_dict(u: dict, *, include_private: bool = False) -> dict:
    """Serialise a MongoDB user document to a clean response dict."""
    roles = u.get("roles", [])
    # Back-fill role for clients that still read the single role field
    primary_role = roles[0] if roles else u.get("role")
    base = {
        "id":                   str(u["_id"]),
        "phone":                u.get("phone"),
        "email":                u.get("email"),
        "name":                 u.get("name"),
        "age":                  u.get("age"),
        "gender":               u.get("gender"),
        "role":                 primary_role,
        "roles":                roles,
        "professional_type":    u.get("professional_type"),
        "organizer_status":     u.get("organizer_status"),
        "professional_status":  u.get("professional_status"),
        "city":                 u.get("city"),
        "state":                u.get("state"),
        "bio":                  u.get("bio"),
        "avatar":               u.get("avatar"),
        "sports_interests":     u.get("sports_interests", []),
        "player_position":      u.get("player_position"),
        "playing_style":        u.get("playing_style"),
        "certification":        u.get("certification"),
        "experience_years":     u.get("experience_years"),
        "children_count":       u.get("children_count"),
        "is_verified":          u.get("is_verified", False),
        "onboarding_completed": u.get("onboarding_completed", False),
        "created_at":           u.get("created_at"),
        "updated_at":           u.get("updated_at"),
    }
    if include_private:
        base.update({
            "latitude":  u.get("latitude"),
            "longitude": u.get("longitude"),
            "is_active": u.get("is_active", True),
        })
    return base


def _send_email_otp_smtp(to_email: str, otp: str):
    """
    Send OTP via SMTP.
    Configure env vars: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD.
    If unconfigured, OTP is printed to console (dev mode).
    Uses only Python stdlib — no paid service needed.
    Free options: Gmail (app-password), Brevo free tier, Mailjet free tier.
    """
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    from_email = os.getenv("SMTP_FROM", smtp_user or "noreply@sportsdiary.app")

    if not smtp_host or not smtp_user:
        # Dev mode: just print
        print(f"[EMAIL OTP] {to_email} → {otp}")
        return

    body = f"""Your Sports Diary OTP is: {otp}

This code expires in {settings.OTP_EXPIRE_MINUTES} minutes.
Do not share it with anyone.
"""
    msg = MIMEText(body)
    msg["Subject"] = f"Sports Diary OTP: {otp}"
    msg["From"] = from_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, [to_email], msg.as_string())
        print(f"[EMAIL OTP] sent to {to_email}")
    except Exception as exc:
        print(f"[EMAIL OTP] SMTP error ({exc}); OTP for {to_email}: {otp}")


# ─── PHONE OTP ─────────────────────────────────────────────────────────────────

@router.post("/send-otp")
async def send_otp(request: OTPRequest):
    """Send OTP to phone number."""
    if not request.phone.startswith("+91") or len(request.phone) != 13:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format. Use +91XXXXXXXXXX",
        )
    otp = generate_otp()
    store_otp(request.phone, otp)
    print(f"[AUTH] OTP for {request.phone}: {otp}")
    return {
        "message": "OTP sent successfully",
        "phone": request.phone,
        "otp": otp,   # dev convenience — remove in production
        "expires_in_minutes": settings.OTP_EXPIRE_MINUTES,
    }


@router.post("/verify-otp", response_model=Token)
async def verify_otp_endpoint(request: OTPVerify):
    """Verify phone OTP and return JWT access token."""
    if not request.otp.isdigit() or len(request.otp) != 6:
        raise HTTPException(status_code=400, detail="OTP must be 6 digits")
    if not verify_otp(request.phone, request.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    db = get_database()
    user_data = await db.users.find_one({"phone": request.phone})
    is_new = False

    if not user_data:
        new_user = {
            "phone":                request.phone,
            "roles":               ["player"],
            "role":                "player",
            "is_verified":          True,
            "is_active":            True,
            "onboarding_completed": False,
            "created_at":           datetime.utcnow(),
            "updated_at":           datetime.utcnow(),
        }
        result    = await db.users.insert_one(new_user)
        user_data = await db.users.find_one({"_id": result.inserted_id})
        is_new    = True
    else:
        # Migrate old single-role users to roles list
        if not user_data.get("roles"):
            old_role = user_data.get("role", "player")
            await db.users.update_one(
                {"_id": user_data["_id"]},
                {"$set": {"roles": [old_role] if old_role else ["player"],
                           "is_verified": True, "updated_at": datetime.utcnow()}},
            )
        else:
            await db.users.update_one(
                {"_id": user_data["_id"]},
                {"$set": {"is_verified": True, "updated_at": datetime.utcnow()}},
            )
        user_data = await db.users.find_one({"_id": user_data["_id"]})

    access_token = create_access_token(
        data={"sub": request.phone},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    user_resp = _user_dict(user_data)
    user_resp["is_new_user"] = is_new
    return {"access_token": access_token, "token_type": "bearer", "user": user_resp}


# ─── EMAIL OTP ─────────────────────────────────────────────────────────────────

@router.post("/send-email-otp")
async def send_email_otp(request: EmailOTPRequest, background_tasks: BackgroundTasks):
    """
    Send OTP to an email address.
    Uses stdlib smtplib — free, no SDK. Configure SMTP_* env vars or OTP prints to console.
    """
    import re
    if not re.match(r"[^@]+@[^@]+\.[^@]+", request.email):
        raise HTTPException(status_code=400, detail="Invalid email address")

    otp = generate_otp()
    # Reuse the phone OTP store keyed on email
    store_otp(request.email, otp)
    background_tasks.add_task(_send_email_otp_smtp, request.email, otp)

    return {
        "message": "OTP sent to email",
        "email": request.email,
        "otp": otp,   # dev convenience — remove in production
        "expires_in_minutes": settings.OTP_EXPIRE_MINUTES,
    }


@router.post("/verify-email-otp", response_model=Token)
async def verify_email_otp_endpoint(request: EmailOTPVerify):
    """Verify email OTP and return JWT (creates user if new, keyed by email)."""
    if not request.otp.isdigit() or len(request.otp) != 6:
        raise HTTPException(status_code=400, detail="OTP must be 6 digits")
    if not verify_otp(request.email, request.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    db = get_database()
    user_data = await db.users.find_one({"email": request.email})
    is_new = False

    if not user_data:
        new_user = {
            "email":                request.email,
            "phone":                None,
            "roles":               ["player"],
            "role":                "player",
            "is_verified":          True,
            "is_active":            True,
            "onboarding_completed": False,
            "created_at":           datetime.utcnow(),
            "updated_at":           datetime.utcnow(),
        }
        result    = await db.users.insert_one(new_user)
        user_data = await db.users.find_one({"_id": result.inserted_id})
        is_new    = True
    else:
        if not user_data.get("roles"):
            old_role = user_data.get("role", "player")
            await db.users.update_one(
                {"_id": user_data["_id"]},
                {"$set": {"roles": [old_role] if old_role else ["player"],
                           "is_verified": True, "updated_at": datetime.utcnow()}},
            )
        else:
            await db.users.update_one(
                {"_id": user_data["_id"]},
                {"$set": {"is_verified": True, "updated_at": datetime.utcnow()}},
            )
        user_data = await db.users.find_one({"_id": user_data["_id"]})

    # JWT sub = email when no phone
    sub = user_data.get("phone") or user_data.get("email")
    access_token = create_access_token(
        data={"sub": sub, "login_method": "email"},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    user_resp = _user_dict(user_data)
    user_resp["is_new_user"] = is_new
    return {"access_token": access_token, "token_type": "bearer", "user": user_resp}


# ─── CURRENT USER ──────────────────────────────────────────────────────────────

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return _user_dict(current_user, include_private=True)


# ─── PROFILE CRUD ──────────────────────────────────────────────────────────────

@router.post("/profile")
async def create_profile(
    profile: UserProfileCreate,
    current_user: dict = Depends(get_current_user),
):
    _RESTRICTED_ROLES = {"organizer", "professional", "admin", "super_admin"}

    db = get_database()
    update_data = {k: v for k, v in profile.dict().items() if v is not None}
    # Sync roles list when role is set directly (onboarding),
    # but never allow restricted roles to be granted this way.
    if "role" in update_data:
        new_role = update_data["role"]
        if new_role in _RESTRICTED_ROLES:
            del update_data["role"]
        else:
            existing_roles = current_user.get("roles", [])
            if new_role not in existing_roles:
                existing_roles = [new_role] + [r for r in existing_roles if r != new_role]
            update_data["roles"] = existing_roles
    update_data["updated_at"] = datetime.utcnow()
    await db.users.update_one({"_id": current_user["_id"]}, {"$set": update_data})
    updated = await db.users.find_one({"_id": current_user["_id"]})
    return _user_dict(updated, include_private=True)


@router.put("/profile")
async def update_profile(
    profile: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
):
    _RESTRICTED_ROLES = {"organizer", "professional", "admin", "super_admin"}

    db = get_database()
    update_data = {k: v for k, v in profile.dict(exclude_unset=True).items() if v is not None}
    if "role" in update_data:
        new_role = update_data["role"]
        if new_role in _RESTRICTED_ROLES:
            del update_data["role"]
        else:
            existing_roles = current_user.get("roles", [])
            if new_role not in existing_roles:
                existing_roles = [new_role] + [r for r in existing_roles if r != new_role]
            update_data["roles"] = existing_roles
    update_data["updated_at"] = datetime.utcnow()
    await db.users.update_one({"_id": current_user["_id"]}, {"$set": update_data})
    updated = await db.users.find_one({"_id": current_user["_id"]})
    return _user_dict(updated, include_private=True)


@router.put("/location")
async def update_location(
    location: LocationUpdate,
    current_user: dict = Depends(get_current_user),
):
    db = get_database()
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {
            "latitude":   location.latitude,
            "longitude":  location.longitude,
            "updated_at": datetime.utcnow(),
        }},
    )
    return {"message": "Location updated", "latitude": location.latitude, "longitude": location.longitude}


# ─── ROLE MANAGEMENT ──────────────────────────────────────────────────────────

@router.post("/request-organizer-role")
async def request_organizer_role(current_user: dict = Depends(get_current_user)):
    """
    User requests the Organiser role. Sets organizer_status='pending'.
    Admin must approve via POST /api/admin/approve-organizer/{user_id}.
    """
    db = get_database()
    current_status = current_user.get("organizer_status")
    roles = current_user.get("roles", [])
    if "organizer" in roles:
        raise HTTPException(status_code=400, detail="You already have the organizer role")
    if current_status == "pending":
        raise HTTPException(status_code=400, detail="Organizer role request already pending admin approval")
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {
            "organizer_status":        "pending",
            "organizer_requested_at":  datetime.utcnow(),
            "updated_at":              datetime.utcnow(),
        }},
    )
    return {"message": "Organizer role request submitted. Awaiting admin approval."}


@router.post("/request-professional-role")
async def request_professional_role(
    data: RoleRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    User requests the Professional role.
    Sets professional_status='pending_payment'.
    Admin confirms fee payment via POST /api/admin/confirm-professional-fee/{user_id}.
    professional_type must be provided (e.g. Coach, Umpire, Trainer).
    """
    db = get_database()
    roles = current_user.get("roles", [])
    if "professional" in roles and current_user.get("professional_status") == "active":
        raise HTTPException(status_code=400, detail="You already have an active professional role")
    if current_user.get("professional_status") == "pending_payment":
        raise HTTPException(status_code=400, detail="Professional fee payment already pending")
    if not data.professional_type:
        raise HTTPException(status_code=400, detail="professional_type is required (e.g. Coach, Umpire, Trainer)")
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {
            "professional_status":   "pending_payment",
            "professional_type":     data.professional_type,
            "updated_at":            datetime.utcnow(),
        }},
    )
    return {
        "message": "Professional role request submitted.",
        "next_step": "Pay the one-time fee of ₹3000. Contact admin or use the payment link provided in the app.",
        "professional_type": data.professional_type,
        "fee_amount": 3000,
        "currency": "INR",
    }


@router.post("/confirm-professional-payment")
async def confirm_professional_payment(
    current_user: dict = Depends(get_current_user),
):
    """
    Called by the app after the in-app mock payment flow succeeds.
    Activates the professional role immediately (no admin approval needed for
    self-serve payment). In production, replace or supplement with a real
    payment-gateway webhook.
    """
    db = get_database()
    roles = current_user.get("roles", [])
    if "professional" in roles and current_user.get("professional_status") == "active":
        raise HTTPException(status_code=400, detail="Professional role already active")

    new_roles = roles if "professional" in roles else roles + ["professional"]
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {
            "roles":                 new_roles,
            "role":                  "professional",
            "professional_status":   "active",
            "professional_fee_paid": True,
            "updated_at":            datetime.utcnow(),
        }},
    )
    updated = await db.users.find_one({"_id": current_user["_id"]})
    return _user_dict(updated, include_private=True)


@router.post("/add-role")
async def add_role(
    data: RoleRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Add an additional role to the user's roles list (player/parent only — no approval).
    Organiser and Professional roles go through their own request endpoints.
    """
    db = get_database()
    if data.role in ("organizer", "professional", "admin", "super_admin"):
        raise HTTPException(
            status_code=403,
            detail=f"Use /request-organizer-role or /request-professional-role for restricted roles."
        )
    allowed = {"player", "parent"}
    if data.role not in allowed:
        raise HTTPException(status_code=400, detail=f"Role must be one of: {', '.join(allowed)}")
    roles = current_user.get("roles", [])
    if data.role in roles:
        raise HTTPException(status_code=400, detail=f"You already have the '{data.role}' role")
    roles.append(data.role)
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"roles": roles, "role": roles[0], "updated_at": datetime.utcnow()}},
    )
    return {"message": f"Role '{data.role}' added", "roles": roles}


# ─── PUBLIC USER PROFILES ─────────────────────────────────────────────────────

@router.get("/users/search")
async def search_users(
    query: str,
    role: Optional[str] = None,
    city: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
):
    db   = get_database()
    filt = {"is_active": True}
    if query:
        filt["name"] = {"$regex": query, "$options": "i"}
    if role:
        filt["roles"] = role   # matches if role is in the array
    if city:
        filt["city"] = {"$regex": city, "$options": "i"}
    cursor  = db.users.find(filt).skip(skip).limit(limit)
    users   = await cursor.to_list(length=limit)
    results = []
    for u in users:
        roles = u.get("roles", [])
        results.append({
            "id":               str(u["_id"]),
            "name":             u.get("name", "Anonymous"),
            "role":             roles[0] if roles else u.get("role"),
            "roles":            roles,
            "professional_type":u.get("professional_type"),
            "city":             u.get("city"),
            "state":            u.get("state"),
            "bio":              u.get("bio"),
            "avatar":           u.get("avatar"),
            "sports_interests": u.get("sports_interests", []),
            "is_verified":      u.get("is_verified", False),
        })
    return {"results": results, "total": len(results)}


@router.get("/users/{user_id}")
async def get_user_by_id(user_id: str):
    db = get_database()
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    roles = user.get("roles", [])

    tournaments = []
    try:
        t_cursor = db.tournaments.find({"organizer_id": user_id, "is_active": True}).sort("start_date", -1).limit(10)
        for t in await t_cursor.to_list(length=10):
            tournaments.append({
                "id": str(t["_id"]), "name": t.get("name"),
                "sport_type": t.get("sport_type"), "city": t.get("city"),
                "start_date": t.get("start_date"), "status": t.get("status"),
                "banner_image": t.get("banner_image"), "entry_fee": t.get("entry_fee"),
                "max_teams": t.get("max_teams"), "current_teams": t.get("current_teams", 0),
                "is_featured": t.get("is_featured", False),
            })
    except Exception as e:
        print(f"[AUTH] Error fetching tournaments: {e}")

    jobs = []
    try:
        j_cursor = db.jobs.find({"posted_by": user_id, "status": "active"}).sort("created_at", -1).limit(10)
        for j in await j_cursor.to_list(length=10):
            jobs.append({
                "id": str(j["_id"]), "title": j.get("title"),
                "job_type": j.get("job_type"), "sport_type": j.get("sport_type"),
                "city": j.get("city"), "banner_image": j.get("banner_image"),
                "employment_type": j.get("employment_type"),
                "salary_min": j.get("salary_min"), "salary_max": j.get("salary_max"),
            })
    except Exception as e:
        print(f"[AUTH] Error fetching jobs: {e}")

    return {
        "id":               str(user["_id"]),
        "name":             user.get("name", "Anonymous"),
        "role":             roles[0] if roles else user.get("role"),
        "roles":            roles,
        "professional_type":user.get("professional_type"),
        "city":             user.get("city"),
        "state":            user.get("state"),
        "bio":              user.get("bio"),
        "avatar":           user.get("avatar"),
        "sports_interests": user.get("sports_interests", []),
        "player_position":  user.get("player_position"),
        "playing_style":    user.get("playing_style"),
        "certification":    user.get("certification"),
        "experience_years": user.get("experience_years"),
        "is_verified":      user.get("is_verified", False),
        "created_at":       user.get("created_at"),
        "tournaments":      tournaments,
        "jobs":             jobs,
    }


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    return {"message": "Logged out successfully. Clear your local token."}
