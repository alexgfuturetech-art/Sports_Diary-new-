#!/usr/bin/env python3
"""
Check what collections exist in MongoDB Atlas
Usage: python check_atlas_collections.py
"""

import os
import sys
from pymongo import MongoClient
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

# Expected collections
expected_collections = [
    'users',
    'tournaments',
    'venues',
    'shops',
    'jobs',
    'communities',
    'posts',
    'academies',
    'bookings',
    'reviews',
    'teams',
    'professional_availability',
    'professional_bookings',
    'tournament_registrations',
    'organizer_teams'
]

# Get actual collections
actual_collections = db.list_collection_names()

print("[*] Collections in MongoDB Atlas:\n")

if not actual_collections:
    print("[WARNING] No collections found in database!")
    print("[HELP] Run: python seed_data.py")
else:
    for collection in sorted(actual_collections):
        count = db[collection].count_documents({})
        print(f"  - {collection}: {count} documents")

print(f"\n[INFO] Total collections: {len(actual_collections)}")

# Check for missing collections
missing = set(expected_collections) - set(actual_collections)
if missing:
    print(f"\n[WARNING] Missing collections ({len(missing)}):")
    for collection in sorted(missing):
        print(f"  - {collection}")
    print("\n[HELP] Run: python seed_data.py")
else:
    print("\n[OK] All expected collections exist!")

# Check for extra collections
extra = set(actual_collections) - set(expected_collections)
if extra:
    print(f"\n[INFO] Extra collections ({len(extra)}):")
    for collection in sorted(extra):
        print(f"  - {collection}")

client.close()
