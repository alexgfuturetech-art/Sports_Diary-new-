#!/usr/bin/env python3
"""
Seed script to populate MongoDB Atlas with dummy data
Run: python seed_data.py
"""

import os
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB connection - use environment variable or default
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://admin:admin123@localhost:27017/sports_diary?authSource=admin")
print(f"🔗 Connecting to MongoDB...")

try:
    client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
    # Test connection
    client.admin.command('ping')
    print("✅ MongoDB connection successful!")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    print(f"Please check your MONGODB_URL in .env file")
    exit(1)

db = client['sports_diary']

def clear_collections():
    """Clear existing data"""
    collections = ['users', 'tournaments', 'venues', 'shops', 'jobs', 'communities', 'posts']
    for collection in collections:
        db[collection].delete_many({})
    print("✅ Cleared existing data")

def seed_users():
    """Create dummy users"""
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
            "created_at": datetime.utcnow()
        }
    ]
    
    result = db.users.insert_many(users)
    print(f"✅ Created {len(result.inserted_ids)} users")
    return users

def seed_venues(users):
    """Create dummy venues"""
    venues = [
        {
            "_id": ObjectId(),
            "name": "Ahmedabad Cricket Ground",
            "description": "Premium cricket venue with international standards",
            "sport_type": "Cricket",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0225,
            "longitude": 72.5714,
            "price_per_hour": 5000,
            "amenities": ["Parking", "Cafeteria", "Washrooms"],
            "owner_id": users[0]["_id"],
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Badminton Court Complex",
            "description": "Indoor badminton courts with professional setup",
            "sport_type": "Badminton",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0300,
            "longitude": 72.5800,
            "price_per_hour": 1500,
            "amenities": ["AC", "Parking", "Washrooms"],
            "owner_id": users[0]["_id"],
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Football Stadium",
            "description": "Full-size football field with floodlights",
            "sport_type": "Football",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0150,
            "longitude": 72.5600,
            "price_per_hour": 3000,
            "amenities": ["Floodlights", "Parking", "Cafeteria"],
            "owner_id": users[0]["_id"],
            "created_at": datetime.utcnow()
        }
    ]
    
    result = db.venues.insert_many(venues)
    print(f"✅ Created {len(result.inserted_ids)} venues")
    return venues

def seed_tournaments(users, venues):
    """Create dummy tournaments"""
    tournaments = [
        {
            "_id": ObjectId(),
            "name": "Gujarat Cricket Championship 2026",
            "description": "Annual cricket tournament for all skill levels",
            "sport_type": "Cricket",
            "tournament_type": "League",
            "format": "T20",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "venue_id": venues[0]["_id"],
            "organizer_id": users[0]["_id"],
            "start_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=45)).isoformat(),
            "registration_deadline": (datetime.utcnow() + timedelta(days=20)).isoformat(),
            "max_teams": 16,
            "current_teams": 8,
            "entry_fee": 5000,
            "prize_pool": 100000,
            "status": "Open",
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Badminton Open 2026",
            "description": "Open badminton tournament for singles and doubles",
            "sport_type": "Badminton",
            "tournament_type": "Knockout",
            "format": "Singles & Doubles",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "venue_id": venues[1]["_id"],
            "organizer_id": users[0]["_id"],
            "start_date": (datetime.utcnow() + timedelta(days=15)).isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=20)).isoformat(),
            "registration_deadline": (datetime.utcnow() + timedelta(days=10)).isoformat(),
            "max_teams": 32,
            "current_teams": 20,
            "entry_fee": 1000,
            "prize_pool": 50000,
            "status": "Open",
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Football League 2026",
            "description": "Professional football league tournament",
            "sport_type": "Football",
            "tournament_type": "League",
            "format": "11-a-side",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "venue_id": venues[2]["_id"],
            "organizer_id": users[0]["_id"],
            "start_date": (datetime.utcnow() + timedelta(days=60)).isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=90)).isoformat(),
            "registration_deadline": (datetime.utcnow() + timedelta(days=50)).isoformat(),
            "max_teams": 12,
            "current_teams": 10,
            "entry_fee": 10000,
            "prize_pool": 200000,
            "status": "Open",
            "created_at": datetime.utcnow()
        }
    ]
    
    result = db.tournaments.insert_many(tournaments)
    print(f"✅ Created {len(result.inserted_ids)} tournaments")
    return tournaments

