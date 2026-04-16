#!/usr/bin/env python3
"""
Complete diagnostic tool for shops not showing issue
Checks: MongoDB connection, database, API endpoint, frontend
Usage: python diagnose_shops_issue.py
"""

import sys
import socket
from pymongo import MongoClient
import requests
import json

# Fix Unicode encoding on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 60)
print("SPORTS DIARY - SHOPS DIAGNOSTIC TOOL")
print("=" * 60)

# Step 1: Check MongoDB
print("\n[STEP 1] Checking MongoDB Connection...")
print("-" * 60)

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('localhost', 27017))
    sock.close()
    
    if result != 0:
        print("[FAIL] MongoDB port 27017 is not open")
        print("[HELP] Start MongoDB: mongod.exe (Windows) or brew services start mongodb-community (Mac)")
        exit(1)
    print("[OK] MongoDB port 27017 is open")
except Exception as e:
    print(f"[ERROR] {e}")
    exit(1)

# Try to connect
try:
    client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=3000)
    client.admin.command('ping')
    print("[OK] Connected to MongoDB")
except Exception as e:
    print(f"[FAIL] Could not connect: {e}")
    print("[HELP] Try: mongod --noauth (to disable authentication)")
    exit(1)

# Step 2: Check Database
print("\n[STEP 2] Checking Database...")
print("-" * 60)

db = client['sports_diary']

total_shops = db.shops.count_documents({})
active_shops = db.shops.count_documents({"is_active": True})
inactive_shops = db.shops.count_documents({"is_active": False})

print(f"[INFO] Total shops: {total_shops}")
print(f"[INFO] Active shops: {active_shops}")
print(f"[INFO] Inactive shops: {inactive_shops}")

if total_shops == 0:
    print("[FAIL] No shops in database!")
    print("[HELP] Run: python seed_local.py")
    exit(1)

if active_shops == 0:
    print("[FAIL] No active shops! All shops are inactive.")
    print("[HELP] Run: python fix_shops.py")
    exit(1)

print("[OK] Database has active shops")

# Step 3: Check Backend API
print("\n[STEP 3] Checking Backend API...")
print("-" * 60)

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('localhost', 8001))
    sock.close()
    
    if result != 0:
        print("[FAIL] Backend port 8001 is not open")
        print("[HELP] Start backend: python run.py (in backend folder)")
        print("[INFO] Continuing with other checks...")
    else:
        print("[OK] Backend port 8001 is open")
        
        # Try to fetch shops from API
        try:
            response = requests.get('http://localhost:8001/api/marketplace/shops', timeout=5)
            if response.status_code == 200:
                data = response.json()
                api_shops = len(data.get('data', []))
                print(f"[OK] API returned {api_shops} shops")
                
                if api_shops == 0:
                    print("[FAIL] API returned 0 shops!")
                    print("[INFO] Checking API response...")
                    print(f"[DEBUG] Response: {json.dumps(data, indent=2)[:200]}")
                elif api_shops < active_shops:
                    print(f"[WARNING] API returned {api_shops} but database has {active_shops}")
                    print("[HELP] Check backend logs for filtering issues")
            else:
                print(f"[FAIL] API returned status {response.status_code}")
                print(f"[DEBUG] Response: {response.text[:200]}")
        except requests.exceptions.ConnectionError:
            print("[FAIL] Could not connect to backend API")
            print("[HELP] Make sure backend is running on port 8001")
        except Exception as e:
            print(f"[ERROR] {e}")
except Exception as e:
    print(f"[ERROR] {e}")

# Step 4: Check Frontend
print("\n[STEP 4] Checking Frontend...")
print("-" * 60)

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('localhost', 3003))
    sock.close()
    
    if result != 0:
        print("[FAIL] Frontend port 3003 is not open")
        print("[HELP] Start frontend: npm run dev (in frontend folder)")
    else:
        print("[OK] Frontend port 3003 is open")
        print("[INFO] Go to http://localhost:3003/shops to see shops")
except Exception as e:
    print(f"[ERROR] {e}")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

print(f"\nDatabase: {active_shops} active shops")
print(f"Backend: {'Running' if result == 0 else 'Not running'}")
print(f"Frontend: {'Running' if result == 0 else 'Not running'}")

if active_shops > 0:
    print("\n[SUCCESS] Everything looks good!")
    print("[NEXT] Refresh http://localhost:3003/shops")
else:
    print("\n[ACTION NEEDED]")
    if total_shops == 0:
        print("1. Run: python seed_local.py")
    else:
        print("1. Run: python fix_shops.py")
    print("2. Start backend: python run.py")
    print("3. Start frontend: npm run dev")
    print("4. Go to http://localhost:3003/shops")

client.close()
