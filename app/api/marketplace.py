from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from app.core.database import get_database
from app.core.security import get_current_user
from app.schemas.schemas import (
    ShopCreate, ShopUpdate, ShopResponse,
    JobCreate, JobUpdate, JobResponse,
    JobApplicationCreate, JobApplicationUpdate,
)

router = APIRouter(tags=["marketplace"])


# ==================== SHOPS ENDPOINTS ====================

@router.get("/shops")
async def get_shops(
    city: Optional[str] = None,
    category: Optional[str] = None,
    shop_type: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    """Get list of sports shops with filters"""
    db = get_database()
    
    query = {"is_active": True}
    
    if city:
        query["city"] = city
    if category:
        query["category"] = category
    if shop_type:
        query["shop_type"] = shop_type
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    # Get total count before limiting
    total_count = await db.shops.count_documents(query)
    
    shops_cursor = db.shops.find(query).skip(skip).limit(limit).sort([("is_featured", -1), ("rating", -1)])
    shops = await shops_cursor.to_list(length=limit)
    
    for shop in shops:
        shop["id"] = str(shop["_id"])
        del shop["_id"]  # Remove ObjectId
    
    return {"shops": shops, "count": total_count}


@router.get("/shops/{shop_id}")
async def get_shop(shop_id: str):
    """Get shop details"""
    db = get_database()
    
    try:
        shop = await db.shops.find_one({"_id": ObjectId(shop_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid shop ID")
    
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    # Increment enquiry count
    await db.shops.update_one(
        {"_id": ObjectId(shop_id)},
        {"$inc": {"total_enquiries": 1}}
    )
    
    shop["id"] = str(shop["_id"])

    
    del shop["_id"]  # Remove ObjectId
    return shop


@router.post("/shops")
async def create_shop(
    shop_data: ShopCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new shop listing"""
    db = get_database()
    
    shop_dict = shop_data.dict()
    shop_dict["owner_id"] = str(current_user["_id"])
    shop_dict["created_at"] = datetime.utcnow()
    shop_dict["updated_at"] = datetime.utcnow()
    shop_dict["is_active"] = True
    shop_dict["rating"] = 0.0
    shop_dict["total_reviews"] = 0
    shop_dict["total_enquiries"] = 0
    
    result = await db.shops.insert_one(shop_dict)
    created_shop = await db.shops.find_one({"_id": result.inserted_id})
    created_shop["id"] = str(created_shop["_id"])

    del created_shop["_id"]  # Remove ObjectId
    
    return created_shop


@router.put("/shops/{shop_id}")
async def update_shop(
    shop_id: str,
    shop_data: ShopUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update shop"""
    db = get_database()
    
    try:
        shop = await db.shops.find_one({"_id": ObjectId(shop_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid shop ID")
    
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    # Check ownership
    if str(shop.get("owner_id")) != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {k: v for k, v in shop_data.dict(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.shops.update_one(
        {"_id": ObjectId(shop_id)},
        {"$set": update_data}
    )
    
    updated_shop = await db.shops.find_one({"_id": ObjectId(shop_id)})
    updated_shop["id"] = str(updated_shop["_id"])

    del updated_shop["_id"]  # Remove ObjectId
    
    return updated_shop


@router.delete("/shops/{shop_id}")
async def delete_shop(
    shop_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete/deactivate shop"""
    db = get_database()
    
    try:
        shop = await db.shops.find_one({"_id": ObjectId(shop_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid shop ID")
    
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    # Check ownership
    if str(shop.get("owner_id")) != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Soft delete
    await db.shops.update_one(
        {"_id": ObjectId(shop_id)},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Shop deleted successfully"}


# ==================== JOBS ENDPOINTS ====================

@router.get("/jobs")
async def get_jobs(
    city: Optional[str] = None,
    job_type: Optional[str] = None,
    sport_type: Optional[str] = None,
    employment_type: Optional[str] = None,
    status: Optional[str] = "active",
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    """Get list of job postings with filters"""
    db = get_database()
    
    query = {}
    
    if status:
        query["status"] = status
    if city:
        query["city"] = city
    if job_type:
        query["job_type"] = job_type
    if sport_type:
        query["sport_type"] = sport_type
    if employment_type:
        query["employment_type"] = employment_type
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    # Get total count before limiting
    total_count = await db.jobs.count_documents(query)
    
    jobs_cursor = db.jobs.find(query).skip(skip).limit(limit).sort([("is_featured", -1), ("created_at", -1)])
    jobs = await jobs_cursor.to_list(length=limit)
    
    for job in jobs:
        job["id"] = str(job["_id"])
        del job["_id"]  # Remove ObjectId
    
    return {"jobs": jobs, "count": total_count}


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Get job details"""
    db = get_database()
    
    try:
        job = await db.jobs.find_one({"_id": ObjectId(job_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid job ID")
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Increment views count
    await db.jobs.update_one(
        {"_id": ObjectId(job_id)},
        {"$inc": {"views_count": 1}}
    )
    
    job["id"] = str(job["_id"])

    
    del job["_id"]  # Remove ObjectId
    return job


@router.post("/jobs")
async def create_job(
    job_data: JobCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new job posting"""
    db = get_database()
    
    job_dict = job_data.dict()
    job_dict["posted_by"] = str(current_user["_id"])
    job_dict["created_at"] = datetime.utcnow()
    job_dict["updated_at"] = datetime.utcnow()
    job_dict["status"] = "active"
    job_dict["views_count"] = 0
    job_dict["applications_count"] = 0
    
    result = await db.jobs.insert_one(job_dict)
    created_job = await db.jobs.find_one({"_id": result.inserted_id})
    created_job["id"] = str(created_job["_id"])

    del created_job["_id"]  # Remove ObjectId
    
    return created_job


@router.put("/jobs/{job_id}")
async def update_job(
    job_id: str,
    job_data: JobUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update job"""
    db = get_database()
    
    try:
        job = await db.jobs.find_one({"_id": ObjectId(job_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid job ID")
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check ownership
    if str(job["posted_by"]) != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {k: v for k, v in job_data.dict(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.jobs.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": update_data}
    )
    
    updated_job = await db.jobs.find_one({"_id": ObjectId(job_id)})
    updated_job["id"] = str(updated_job["_id"])

    del updated_job["_id"]  # Remove ObjectId
    
    return updated_job


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete job posting"""
    db = get_database()
    
    try:
        job = await db.jobs.find_one({"_id": ObjectId(job_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid job ID")
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check ownership
    if str(job["posted_by"]) != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update status to closed
    await db.jobs.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {"status": "closed", "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Job posting deleted successfully"}


# ==================== JOB APPLICATIONS (new) ====================

@router.post("/jobs/{job_id}/apply")
async def apply_for_job(
    job_id: str,
    data: JobApplicationCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Professional applies for a job.
    Only users with 'professional' in their roles list can apply.
    """
    db = get_database()
    roles = current_user.get("roles", [])
    if "professional" not in roles:
        raise HTTPException(
            status_code=403,
            detail="Only professionals can apply for jobs. Request the professional role first."
        )

    try:
        job = await db.jobs.find_one({"_id": ObjectId(job_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job ID")
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get("status") != "active":
        raise HTTPException(status_code=400, detail="This job is no longer accepting applications")

    applicant_id = str(current_user["_id"])
    existing = await db.job_applications.find_one({"job_id": job_id, "applicant_id": applicant_id})
    if existing:
        raise HTTPException(status_code=400, detail="You have already applied for this job")

    app_dict = {
        "job_id":                    job_id,
        "applicant_id":              applicant_id,
        "applicant_name":            current_user.get("name", "Unknown"),
        "applicant_phone":           current_user.get("phone", ""),
        "applicant_professional_type": current_user.get("professional_type"),
        "cover_letter":              data.cover_letter,
        "experience_years":          current_user.get("experience_years"),
        "certification":             current_user.get("certification"),
        "expected_salary":           data.expected_salary,
        "available_from":            data.available_from,
        "status":                    "applied",
        "reviewed_by":               None,
        "reviewed_at":               None,
        "rejection_reason":          None,
        "organizer_notes":           None,
        "created_at":                datetime.utcnow(),
        "updated_at":                datetime.utcnow(),
    }
    result = await db.job_applications.insert_one(app_dict)
    # Increment applications count on job
    await db.jobs.update_one({"_id": ObjectId(job_id)}, {"$inc": {"applications_count": 1}})
    app_dict["id"] = str(result.inserted_id)
    app_dict.pop("_id", None)
    return {"message": "Application submitted successfully", "application": app_dict}


@router.get("/jobs/{job_id}/applications")
async def get_job_applications(
    job_id: str,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Get all applications for a job.
    Only the job poster (organiser) or admin/super_admin can view.
    """
    db = get_database()
    try:
        job = await db.jobs.find_one({"_id": ObjectId(job_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job ID")
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    roles = current_user.get("roles", [])
    user_id = str(current_user["_id"])
    is_admin = any(r in roles for r in ("admin", "super_admin"))
    is_poster = job.get("posted_by") == user_id
    if not is_admin and not is_poster:
        raise HTTPException(status_code=403, detail="Not authorized to view applications for this job")

    query = {"job_id": job_id}
    if status:
        query["status"] = status
    cursor = db.job_applications.find(query).sort("created_at", -1)
    apps   = await cursor.to_list(length=200)

    # Batch-fetch applicant profiles to embed avatar, role, city, experience_years
    if apps:
        applicant_oids = []
        for a in apps:
            try:
                applicant_oids.append(ObjectId(a["applicant_id"]))
            except Exception:
                pass
        if applicant_oids:
            users_cursor = db.users.find(
                {"_id": {"$in": applicant_oids}},
                {"_id": 1, "avatar": 1, "role": 1, "city": 1, "experience_years": 1},
            )
            applicant_map = {str(u["_id"]): u async for u in users_cursor}
        else:
            applicant_map = {}
    else:
        applicant_map = {}

    for a in apps:
        a["id"] = str(a["_id"])
        del a["_id"]
        u = applicant_map.get(a.get("applicant_id", ""), {})
        a["applicant_avatar"] = u.get("avatar")
        a["applicant_role"]   = u.get("role")
        a["applicant_city"]   = u.get("city")
        a["experience_years"] = u.get("experience_years")

    return {"applications": apps, "total": len(apps)}


@router.get("/my-applications")
async def get_my_applications(
    current_user: dict = Depends(get_current_user),
):
    """Get all job applications submitted by the current professional."""
    db = get_database()
    applicant_id = str(current_user["_id"])
    cursor = db.job_applications.find({"applicant_id": applicant_id}).sort("created_at", -1)
    apps   = await cursor.to_list(length=200)
    for a in apps:
        a["id"] = str(a["_id"])
        del a["_id"]
    return {"applications": apps, "total": len(apps)}


@router.put("/applications/{application_id}")
async def update_application_status(
    application_id: str,
    data: JobApplicationUpdate,
    current_user: dict = Depends(get_current_user),
):
    """
    Organiser shortlists / selects / rejects an application.
    """
    db = get_database()
    try:
        app = await db.job_applications.find_one({"_id": ObjectId(application_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid application ID")
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    job = await db.jobs.find_one({"_id": ObjectId(app["job_id"])})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    roles   = current_user.get("roles", [])
    user_id = str(current_user["_id"])
    is_admin  = any(r in roles for r in ("admin", "super_admin"))
    is_poster = job.get("posted_by") == user_id
    if not is_admin and not is_poster:
        raise HTTPException(status_code=403, detail="Not authorized to update this application")

    valid_statuses = {"applied", "shortlisted", "selected", "rejected"}
    if data.status and data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"status must be one of: {valid_statuses}")

    update = {k: v for k, v in data.dict(exclude_unset=True).items() if v is not None}
    update["reviewed_by"]  = user_id
    update["reviewed_at"]  = datetime.utcnow()
    update["updated_at"]   = datetime.utcnow()
    await db.job_applications.update_one({"_id": ObjectId(application_id)}, {"$set": update})

    # If selected, optionally close the job
    if data.status == "selected":
        await db.jobs.update_one(
            {"_id": ObjectId(app["job_id"])},
            {"$set": {"status": "filled", "updated_at": datetime.utcnow()}},
        )
    updated = await db.job_applications.find_one({"_id": ObjectId(application_id)})
    updated["id"] = str(updated["_id"])
    del updated["_id"]
    return updated