def seed_shops():
    """Create dummy shops with images"""
    shops = [
        {
            "_id": ObjectId(),
            "name": "Sports Pro Store",
            "description": "Premium sports equipment and apparel",
            "category": "Equipment",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0225,
            "longitude": 72.5714,
            "phone": "9876543220",
            "email": "sportspro@example.com",
            "image": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=500&h=500&fit=crop",
            "is_active": True,
            "is_verified": True,
            "is_featured": False,
            "rating": 4.5,
            "total_reviews": 12,
            "total_enquiries": 0,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Cricket Gear Hub",
            "description": "Specialized cricket equipment and accessories",
            "category": "Cricket",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0300,
            "longitude": 72.5800,
            "phone": "9876543221",
            "email": "cricketgear@example.com",
            "image": "https://images.unsplash.com/photo-1624526267942-ab67cb38121d?w=500&h=500&fit=crop",
            "is_active": True,
            "is_verified": True,
            "is_featured": False,
            "rating": 4.7,
            "total_reviews": 18,
            "total_enquiries": 0,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Fitness World",
            "description": "Gym equipment and fitness accessories",
            "category": "Fitness",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0150,
            "longitude": 72.5600,
            "phone": "9876543222",
            "email": "fitnessworld@example.com",
            "image": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=500&h=500&fit=crop",
            "is_active": True,
            "is_verified": True,
            "is_featured": True,
            "rating": 4.8,
            "total_reviews": 25,
            "total_enquiries": 0,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Badminton Express",
            "description": "Complete badminton equipment and rackets",
            "category": "Badminton",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0275,
            "longitude": 72.5750,
            "phone": "9876543223",
            "email": "badmintonexpress@example.com",
            "image": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=500&h=500&fit=crop",
            "is_active": True,
            "is_verified": True,
            "is_featured": False,
            "rating": 4.6,
            "total_reviews": 14,
            "total_enquiries": 0,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Football Factory",
            "description": "Official football gear and training equipment",
            "category": "Football",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0180,
            "longitude": 72.5680,
            "phone": "9876543224",
            "email": "footballfactory@example.com",
            "image": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=500&h=500&fit=crop",
            "is_active": True,
            "is_verified": True,
            "is_featured": False,
            "rating": 4.4,
            "total_reviews": 10,
            "total_enquiries": 0,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Tennis Zone",
            "description": "Premium tennis rackets and accessories",
            "category": "Tennis",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0320,
            "longitude": 72.5820,
            "phone": "9876543225",
            "email": "tenniszone@example.com",
            "image": "https://images.unsplash.com/photo-1554224311-beee415c15cb?w=500&h=500&fit=crop",
            "is_active": True,
            "is_verified": True,
            "is_featured": False,
            "rating": 4.5,
            "total_reviews": 11,
            "total_enquiries": 0,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Athletic Wear Co",
            "description": "Sports apparel and athletic wear",
            "category": "Apparel",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0240,
            "longitude": 72.5730,
            "phone": "9876543226",
            "email": "athleticwear@example.com",
            "image": "https://images.unsplash.com/photo-1556821552-5f63b1c2c723?w=500&h=500&fit=crop",
            "is_active": True,
            "is_verified": True,
            "is_featured": False,
            "rating": 4.3,
            "total_reviews": 9,
            "total_enquiries": 0,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Gym Masters",
            "description": "Complete gym and home fitness equipment",
            "category": "Fitness",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0200,
            "longitude": 72.5700,
            "phone": "9876543227",
            "email": "gymmasters@example.com",
            "image": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=500&h=500&fit=crop",
            "is_active": True,
            "is_verified": True,
            "is_featured": False,
            "rating": 4.6,
            "total_reviews": 16,
            "total_enquiries": 0,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Sports Nutrition Hub",
            "description": "Protein supplements and sports nutrition",
            "category": "Nutrition",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0260,
            "longitude": 72.5760,
            "phone": "9876543228",
            "email": "nutritionhub@example.com",
            "image": "https://images.unsplash.com/photo-1607623814075-e51df1bdc82f?w=500&h=500&fit=crop",
            "is_active": True,
            "is_verified": True,
            "is_featured": False,
            "rating": 4.7,
            "total_reviews": 20,
            "total_enquiries": 0,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Running Gear Store",
            "description": "Running shoes and athletic footwear",
            "category": "Footwear",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0290,
            "longitude": 72.5790,
            "phone": "9876543229",
            "email": "runningstore@example.com",
            "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&h=500&fit=crop",
            "is_active": True,
            "is_verified": True,
            "is_featured": False,
            "rating": 4.5,
            "total_reviews": 13,
            "total_enquiries": 0,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Yoga & Wellness",
            "description": "Yoga mats, meditation gear and wellness products",
            "category": "Wellness",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0210,
            "longitude": 72.5710,
            "phone": "9876543230",
            "email": "yogawellness@example.com",
            "image": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=500&h=500&fit=crop",
            "is_active": True,
            "is_verified": True,
            "is_featured": False,
            "rating": 4.4,
            "total_reviews": 8,
            "total_enquiries": 0,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Cycling Paradise",
            "description": "Bicycles, helmets and cycling accessories",
            "category": "Cycling",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0310,
            "longitude": 72.5810,
            "phone": "9876543231",
            "email": "cyclingparadise@example.com",
            "image": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500&h=500&fit=crop",
            "is_active": True,
            "is_verified": True,
            "is_featured": False,
            "rating": 4.6,
            "total_reviews": 15,
            "total_enquiries": 0,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Swimming Central",
            "description": "Swimming gear, goggles and pool equipment",
            "category": "Swimming",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0230,
            "longitude": 72.5740,
            "phone": "9876543232",
            "email": "swimmingcentral@example.com",
            "image": "https://images.unsplash.com/photo-1576610616656-d3aa5d1f4534?w=500&h=500&fit=crop",
            "is_active": True,
            "is_verified": True,
            "is_featured": False,
            "rating": 4.5,
            "total_reviews": 12,
            "total_enquiries": 0,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Martial Arts Supplies",
            "description": "Karate, boxing and martial arts equipment",
            "category": "Martial Arts",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0270,
            "longitude": 72.5770,
            "phone": "9876543233",
            "email": "martialarts@example.com",
            "image": "https://images.unsplash.com/photo-1517836357463-d25ddfcbf042?w=500&h=500&fit=crop",
            "is_active": True,
            "is_verified": True,
            "is_featured": False,
            "rating": 4.7,
            "total_reviews": 19,
            "total_enquiries": 0,
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Sports Accessories Plus",
            "description": "Bags, water bottles and sports accessories",
            "category": "Accessories",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "latitude": 23.0220,
            "longitude": 72.5720,
            "phone": "9876543234",
            "email": "accessoriesplus@example.com",
            "image": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&h=500&fit=crop",
            "is_active": True,
            "is_verified": True,
            "is_featured": False,
            "rating": 4.4,
            "total_reviews": 11,
            "total_enquiries": 0,
            "created_at": datetime.utcnow()
        }
    ]
    
    result = db.shops.insert_many(shops)
    print(f"✅ Created {len(result.inserted_ids)} shops")
    return shops

