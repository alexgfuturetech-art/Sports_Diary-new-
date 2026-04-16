from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime
from bson import ObjectId

from app.core.database import get_database
from app.core.security import get_current_user

router = APIRouter(tags=["reviews"])


@router.post("/{entity_type}/{entity_id}")
async def create_review(
    entity_type: str,
    entity_id: str,
    rating: int,
    comment: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Create a review for any entity (venue, tournament, shop, academy)"""
    db = get_database()
    
    # Validate rating
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    # Validate entity type
    valid_types = ["venue", "tournament", "shop", "academy"]
    if entity_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid entity type. Must be one of: {', '.join(valid_types)}")
    
    # Check if entity exists
    collection_map = {
        "venue": "venues",
        "tournament": "tournaments",
        "shop": "shops",
        "academy": "dictionary"
    }
    
    collection_name = collection_map[entity_type]
    
    try:
        entity = await db[collection_name].find_one({"_id": ObjectId(entity_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid entity ID")
    
    if not entity:
        raise HTTPException(status_code=404, detail=f"{entity_type.capitalize()} not found")
    
    # Check if user already reviewed this entity
    existing_review = await db.reviews.find_one({
        "entity_type": entity_type,
        "entity_id": entity_id,
        "user_id": str(current_user["_id"])
    })
    
    if existing_review:
        # Update existing review
        await db.reviews.update_one(
            {"_id": existing_review["_id"]},
            {
                "$set": {
                    "rating": rating,
                    "comment": comment,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        review_id = existing_review["_id"]
        message = "Review updated successfully"
    else:
        # Create new review
        review_dict = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "user_id": str(current_user["_id"]),
            "user_name": current_user.get("name", "Anonymous"),
            "user_avatar": current_user.get("avatar"),
            "rating": rating,
            "comment": comment,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        
        result = await db.reviews.insert_one(review_dict)
        review_id = result.inserted_id
        message = "Review created successfully"
    
    # Update entity's average rating and review count
    await update_entity_rating(db, entity_type, entity_id)
    
    return {
        "message": message,
        "review_id": str(review_id)
    }


@router.get("/{entity_type}/{entity_id}")
async def get_reviews(
    entity_type: str,
    entity_id: str,
    skip: int = 0,
    limit: int = 4
):
    """Get reviews for any entity"""
    db = get_database()
    
    reviews_cursor = db.reviews.find({
        "entity_type": entity_type,
        "entity_id": entity_id,
        "is_active": True
    }).sort([("created_at", -1)]).skip(skip).limit(limit)
    
    reviews = await reviews_cursor.to_list(length=limit)
    
    for review in reviews:
        review["id"] = str(review["_id"])
        del review["_id"]
    
    # Get average rating and total count
    total_reviews = await db.reviews.count_documents({
        "entity_type": entity_type,
        "entity_id": entity_id,
        "is_active": True
    })
    
    # Calculate average rating
    pipeline = [
        {
            "$match": {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "is_active": True
            }
        },
        {
            "$group": {
                "_id": None,
                "average_rating": {"$avg": "$rating"}
            }
        }
    ]
    
    rating_result = await db.reviews.aggregate(pipeline).to_list(length=1)
    average_rating = rating_result[0]["average_rating"] if rating_result else 0
    
    return {
        "reviews": reviews,
        "total_reviews": total_reviews,
        "average_rating": round(average_rating, 1)
    }


@router.get("/{entity_type}/{entity_id}/user-review")
async def get_user_review(
    entity_type: str,
    entity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get current user's review for an entity"""
    db = get_database()
    
    review = await db.reviews.find_one({
        "entity_type": entity_type,
        "entity_id": entity_id,
        "user_id": str(current_user["_id"]),
        "is_active": True
    })
    
    if not review:
        return None
    
    review["id"] = str(review["_id"])
    del review["_id"]
    
    return review


@router.delete("/{entity_type}/{entity_id}")
async def delete_review(
    entity_type: str,
    entity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete user's review"""
    db = get_database()
    
    result = await db.reviews.delete_one({
        "entity_type": entity_type,
        "entity_id": entity_id,
        "user_id": str(current_user["_id"])
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Update entity's average rating
    await update_entity_rating(db, entity_type, entity_id)
    
    return {"message": "Review deleted successfully"}


async def update_entity_rating(db, entity_type: str, entity_id: str):
    """Update entity's average rating and review count"""
    # Calculate average rating
    pipeline = [
        {
            "$match": {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "is_active": True
            }
        },
        {
            "$group": {
                "_id": None,
                "average_rating": {"$avg": "$rating"},
                "count": {"$sum": 1}
            }
        }
    ]
    
    result = await db.reviews.aggregate(pipeline).to_list(length=1)
    
    if result:
        average_rating = result[0]["average_rating"]
        count = result[0]["count"]
    else:
        average_rating = 0
        count = 0
    
    # Update entity
    collection_map = {
        "venue": "venues",
        "tournament": "tournaments",
        "shop": "shops",
        "academy": "dictionary"
    }
    
    collection_name = collection_map[entity_type]
    
    try:
        await db[collection_name].update_one(
            {"_id": ObjectId(entity_id)},
            {
                "$set": {
                    "rating": round(average_rating, 1),
                    "total_reviews": count
                }
            }
        )
    except:
        pass  # Entity might not exist anymore

