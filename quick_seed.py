#!/usr/bin/env python3
"""
Quick seed script - Run this to populate 15 shops
Usage: python quick_seed.py
"""

import os
import sys
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId

# MongoDB URL from environment or use default
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://utsavgfuturetech_db_user:Utsavv%4011@cluster0.k3reanw.mongodb.net/?appName=Cluster0")

print("🔗 Connecting to MongoDB Atlas...")
print(f"URL: {MONGODB_URL[:60]}...")

try:
    client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
    client.admin.command('ping')
    print("✅ Connected to MongoDB!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

db = client['sports_diary']

# Delete existing shops
print("\n🗑️  Clearing existing shops...")
db.shops.delete_many({})
print("✅ Cleared!")

# Create 15 shops
shops = [
    {"name": "Sports Pro Store", "category": "Equipment", "rating": 4.5, "reviews": 12},
    {"name": "Cricket Gear Hub", "category": "Cricket", "rating": 4.7, "reviews": 18},
    {"name": "Fitness World", "category": "Fitness", "rating": 4.8, "reviews": 25, "featured": True},
    {"name": "Badminton Express", "category": "Badminton", "rating": 4.6, "reviews": 14},
    {"name": "Football Factory", "category": "Football", "rating": 4.4, "reviews": 10},
    {"name": "Tennis Zone", "category": "Tennis", "rating": 4.5, "reviews": 11},
    {"name": "Athletic Wear Co", "category": "Apparel", "rating": 4.3, "reviews": 9},
    {"name": "Gym Masters", "category": "Fitness", "rating": 4.6, "reviews": 16},
    {"name": "Sports Nutrition Hub", "category": "Nutrition", "rating": 4.7, "reviews": 20},
    {"name": "Running Gear Store", "category": "Footwear", "rating": 4.5, "reviews": 13},
    {"name": "Yoga & Wellness", "category": "Wellness", "rating": 4.4, "reviews": 8},
    {"name": "Cycling Paradise", "category": "Cycling", "rating": 4.6, "reviews": 15},
    {"name": "Swimming Central", "category": "Swimming", "rating": 4.5, "reviews": 12},
    {"name": "Martial Arts Supplies", "category": "Martial Arts", "rating": 4.7, "reviews": 19},
    {"name": "Sports Accessories Plus", "category": "Accessories", "rating": 4.4, "reviews": 11},
]

print("\n📝 Creating 15 shops...")

shop_docs = []
for i, shop in enumerate(shops, 1):
    doc = {
        "_id": ObjectId(),
        "name": shop["name"],
        "description": f"{shop['name']} - Premium sports equipment",
        "category": shop["category"],
        "city": "Ahmedabad",
        "state": "Gujarat",
        "latitude": 23.0 + (i * 0.001),
        "longitude": 72.5 + (i * 0.001),
        "phone": f"987654{3200 + i}",
        "email": f"{shop['name'].lower().replace(' ', '')}@example.com",
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

result = db.shops.insert_many(shop_docs)
print(f"✅ Created {len(result.inserted_ids)} shops!")

# Verify
count = db.shops.count_documents({"is_active": True})
print(f"\n📊 Total active shops in database: {count}")

if count >= 15:
    print("✅ SUCCESS! All 15 shops are now in the database!")
    print("\n🎉 Refresh your browser to see all shops on the Sports Shops page!")
else:
    print(f"⚠️  Only {count} shops found. Something went wrong.")

print("\nDone!")