def seed_jobs():
    """Create dummy jobs"""
    jobs = [
        {
            "_id": ObjectId(),
            "title": "Cricket Coach",
            "description": "Experienced cricket coach needed for academy",
            "sport_type": "Cricket",
            "job_type": "Full-time",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "salary_min": 30000,
            "salary_max": 50000,
            "experience_required": "3+ years",
            "status": "Open",
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "title": "Badminton Trainer",
            "description": "Professional badminton trainer for coaching center",
            "sport_type": "Badminton",
            "job_type": "Part-time",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "salary_min": 15000,
            "salary_max": 25000,
            "experience_required": "2+ years",
            "status": "Open",
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "title": "Sports Manager",
            "description": "Sports event manager for tournament organization",
            "sport_type": "Multi-sport",
            "job_type": "Full-time",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "salary_min": 25000,
            "salary_max": 40000,
            "experience_required": "2+ years",
            "status": "Open",
            "created_at": datetime.utcnow()
        }
    ]
    
    result = db.jobs.insert_many(jobs)
    print(f"✅ Created {len(result.inserted_ids)} jobs")
    return jobs

def seed_communities(users):
    """Create dummy communities"""
    communities = [
        {
            "_id": ObjectId(),
            "name": "Cricket Enthusiasts",
            "description": "Community for cricket lovers and players",
            "sport_type": "Cricket",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "members": [users[0]["_id"], users[1]["_id"]],
            "member_count": 2,
            "created_by": users[0]["_id"],
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Badminton Players",
            "description": "Connect with badminton players in your area",
            "sport_type": "Badminton",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "members": [users[1]["_id"]],
            "member_count": 1,
            "created_by": users[1]["_id"],
            "created_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "Football Community",
            "description": "Football players and fans community",
            "sport_type": "Football",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "members": [users[0]["_id"]],
            "member_count": 1,
            "created_by": users[0]["_id"],
            "created_at": datetime.utcnow()
        }
    ]
    
    result = db.communities.insert_many(communities)
    print(f"✅ Created {len(result.inserted_ids)} communities")
    return communities

def main():
    """Run all seed functions"""
    try:
        print("🌱 Starting database seeding...\n")
        
        clear_collections()
        users = seed_users()
        venues = seed_venues(users)
        tournaments = seed_tournaments(users, venues)
        shops = seed_shops()
        jobs = seed_jobs()
        communities = seed_communities(users)
        
        print("\n✅ Database seeding completed successfully!")
        print(f"\nSummary:")
        print(f"  - Users: {len(users)}")
        print(f"  - Venues: {len(venues)}")
        print(f"  - Tournaments: {len(tournaments)}")
        print(f"  - Shops: {len(shops)}")
        print(f"  - Jobs: {len(jobs)}")
        print(f"  - Communities: {len(communities)}")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        raise

if __name__ == "__main__":
    main()
