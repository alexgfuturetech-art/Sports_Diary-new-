#!/usr/bin/env python3
"""
Seed missing collections to MongoDB Atlas
Missing: communities, organizer_teams, posts, reviews, teams, tournament_registrations
Usage: python seed_missing_collections.py
"""

import os
import sys
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

# Fix Unicode encoding on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")

if not MONGODB_URL:
    print("[ERROR] MONGODB_URL not found in .env file")
    print("[HELP] Add MONGODB_URL to backend/.env")
    exit(1)

print("[*] Connecting to MongoDB Atlas...\n")

try:
    client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("[OK] Connected to MongoDB Atlas\n")
except Exception as e:
    print(f"[ERROR] Connection failed: {e}")
    exit(1)

db = client['sports_diary']

# Get existing users for references
users_list = list(db.users.find({}))
if not users_list:
    print("[ERROR] No users found in database")
    print("[HELP] Run: python seed_data.py first")
    exit(1)

user_ids = [str(u["_id"]) for u in users_list]
print(f"[INFO] Found {len(users_list)} users\n")

def seed_communities():
    """Create communities"""
    print("[*] Seeding communities...")
    communities = [
        {
            "_id": ObjectId(),
            "name": "Cricket Enthusiasts",
            "description": "Community for cricket lovers and players",
            "sport_type": "Cricket",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "members": user_ids[:2] if len(user_ids) >= 2 else user_ids,
            "member_count": min(2, len(user_ids)),
            "created_by": user_ids[0],
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Badminton Players",
            "description": "Connect with badminton players in your area",
            "sport_type": "Badminton",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "members": [user_ids[1]] if len(user_ids) > 1 else user_ids,
            "member_count": 1,
            "created_by": user_ids[1] if len(user_ids) > 1 else user_ids[0],
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Football Community",
            "description": "Football players and fans community",
            "sport_type": "Football",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "members": [user_ids[0]],
            "member_count": 1,
            "created_by": user_ids[0],
            "is_active": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    db.communities.insert_many(communities)
    print(f"  [OK] Created {len(communities)} communities\n")
    return communities

def seed_teams(users_list):
    """Create teams"""
    print("[*] Seeding teams...")
    teams = [
        {
            "_id": ObjectId(),
            "name": "Cricket Warriors",
            "short_name": "CW",
            "sport_type": "Cricket",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "captain_id": user_ids[0],
            "players": [{"user_id": user_ids[0], "name": users_list[0].get("name", "Player 1")}],
            "total_players": 1,
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Badminton Stars",
            "short_name": "BS",
            "sport_type": "Badminton",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "captain_id": user_ids[1] if len(user_ids) > 1 else user_ids[0],
            "players": [{"user_id": user_ids[1] if len(user_ids) > 1 else user_ids[0], "name": users_list[1].get("name", "Player 2") if len(users_list) > 1 else users_list[0].get("name", "Player")}],
            "total_players": 1,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    db.teams.insert_many(teams)
    print(f"  [OK] Created {len(teams)} teams\n")
    return teams

def seed_reviews(users_list):
    """Create reviews"""
    print("[*] Seeding reviews...")
    
    # Get venues for references
    venues_list = list(db.venues.find({}))
    if not venues_list:
        print("  [WARNING] No venues found, skipping reviews")
        return []
    
    venue_ids = [str(v["_id"]) for v in venues_list]
    
    reviews = [
        {
            "_id": ObjectId(),
            "venue_id": venue_ids[0],
            "user_id": user_ids[1] if len(user_ids) > 1 else user_ids[0],
            "rating": 5,
            "review_text": "Great venue with excellent facilities",
            "is_verified": True,
            "helpful_count": 0,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "venue_id": venue_ids[1] if len(venue_ids) > 1 else venue_ids[0],
            "user_id": user_ids[2] if len(user_ids) > 2 else user_ids[0],
            "rating": 4,
            "review_text": "Good courts, friendly staff",
            "is_verified": True,
            "helpful_count": 0,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "venue_id": venue_ids[2] if len(venue_ids) > 2 else venue_ids[0],
            "user_id": user_ids[0],
            "rating": 5,
            "review_text": "Amazing experience, will come again",
            "is_verified": True,
            "helpful_count": 0,
            "created_at": datetime.utcnow()
        }
    ]
    
    db.reviews.insert_many(reviews)
    print(f"  [OK] Created {len(reviews)} reviews\n")
    return reviews

def seed_posts():
    """Create posts"""
    print("[*] Seeding posts...")
    posts = [
        {
            "_id": ObjectId(),
            "title": "Cricket Tournament Announcement",
            "content": "Join our upcoming cricket tournament in Ahmedabad",
            "author_id": user_ids[0],
            "category": "Tournament",
            "sport_type": "Cricket",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "likes": 0,
            "comments": 0,
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "title": "Badminton Tips and Tricks",
            "content": "Learn the best badminton techniques from professionals",
            "author_id": user_ids[1] if len(user_ids) > 1 else user_ids[0],
            "category": "Tips",
            "sport_type": "Badminton",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "likes": 0,
            "comments": 0,
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "title": "New Venue Opening",
            "content": "Exciting new sports venue opening in Ahmedabad",
            "author_id": user_ids[0],
            "category": "News",
            "sport_type": "Multi-sport",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "likes": 0,
            "comments": 0,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    db.posts.insert_many(posts)
    print(f"  [OK] Created {len(posts)} posts\n")
    return posts

def seed_organizer_teams():
    """Create organizer teams"""
    print("[*] Seeding organizer_teams...")
    teams = [
        {
            "_id": ObjectId(),
            "organizer_id": user_ids[0],
            "name": "Tournament Organizers",
            "description": "Team for organizing tournaments",
            "members": [user_ids[0]],
            "member_count": 1,
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "organizer_id": user_ids[0],
            "name": "Event Managers",
            "description": "Team for managing sports events",
            "members": [user_ids[0], user_ids[1]] if len(user_ids) > 1 else [user_ids[0]],
            "member_count": min(2, len(user_ids)),
            "is_active": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    db.organizer_teams.insert_many(teams)
    print(f"  [OK] Created {len(teams)} organizer_teams\n")
    return teams

def seed_tournament_registrations():
    """Create tournament registrations"""
    print("[*] Seeding tournament_registrations...")
    
    # Get tournaments for references
    tournaments_list = list(db.tournaments.find({}))
    if not tournaments_list:
        print("  [WARNING] No tournaments found, skipping registrations")
        return []
    
    # Get teams for references
    teams_list = list(db.teams.find({}))
    if not teams_list:
        print("  [WARNING] No teams found, skipping registrations")
        return []
    
    tournament_ids = [str(t["_id"]) for t in tournaments_list]
    team_ids = [str(t["_id"]) for t in teams_list]
    
    registrations = [
        {
            "_id": ObjectId(),
            "registration_number": "REG001",
            "tournament_id": tournament_ids[0],
            "team_id": team_ids[0],
            "registered_by": user_ids[0],
            "registration_date": datetime.utcnow(),
            "captain_name": users_list[0].get("name", "Captain"),
            "captain_contact": users_list[0].get("phone", "9876543210"),
            "entry_fee": 5000,
            "payment_status": "paid",
            "status": "approved",
            "approval_date": datetime.utcnow(),
            "approved_by": user_ids[0],
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "registration_number": "REG002",
            "tournament_id": tournament_ids[1] if len(tournament_ids) > 1 else tournament_ids[0],
            "team_id": team_ids[1] if len(team_ids) > 1 else team_ids[0],
            "registered_by": user_ids[1] if len(user_ids) > 1 else user_ids[0],
            "registration_date": datetime.utcnow(),
            "captain_name": users_list[1].get("name", "Captain") if len(users_list) > 1 else users_list[0].get("name", "Captain"),
            "captain_contact": users_list[1].get("phone", "9876543211") if len(users_list) > 1 else users_list[0].get("phone", "9876543210"),
            "entry_fee": 1000,
            "payment_status": "pending",
            "status": "pending",
            "created_at": datetime.utcnow()
        }
    ]
    
    db.tournament_registrations.insert_many(registrations)
    print(f"  [OK] Created {len(registrations)} tournament_registrations\n")
    return registrations

def main():
    """Run all seed functions"""
    try:
        print("[*] Starting to seed missing collections...\n")
        
        communities = seed_communities()
        teams = seed_teams(users_list)
        reviews = seed_reviews(users_list)
        posts = seed_posts()
        organizer_teams = seed_organizer_teams()
        tournament_registrations = seed_tournament_registrations()
        
        print("[SUCCESS] Missing collections seeded successfully!\n")
        print("[*] Summary:")
        print(f"  - communities: {len(communities)}")
        print(f"  - teams: {len(teams)}")
        print(f"  - reviews: {len(reviews)}")
        print(f"  - posts: {len(posts)}")
        print(f"  - organizer_teams: {len(organizer_teams)}")
        print(f"  - tournament_registrations: {len(tournament_registrations)}")
        
        print("\n[NEXT] Run: python check_atlas_collections.py")
        
    except Exception as e:
        print(f"[ERROR] Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()
