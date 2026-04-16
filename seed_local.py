#!/usr/bin/env python3
"""
Local seed script - Run this to populate 15 shops on localhost
Usage: python seed_local.py
"""

import os     
import sys
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
import time

# Fix Unicode encoding on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Try different MongoDB connection strings
connection_strings = [
    ("mongodb://localhost:27017/sports_diary", "Local (no auth)"),
    ("mongodb://localhost:27017", "Local (no auth, no db)"),
    ("mongodb://admin:admin123@localhost:27017/sports_diary?authSource=admin", "Local (with auth)"),
]

client = None
print("[*] Trying to connect to Local MongoDB...\n")

for conn_str, desc in connection_strings:
    try:
        print(f"[ATTEMPT] {desc}")
        print(f"[URL] {conn_str}")
        client = MongoClient(conn_str, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
        # Try to ping
        client.admin.command('ping')
        print(f"[SUCCESS] Connected using: {desc}\n")
        break
    except Exception as e:
        error_msg = str(e)
        print(f"[FAILED] {error_msg[:80]}\n")
        client = None
        continue

if not client:
    print("[ERROR] Could not connect to MongoDB!")
    print("\n[HELP] Make sure MongoDB is running locally!")
    print("   Windows: mongod.exe")
    print("   Mac: brew services start mongodb-community")
    print("   Linux: sudo systemctl start mongod")
    print("\n[HELP] Check if MongoDB is listening on port 27017:")
    print("   Windows: netstat -ano | findstr :27017")
    print("   Mac/Linux: lsof -i :27017")
    print("\n[HELP] If you see 'Authentication failed', your MongoDB has auth enabled.")
    print("   Try: mongod --noauth (to disable auth temporarily)")
    exit(1)

db = client['sports_diary']

# Delete existing shops
print("[*] Clearing existing shops...")
try:
    result = db.shops.delete_many({})
    print(f"[OK] Deleted {result.deleted_count} existing shops\n")
except Exception as e:
    print(f"[WARNING] Could not delete existing shops: {e}\n")

# Create 15 shops
shops = [
    {
        "name": "Sports Pro Store",
        "description": "Premium sports equipment and apparel",
        "category": "Equipment",
        "rating": 4.5,
        "reviews": 12,
        "phone": "9876543220",
        "email": "sportspro@example.com"
    },
    {
        "name": "Cricket Gear Hub",
        "description": "Specialized cricket equipment and accessories",
        "category": "Cricket",
        "rating": 4.7,
        "reviews": 18,
        "phone": "9876543221",
        "email": "cricketgear@example.com"
    },
    {
        "name": "Fitness World",
        "description": "Gym equipment and fitness accessories",
        "category": "Fitness",
        "rating": 4.8,
        "reviews": 25,
        "phone": "9876543222",
        "email": "fitnessworld@example.com",
        "featured": True
    },
    {
        "name": "Badminton Express",
        "description": "Complete badminton equipment and rackets",
        "category": "Badminton",
        "rating": 4.6,
        "reviews": 14,
        "phone": "9876543223",
        "email": "badmintonexpress@example.com"
    },
    {
        "name": "Football Factory",
        "description": "Official football gear and training equipment",
        "category": "Football",
        "rating": 4.4,
        "reviews": 10,
        "phone": "9876543224",
        "email": "footballfactory@example.com"
    },
    {
        "name": "Tennis Zone",
        "description": "Premium tennis rackets and accessories",
        "category": "Tennis",
        "rating": 4.5,
        "reviews": 11,
        "phone": "9876543225",
        "email": "tenniszone@example.com"
    },
    {
        "name": "Athletic Wear Co",
        "description": "Sports apparel and athletic wear",
        "category": "Apparel",
        "rating": 4.3,
        "reviews": 9,
        "phone": "9876543226",
        "email": "athleticwear@example.com"
    },
    {
        "name": "Gym Masters",
        "description": "Complete gym and home fitness equipment",
        "category": "Fitness",
        "rating": 4.6,
        "reviews": 16,
        "phone": "9876543227",
        "email": "gymmasters@example.com"
    },
    {
        "name": "Sports Nutrition Hub",
        "description": "Protein supplements and sports nutrition",
        "category": "Nutrition",
        "rating": 4.7,
        "reviews": 20,
        "phone": "9876543228",
        "email": "nutritionhub@example.com"
    },
    {
        "name": "Running Gear Store",
        "description": "Running shoes and athletic footwear",
        "category": "Footwear",
        "rating": 4.5,
        "reviews": 13,
        "phone": "9876543229",
        "email": "runningstore@example.com"
    },
    {
        "name": "Yoga & Wellness",
        "description": "Yoga mats, meditation gear and wellness products",
        "category": "Wellness",
        "rating": 4.4,
        "reviews": 8,
        "phone": "9876543230",
        "email": "yogawellness@example.com"
    },
    {
        "name": "Cycling Paradise",
        "description": "Bicycles, helmets and cycling accessories",
        "category": "Cycling",
        "rating": 4.6,
        "reviews": 15,
        "phone": "9876543231",
        "email": "cyclingparadise@example.com"
    },
    {
        "name": "Swimming Central",
        "description": "Swimming gear, goggles and pool equipment",
        "category": "Swimming",
        "rating": 4.5,
        "reviews": 12,
        "phone": "9876543232",
        "email": "swimmingcentral@example.com"
    },
    {
        "name": "Martial Arts Supplies",
        "description": "Karate, boxing and martial arts equipment",
        "category": "Martial Arts",
        "rating": 4.7,
        "reviews": 19,
        "phone": "9876543233",
        "email": "martialarts@example.com"
    },
    {
        "name": "Sports Accessories Plus",
        "description": "Bags, water bottles and sports accessories",
        "category": "Accessories",
        "rating": 4.4,
        "reviews": 11,
        "phone": "9876543234",
        "email": "accessoriesplus@example.com"
    }
]

print("\n[*] Creating 15 shops...")

shop_docs = []
for i, shop in enumerate(shops, 1):
    doc = {
        "_id": ObjectId(),
        "name": shop["name"],
        "description": shop["description"],
        "category": shop["category"],
        "city": "Ahmedabad",
        "state": "Gujarat",
        "latitude": 23.0 + (i * 0.001),
        "longitude": 72.5 + (i * 0.001),
        "phone": shop["phone"],
        "email": shop["email"],
        "image": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=500&h=500&fit=crop",
        "is_active": True,
        "is_verified": True,
        "is_featured": shop.get("featured", False),
        "rating": shop["rating"],
        "total_reviews": shop["reviews"],
        "total_enquiries": 0,
        "created_at": datetime.utcnow()
    }
    shop_docs.append(doc)

try:
    result = db.shops.insert_many(shop_docs)
    print(f"[OK] Created {len(result.inserted_ids)} shops!")
except Exception as e:
    print(f"[ERROR] Failed to insert shops: {e}")
    exit(1)

# Verify
try:
    count = db.shops.count_documents({"is_active": True})
    print(f"\n[INFO] Total active shops in database: {count}")
    
    if count >= 15:
        print("[SUCCESS] All 15 shops are now in the local database!")
        print("\n[NEXT] Refresh your browser at http://localhost:3003 to see all shops!")
    else:
        print(f"[WARNING] Only {count} shops found. Something went wrong.")
except Exception as e:
    print(f"[ERROR] Failed to verify shops: {e}")

print("\n[DONE] Seeding complete!")
client.close()
