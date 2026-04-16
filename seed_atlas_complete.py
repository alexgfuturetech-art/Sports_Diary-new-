#!/usr/bin/env python3
"""
Complete seed script for MongoDB Atlas - Creates ALL collections with dummy data
Usage: python seed_atlas_complete.py
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

def seed_users():
    """Create users"""
    print("[*] Seeding users...")
    users = [
        {
            "_id": ObjectId(),
            "phone": "9876543210",
            "name": "Rajesh Kumar",
            "email": "rajesh@example.com",
            "role": "organizer",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "onboarding_completed": True,
            "sports_interests": ["Cricket", "Football"],
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "phone": "9876543211",
            "name": "Priya Singh",
            "email": "priya@example.com",
            "role": "player",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "onboarding_completed": True,
            "sports_interests": ["Badminton", "Tennis"],
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "phone": "9876543212",
            "name": "Amit Patel",
            "email": "amit@example.com",
            "role": "professional",
            "professional_type": "Coach",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "onboarding_completed": True,
            "sports_interests": ["Cricket"],
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    db.users.insert_many(users)
    print(f"  [OK] Created {len(users)} users")
    return users

def seed_venues(users):
    """Create venues"""
    print("[*] Seeding venues...")
    venues = [
        {
            "_id": ObjectId(),
            "name": "Ahmedabad Cricket Ground",
            "description": "Premium cricket venue",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0225,
            "longitude": 72.5714,
            "price_per_hour": 5000,
            "owner_id": str(users[0]["_id"]),
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Badminton Court Complex",
            "description": "Indoor badminton courts",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0300,
            "longitude": 72.5800,
            "price_per_hour": 1500,
            "owner_id": str(users[0]["_id"]),
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Football Stadium",
            "description": "Full-size football field",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0150,
            "longitude": 72.5600,
            "price_per_hour": 3000,
            "owner_id": str(users[0]["_id"]),
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    db.venues.insert_many(venues)
    print(f"  [OK] Created {len(venues)} venues")
    return venues

def seed_tournaments(users, venues):
    """Create tournaments"""
    print("[*] Seeding tournaments...")
    tournaments = [
        {
            "_id": ObjectId(),
            "name": "Gujarat Cricket Championship 2026",
            "description": "Annual cricket tournament",
            "sport_type": "Cricket",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "venue_id": str(venues[0]["_id"]),
            "organizer_id": str(users[0]["_id"]),
            "start_date": datetime.utcnow() + timedelta(days=30),
            "registration_deadline": datetime.utcnow() + timedelta(days=20),
            "max_teams": 16,
            "current_teams": 8,
            "entry_fee": 5000,
            "status": "upcoming",
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Badminton Open 2026",
            "description": "Open badminton tournament",
            "sport_type": "Badminton",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "venue_id": str(venues[1]["_id"]),
            "organizer_id": str(users[0]["_id"]),
            "start_date": datetime.utcnow() + timedelta(days=15),
            "registration_deadline": datetime.utcnow() + timedelta(days=10),
            "max_teams": 32,
            "current_teams": 20,
            "entry_fee": 1000,
            "status": "upcoming",
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    db.tournaments.insert_many(tournaments)
    print(f"  [OK] Created {len(tournaments)} tournaments")
    return tournaments

def seed_shops():
    """Create shops"""
    print("[*] Seeding shops...")
    shops = [
        {
            "_id": ObjectId(),
            "name": "Sports Pro Store",
            "description": "Premium sports equipment",
            "category": "Equipment",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0225,
            "longitude": 72.5714,
            "phone": "9876543220",
            "email": "sportspro@example.com",
            "is_active": True,
            "is_verified": True,
            "rating": 4.5,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Cricket Gear Hub",
            "description": "Cricket equipment",
            "category": "Cricket",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0300,
            "longitude": 72.5800,
            "phone": "9876543221",
            "email": "cricketgear@example.com",
            "is_active": True,
            "is_verified": True,
            "rating": 4.7,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Fitness World",
            "description": "Gym equipment",
            "category": "Fitness",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0150,
            "longitude": 72.5600,
            "phone": "9876543222",
            "email": "fitnessworld@example.com",
            "is_active": True,
            "is_verified": True,
            "is_featured": True,
            "rating": 4.8,
            "created_at": datetime.utcnow()
        }
    ]
    
    db.shops.insert_many(shops)
    print(f"  [OK] Created {len(shops)} shops")
    return shops

def seed_jobs():
    """Create jobs"""
    print("[*] Seeding jobs...")
    jobs = [
        {
            "_id": ObjectId(),
            "title": "Cricket Coach",
            "description": "Experienced cricket coach needed",
            "sport_type": "Cricket",
            "job_type": "Full-time",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "salary_min": 30000,
            "salary_max": 50000,
            "status": "active",
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "title": "Badminton Trainer",
            "description": "Professional badminton trainer",
            "sport_type": "Badminton",
            "job_type": "Part-time",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "salary_min": 15000,
            "salary_max": 25000,
            "status": "active",
            "is_active": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    db.jobs.insert_many(jobs)
    print(f"  [OK] Created {len(jobs)} jobs")
    return jobs

def seed_communities(users):
    """Create communities"""
    print("[*] Seeding communities...")
    communities = [
        {
            "_id": ObjectId(),
            "name": "Cricket Enthusiasts",
            "description": "Community for cricket lovers",
            "sport_type": "Cricket",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "members": [str(users[0]["_id"]), str(users[1]["_id"])],
            "member_count": 2,
            "created_by": str(users[0]["_id"]),
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Badminton Players",
            "description": "Connect with badminton players",
            "sport_type": "Badminton",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "members": [str(users[1]["_id"])],
            "member_count": 1,
            "created_by": str(users[1]["_id"]),
            "is_active": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    db.communities.insert_many(communities)
    print(f"  [OK] Created {len(communities)} communities")
    return communities

def seed_dictionary():
    """Create dictionary entries (academies)"""
    print("[*] Seeding dictionary (academies)...")
    entries = [
        {
            "_id": ObjectId(),
            "term": "Ahmedabad Sports Academy",
            "sport": "Cricket",
            "category": "Academy",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "definition": "Premier cricket coaching academy",
            "is_active": True,
            "is_featured": True,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "term": "Elite Football Academy",
            "sport": "Football",
            "category": "Academy",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "definition": "Professional football training academy",
            "is_active": True,
            "is_featured": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    db.dictionary.insert_many(entries)
    print(f"  [OK] Created {len(entries)} dictionary entries")
    return entries

def seed_reviews(users, venues):
    """Create reviews"""
    print("[*] Seeding reviews...")
    reviews = [
        {
            "_id": ObjectId(),
            "venue_id": str(venues[0]["_id"]),
            "user_id": str(users[1]["_id"]),
            "rating": 5,
            "review_text": "Great venue with excellent facilities",
            "is_verified": True,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "venue_id": str(venues[1]["_id"]),
            "user_id": str(users[2]["_id"]),
            "rating": 4,
            "review_text": "Good courts, friendly staff",
            "is_verified": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    db.reviews.insert_many(reviews)
    print(f"  [OK] Created {len(reviews)} reviews")
    return reviews

def seed_bookings(users, venues):
    """Create bookings"""
    print("[*] Seeding bookings...")
    bookings = [
        {
            "_id": ObjectId(),
            "booking_number": "BK001",
            "user_id": str(users[0]["_id"]),
            "venue_id": str(venues[0]["_id"]),
            "booking_date": datetime.utcnow().date().isoformat(),
            "start_time": "18:00",
            "end_time": "19:00",
            "base_price": 5000,
            "total_amount": 5000,
            "status": "confirmed",
            "payment_status": "paid",
            "created_at": datetime.utcnow()
        }
    ]
    
    db.bookings.insert_many(bookings)
    print(f"  [OK] Created {len(bookings)} bookings")
    return bookings

def seed_teams(users):
    """Create teams"""
    print("[*] Seeding teams...")
    teams = [
        {
            "_id": ObjectId(),
            "name": "Cricket Warriors",
            "sport_type": "Cricket",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "captain_id": str(users[0]["_id"]),
            "players": [str(users[0]["_id"]), str(users[1]["_id"])],
            "total_players": 2,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    db.teams.insert_many(teams)
    print(f"  [OK] Created {len(teams)} teams")
    return teams

def seed_professional_availability(users):
    """Create professional availability"""
    print("[*] Seeding professional availability...")
    availability = [
        {
            "_id": ObjectId(),
            "professional_id": str(users[2]["_id"]),
            "professional_name": "Amit Patel",
            "professional_type": "Coach",
            "sport_type": "Cricket",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "available_from_date": datetime.utcnow(),
            "per_match_fee": 5000,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    db.professional_availability.insert_many(availability)
    print(f"  [OK] Created {len(availability)} professional availability records")
    return availability

def seed_organizer_teams(users):
    """Create organizer teams"""
    print("[*] Seeding organizer teams...")
    teams = [
        {
            "_id": ObjectId(),
            "organizer_id": str(users[0]["_id"]),
            "name": "Tournament Organizers",
            "members": [str(users[0]["_id"])],
            "is_active": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    db.organizer_teams.insert_many(teams)
    print(f"  [OK] Created {len(teams)} organizer teams")
    return teams

def main():
    """Run all seed functions"""
    try:
        print("[*] Starting complete database seeding...\n")
        
        users = seed_users()
        venues = seed_venues(users)
        tournaments = seed_tournaments(users, venues)
        shops = seed_shops()
        jobs = seed_jobs()
        communities = seed_communities(users)
        dictionary = seed_dictionary()
        reviews = seed_reviews(users, venues)
        bookings = seed_bookings(users, venues)
        teams = seed_teams(users)
        professional_availability = seed_professional_availability(users)
        organizer_teams = seed_organizer_teams(users)
        
        print("\n[SUCCESS] Database seeding completed!\n")
        print("[*] Summary:")
        print(f"  - Users: {len(users)}")
        print(f"  - Venues: {len(venues)}")
        print(f"  - Tournaments: {len(tournaments)}")
        print(f"  - Shops: {len(shops)}")
        print(f"  - Jobs: {len(jobs)}")
        print(f"  - Communities: {len(communities)}")
        print(f"  - Dictionary: {len(dictionary)}")
        print(f"  - Reviews: {len(reviews)}")
        print(f"  - Bookings: {len(bookings)}")
        print(f"  - Teams: {len(teams)}")
        print(f"  - Professional Availability: {len(professional_availability)}")
        print(f"  - Organizer Teams: {len(organizer_teams)}")
        
        # Verify collections
        collections = db.list_collection_names()
        print(f"\n[INFO] Total collections created: {len(collections)}")
        
    except Exception as e:
        print(f"[ERROR] Seeding failed: {e}")
        raise

if __name__ == "__main__":
    main()
