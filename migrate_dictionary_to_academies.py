#!/usr/bin/env python3
"""
One-time migration: move all documents from the old `dictionary` collection
into the new `academies` collection.

Run once:
    python migrate_dictionary_to_academies.py

Safe to re-run — skips documents already migrated (matched by _id).
"""

import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
if not MONGODB_URL:
    print("[ERROR] MONGODB_URL not found in .env file")
    exit(1)

print("[*] Connecting to MongoDB...\n")
try:
    client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    print("[OK] Connected\n")
except Exception as e:
    print(f"[ERROR] Connection failed: {e}")
    exit(1)

db = client["sports_diary"]

# ── Fetch all docs from old collection ────────────────────────────────────────
old_docs = list(db.dictionary.find({}))
print(f"[INFO] Found {len(old_docs)} document(s) in `dictionary` collection")

if not old_docs:
    print("[OK] Nothing to migrate. Exiting.")
    client.close()
    exit(0)

# ── Migrate each doc ──────────────────────────────────────────────────────────
migrated = 0
skipped  = 0

for doc in old_docs:
    existing = db.academies.find_one({"_id": doc["_id"]})
    if existing:
        skipped += 1
        continue

    # Normalise fields so both old (term/sport/definition) and new
    # (name/sport_type/description) field names are present on every doc.
    if not doc.get("name"):
        doc["name"] = doc.get("term", "")
    if not doc.get("sport_type"):
        doc["sport_type"] = doc.get("sport", "")
    if not doc.get("description"):
        defn = doc.get("definition", "")
        expl = doc.get("explanation", "")
        doc["description"] = f"{defn}. {expl}".strip(". ") if expl else defn

    doc.setdefault("category",      "Academy")
    doc.setdefault("is_active",     True)
    doc.setdefault("is_featured",   False)
    doc.setdefault("is_verified",   False)
    doc.setdefault("rating",        0.0)
    doc.setdefault("total_reviews", 0)
    doc.setdefault("views_count",   0)
    doc.setdefault("helpful_count", 0)

    db.academies.insert_one(doc)
    migrated += 1
    print(f"   [+] Migrated: {doc.get('name') or doc.get('term', str(doc['_id']))}")

print(f"\n[DONE] Migrated: {migrated}  |  Already existed (skipped): {skipped}")

# ── Verify ────────────────────────────────────────────────────────────────────
total_academies = db.academies.count_documents({})
print(f"[INFO] Total documents now in `academies` collection: {total_academies}")

print("""
[NEXT STEPS]
  - Verify the data looks correct in MongoDB Atlas.
  - Once confirmed, you can drop the old `dictionary` collection:
      db.dictionary.drop()
  - Do NOT drop it until you have verified the migration.
""")

client.close()
