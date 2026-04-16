#!/usr/bin/env python3
"""
Fix script to activate all shops in the database
Run: python fix_shops.py
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://utsavgfuturetech_db_user:Utsavv%4011@cluster0.k3reanw.mongodb.net/?appName=Cluster0")

print("🔗 Connecting to MongoDB Atlas...")

try:
    client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
    client.admin.command('ping')
    print("✅ Connected to MongoDB!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit(1)

db = client['sports_diary']

# Check current shops
print("\n📊 Checking shops in database...")
total_shops = db.shops.count_documents({})
active_shops = db.shops.count_documents({"is_active": True})
inactive_shops = db.shops.count_documents({"is_active": False})
no_active_field = db.shops.count_documents({"is_active": {"$exists": False}})

print(f"Total shops: {total_shops}")
print(f"Active shops: {active_shops}")
print(f"Inactive shops: {inactive_shops}")
print(f"Shops without is_active field: {no_active_field}")

# Fix 1: Set is_active to True for all shops
print("\n🔧 Fixing shops...")
result = db.shops.update_many(
    {},
    {
        "$set": {
            "is_active": True,
            "is_verified": True
        }
    }
)

print(f"✅ Updated {result.modified_count} shops")

# Verify
active_shops_after = db.shops.count_documents({"is_active": True})
print(f"\n✅ Active shops after fix: {active_shops_after}")

if active_shops_after > 0:
    print(f"\n🎉 SUCCESS! {active_shops_after} shops are now active!")
    print("Refresh your browser to see all shops!")
else:
    print("⚠️  No active shops found. Check your database.")

print("\nDone!")
