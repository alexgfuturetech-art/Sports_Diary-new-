#!/usr/bin/env python3
"""
Seed script to add 10+ Sports Academies to local MongoDB
Usage: python seed_academies_local.py
"""

import sys
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId

# Fix Unicode encoding on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("[*] Connecting to Local MongoDB...\n")

# Try different MongoDB connection strings
connection_strings = [
    ("mongodb://localhost:27017/sports_diary", "Local (no auth)"),
    ("mongodb://localhost:27017", "Local (no auth, no db)"),
    ("mongodb://admin:admin123@localhost:27017/sports_diary?authSource=admin", "Local (with auth)"),
]

client = None

for conn_str, desc in connection_strings:
    try:
        print(f"[ATTEMPT] {desc}")
        client = MongoClient(conn_str, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
        client.admin.command('ping')
        print(f"[SUCCESS] Connected using: {desc}\n")
        break
    except Exception as e:
        print(f"[FAILED] {str(e)[:80]}\n")
        client = None
        continue

if not client:
    print("[ERROR] Could not connect to MongoDB!")
    print("\n[HELP] Make sure MongoDB is running locally!")
    print("   Windows: mongod.exe")
    print("   Mac: brew services start mongodb-community")
    print("   Linux: sudo systemctl start mongod")
    print("\n[HELP] If you see 'Authentication failed', run: mongod --noauth")
    exit(1)

db = client['sports_diary']

# Create 10+ Sports Academies
academies = [
    {
        "term": "Ahmedabad Sports Academy",
        "sport": "Cricket",
        "category": "Academy",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "address": "Stadium Road, Ahmedabad",
        "latitude": 23.0225,
        "longitude": 72.5714,
        "contact_number": "9876543220",
        "contact_email": "ahmedabad.academy@example.com",
        "definition": "Premier cricket coaching academy in Ahmedabad",
        "explanation": "Offers professional cricket training for all age groups with expert coaches and world-class facilities",
        "examples": ["Daily practice sessions", "Weekly match simulations", "Professional coaching"],
        "images": ["https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=500&h=500&fit=crop"],
        "tags": ["Cricket", "Coaching", "Academy", "Professional"],
        "difficulty_level": "Intermediate",
        "is_featured": True,
        "is_active": True,
        "views_count": 0,
        "helpful_count": 0,
        "created_at": datetime.utcnow()
    },
    {
        "term": "Elite Football Academy",
        "sport": "Football",
        "category": "Academy",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "address": "Surat, Gujarat",
        "latitude": 21.1458,
        "longitude": 72.8479,
        "contact_number": "9876543221",
        "contact_email": "elite.football@example.com",
        "definition": "Professional football training academy",
        "explanation": "Comprehensive football training program following international standards with UEFA certified coaches",
        "examples": ["Professional training methodology", "Regular friendly matches", "International exposure"],
        "images": ["https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=500&h=500&fit=crop"],
        "tags": ["Football", "Professional", "Academy", "UEFA"],
        "difficulty_level": "Advanced",
        "is_featured": True,
        "is_active": True,
        "views_count": 0,
        "helpful_count": 0,
        "created_at": datetime.utcnow()
    },
    {
        "term": "Badminton Excellence Center",
        "sport": "Badminton",
        "category": "Academy",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "address": "Sports Complex, Ahmedabad",
        "latitude": 23.0500,
        "longitude": 72.5500,
        "contact_number": "9876543222",
        "contact_email": "badminton.excellence@example.com",
        "definition": "Specialized badminton training center",
        "explanation": "State-of-the-art badminton academy with national-level coaches and modern facilities",
        "examples": ["Technique training", "Tournament preparation", "Fitness coaching"],
        "images": ["https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=500&h=500&fit=crop"],
        "tags": ["Badminton", "Training", "Academy", "National"],
        "difficulty_level": "Intermediate",
        "is_featured": False,
        "is_active": True,
        "views_count": 0,
        "helpful_count": 0,
        "created_at": datetime.utcnow()
    },
    {
        "term": "Tennis Pro Academy",
        "sport": "Tennis",
        "category": "Academy",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "address": "Tennis Courts, Ahmedabad",
        "latitude": 23.0300,
        "longitude": 72.5600,
        "contact_number": "9876543223",
        "contact_email": "tennis.pro@example.com",
        "definition": "Professional tennis coaching academy",
        "explanation": "Comprehensive tennis training with ITF certified coaches for beginners to advanced players",
        "examples": ["Stroke technique", "Match strategy", "Physical conditioning"],
        "images": ["https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=500&h=500&fit=crop"],
        "tags": ["Tennis", "Professional", "Academy", "ITF"],
        "difficulty_level": "Beginner",
        "is_featured": False,
        "is_active": True,
        "views_count": 0,
        "helpful_count": 0,
        "created_at": datetime.utcnow()
    },
    {
        "term": "Kabaddi Warriors Academy",
        "sport": "Kabaddi",
        "category": "Academy",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "address": "Community Ground, Ahmedabad",
        "latitude": 23.0400,
        "longitude": 72.5800,
        "contact_number": "9876543224",
        "contact_email": "kabaddi.warriors@example.com",
        "definition": "Traditional kabaddi training academy",
        "explanation": "Specialized kabaddi coaching with focus on traditional techniques and modern strategies",
        "examples": ["Raiding techniques", "Defensive formations", "Team coordination"],
        "images": ["https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=500&h=500&fit=crop"],
        "tags": ["Kabaddi", "Traditional", "Academy", "Team"],
        "difficulty_level": "Intermediate",
        "is_featured": False,
        "is_active": True,
        "views_count": 0,
        "helpful_count": 0,
        "created_at": datetime.utcnow()
    },
    {
        "term": "Swimming Champions Academy",
        "sport": "Swimming",
        "category": "Academy",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "address": "Olympic Pool, Ahmedabad",
        "latitude": 23.0350,
        "longitude": 72.5750,
        "contact_number": "9876543225",
        "contact_email": "swimming.champions@example.com",
        "definition": "Professional swimming training center",
        "explanation": "Olympic-standard swimming academy with certified coaches and modern pool facilities",
        "examples": ["Stroke techniques", "Endurance training", "Competition preparation"],
        "images": ["https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=500&h=500&fit=crop"],
        "tags": ["Swimming", "Olympic", "Academy", "Professional"],
        "difficulty_level": "Beginner",
        "is_featured": False,
        "is_active": True,
        "views_count": 0,
        "helpful_count": 0,
        "created_at": datetime.utcnow()
    },
    {
        "term": "Martial Arts Institute",
        "sport": "Martial Arts",
        "category": "Academy",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "address": "Martial Arts Center, Ahmedabad",
        "latitude": 23.0450,
        "longitude": 72.5650,
        "contact_number": "9876543226",
        "contact_email": "martial.arts@example.com",
        "definition": "Comprehensive martial arts training institute",
        "explanation": "Training in Karate, Taekwondo, Judo, and Boxing with international certified instructors",
        "examples": ["Belt progression", "Self-defense", "Competition training"],
        "images": ["https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=500&h=500&fit=crop"],
        "tags": ["Martial Arts", "Karate", "Academy", "Self-defense"],
        "difficulty_level": "Beginner",
        "is_featured": False,
        "is_active": True,
        "views_count": 0,
        "helpful_count": 0,
        "created_at": datetime.utcnow()
    },
    {
        "term": "Basketball Elite Academy",
        "sport": "Basketball",
        "category": "Academy",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "address": "Basketball Court, Ahmedabad",
        "latitude": 23.0200,
        "longitude": 72.5900,
        "contact_number": "9876543227",
        "contact_email": "basketball.elite@example.com",
        "definition": "Professional basketball coaching academy",
        "explanation": "NBA-style basketball training with certified coaches focusing on skill development and team play",
        "examples": ["Dribbling drills", "Shooting techniques", "Team strategies"],
        "images": ["https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=500&h=500&fit=crop"],
        "tags": ["Basketball", "Professional", "Academy", "NBA"],
        "difficulty_level": "Intermediate",
        "is_featured": False,
        "is_active": True,
        "views_count": 0,
        "helpful_count": 0,
        "created_at": datetime.utcnow()
    },
    {
        "term": "Volleyball Academy",
        "sport": "Volleyball",
        "category": "Academy",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "address": "Sports Hall, Ahmedabad",
        "latitude": 23.0150,
        "longitude": 72.5850,
        "contact_number": "9876543228",
        "contact_email": "volleyball.academy@example.com",
        "definition": "Competitive volleyball training academy",
        "explanation": "Professional volleyball coaching with focus on technique, tactics, and team coordination",
        "examples": ["Serving techniques", "Blocking strategies", "Team formations"],
        "images": ["https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=500&h=500&fit=crop"],
        "tags": ["Volleyball", "Team", "Academy", "Professional"],
        "difficulty_level": "Intermediate",
        "is_featured": False,
        "is_active": True,
        "views_count": 0,
        "helpful_count": 0,
        "created_at": datetime.utcnow()
    },
    {
        "term": "Hockey Training Center",
        "sport": "Hockey",
        "category": "Academy",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "address": "Hockey Field, Ahmedabad",
        "latitude": 23.0100,
        "longitude": 72.5950,
        "contact_number": "9876543229",
        "contact_email": "hockey.training@example.com",
        "definition": "Professional hockey training center",
        "explanation": "International-standard hockey coaching with focus on stick skills and tactical awareness",
        "examples": ["Stick handling", "Passing drills", "Game tactics"],
        "images": ["https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=500&h=500&fit=crop"],
        "tags": ["Hockey", "Professional", "Academy", "International"],
        "difficulty_level": "Advanced",
        "is_featured": False,
        "is_active": True,
        "views_count": 0,
        "helpful_count": 0,
        "created_at": datetime.utcnow()
    },
    {
        "term": "Gymnastics Excellence Academy",
        "sport": "Gymnastics",
        "category": "Academy",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "address": "Gymnastics Center, Ahmedabad",
        "latitude": 23.0050,
        "longitude": 72.6000,
        "contact_number": "9876543230",
        "contact_email": "gymnastics.excellence@example.com",
        "definition": "Professional gymnastics training academy",
        "explanation": "Artistic and rhythmic gymnastics training with certified coaches and modern equipment",
        "examples": ["Floor exercises", "Apparatus training", "Flexibility work"],
        "images": ["https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=500&h=500&fit=crop"],
        "tags": ["Gymnastics", "Artistic", "Academy", "Professional"],
        "difficulty_level": "Beginner",
        "is_featured": False,
        "is_active": True,
        "views_count": 0,
        "helpful_count": 0,
        "created_at": datetime.utcnow()
    }
]

print("[*] Creating 10 Sports Academies...\n")

academy_docs = []
for i, academy in enumerate(academies, 1):
    doc = {
        "_id": ObjectId(),
        **academy
    }
    academy_docs.append(doc)
    print(f"   {i}. {academy['term']}")

try:
    result = db.dictionary.insert_many(academy_docs)
    print(f"\n[OK] Created {len(result.inserted_ids)} academies!")
except Exception as e:
    print(f"\n[ERROR] Failed to insert academies: {e}")
    exit(1)

# Verify
try:
    count = db.dictionary.count_documents({"category": "Academy", "is_active": True})
    print(f"\n[INFO] Total active academies in database: {count}")
    
    if count >= 10:
        print("[SUCCESS] All 10 academies are now in the local database!")
        print("\n[NEXT] Refresh your browser at http://localhost:3003/dictionary to see all academies!")
    else:
        print(f"[WARNING] Only {count} academies found. Something went wrong.")
except Exception as e:
    print(f"[ERROR] Failed to verify academies: {e}")

print("\n[DONE] Seeding complete!")
client.close()
