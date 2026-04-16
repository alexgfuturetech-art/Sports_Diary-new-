#!/usr/bin/env python3
"""
Check what shops are in the local MongoDB database
Usage: python check_shops.py
"""

import sys
from pymongo import MongoClient

# Fix Unicode encoding on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("[*] Checking shops in local MongoDB...\n")

# Try to connect
try:
    client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=3000)
    client.admin.command('ping')
except Exception as e:
    print(f"[ERROR] Could not connect to MongoDB: {e}")
    print("\n[HELP] Make sure MongoDB is running:")
    print("   Windows: mongod.exe")
    print("   Mac: brew services start mongodb-community")
    print("   Linux: sudo systemctl start mongod")
    exit(1)

db = client['sports_diary']

# Check total shops
total = db.shops.count_documents({})
active = db.shops.count_documents({"is_active": True})
inactive = db.shops.count_documents({"is_active": False})

print(f"[INFO] Total shops in database: {total}")
print(f"[INFO] Active shops (is_active=True): {active}")
print(f"[INFO] Inactive shops (is_active=False): {inactive}\n")

if total == 0:
    print("[WARNING] No shops found in database!")
    print("[HELP] Run: python seed_local.py")
    exit(1)

# List all shops
print("[*] All shops:\n")
shops = db.shops.find({}).sort("name", 1)
for i, shop in enumerate(shops, 1):
    status = "ACTIVE" if shop.get("is_active") else "INACTIVE"
    print(f"{i}. {shop['name']}")
    print(f"   Status: {status}")
    print(f"   Category: {shop.get('category', 'N/A')}")
    print(f"   Rating: {shop.get('rating', 'N/A')}")
    print()

print(f"[DONE] Total: {total} shops")

if active < total:
    print(f"\n[WARNING] {inactive} shops are inactive!")
    print("[HELP] Run: python fix_shops.py")

client.close()
