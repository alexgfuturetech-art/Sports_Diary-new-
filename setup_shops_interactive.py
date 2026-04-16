#!/usr/bin/env python3
"""
Interactive setup wizard for shops
Guides you through the entire process
Usage: python setup_shops_interactive.py
"""

import sys
import socket
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

# Fix Unicode encoding on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_mongodb_running():
    """Check if MongoDB is running"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 27017))
        sock.close()
        return result == 0
    except:
        return False

def try_connect_mongodb():
    """Try to connect to MongoDB"""
    connection_strings = [
        ("mongodb://localhost:27017/sports_diary", "no auth"),
        ("mongodb://localhost:27017", "no auth (no db)"),
        ("mongodb://admin:admin123@localhost:27017/sports_diary?authSource=admin", "with auth"),
    ]
    
    for conn_str, desc in connection_strings:
        try:
            client = MongoClient(conn_str, serverSelectionTimeoutMS=3000)
            client.admin.command('ping')
            return client, desc
        except:
            continue
    
    return None, None

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(text.center(60))
    print("=" * 60 + "\n")

def print_step(num, text):
    """Print a step"""
    print(f"\n[STEP {num}] {text}")
    print("-" * 60)

# Main wizard
print_header("SPORTS DIARY - SHOPS SETUP WIZARD")

print_step(1, "Checking MongoDB")

if not check_mongodb_running():
    print("[FAIL] MongoDB is not running on port 27017")
    print("\n[ACTION] Start MongoDB:")
    print("   Windows: mongod.exe")
    print("   Mac: brew services start mongodb-community")
    print("   Linux: sudo systemctl start mongod")
    print("\n[THEN] Run this script again")
    exit(1)

print("[OK] MongoDB is running")

print_step(2, "Connecting to MongoDB")

client, auth_method = try_connect_mongodb()

if not client:
    print("[FAIL] Could not connect to MongoDB")
    print("\n[POSSIBLE CAUSES]")
    print("1. Authentication is enabled but credentials are wrong")
    print("2. MongoDB is not accepting connections")
    print("\n[SOLUTION] Try disabling authentication:")
    print("   mongod --noauth")
    exit(1)

print(f"[OK] Connected using: {auth_method}")

db = client['sports_diary']

print_step(3, "Checking existing shops")

total = db.shops.count_documents({})
active = db.shops.count_documents({"is_active": True})

print(f"[INFO] Total shops: {total}")
print(f"[INFO] Active shops: {active}")

if total > 0:
    print("\n[QUESTION] Delete existing shops and create new ones? (y/n)")
    response = input("[INPUT] > ").strip().lower()
    if response != 'y':
        print("[SKIP] Keeping existing shops")
        client.close()
        exit(0)

print_step(4, "Creating 15 shops")

# Delete existing
if total > 0:
    db.shops.delete_many({})
    print(f"[OK] Deleted {total} existing shops")

# Create shops
shops_data = [
    ("Sports Pro Store", "Premium sports equipment and apparel", "Equipment", 4.5, 12),
    ("Cricket Gear Hub", "Specialized cricket equipment and accessories", "Cricket", 4.7, 18),
    ("Fitness World", "Gym equipment and fitness accessories", "Fitness", 4.8, 25),
    ("Badminton Express", "Complete badminton equipment and rackets", "Badminton", 4.6, 14),
    ("Football Factory", "Official football gear and training equipment", "Football", 4.4, 10),
    ("Tennis Zone", "Premium tennis rackets and accessories", "Tennis", 4.5, 11),
    ("Athletic Wear Co", "Sports apparel and athletic wear", "Apparel", 4.3, 9),
    ("Gym Masters", "Complete gym and home fitness equipment", "Fitness", 4.6, 16),
    ("Sports Nutrition Hub", "Protein supplements and sports nutrition", "Nutrition", 4.7, 20),
    ("Running Gear Store", "Running shoes and athletic footwear", "Footwear", 4.5, 13),
    ("Yoga & Wellness", "Yoga mats, meditation gear and wellness products", "Wellness", 4.4, 8),
    ("Cycling Paradise", "Bicycles, helmets and cycling accessories", "Cycling", 4.6, 15),
    ("Swimming Central", "Swimming gear, goggles and pool equipment", "Swimming", 4.5, 12),
    ("Martial Arts Supplies", "Karate, boxing and martial arts equipment", "Martial Arts", 4.7, 19),
    ("Sports Accessories Plus", "Bags, water bottles and sports accessories", "Accessories", 4.4, 11),
]

shop_docs = []
for i, (name, desc, category, rating, reviews) in enumerate(shops_data, 1):
    doc = {
        "_id": ObjectId(),
        "name": name,
        "description": desc,
        "category": category,
        "city": "Ahmedabad",
        "state": "Gujarat",
        "latitude": 23.0 + (i * 0.001),
        "longitude": 72.5 + (i * 0.001),
        "phone": f"987654{3220 + i}",
        "email": f"shop{i}@example.com",
        "image": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=500&h=500&fit=crop",
        "is_active": True,
        "is_verified": True,
        "is_featured": i == 3,  # Fitness World is featured
        "rating": rating,
        "total_reviews": reviews,
        "total_enquiries": 0,
        "created_at": datetime.utcnow()
    }
    shop_docs.append(doc)
    print(f"   {i}. {name}")

result = db.shops.insert_many(shop_docs)
print(f"\n[OK] Created {len(result.inserted_ids)} shops")

print_step(5, "Verifying")

count = db.shops.count_documents({"is_active": True})
print(f"[INFO] Active shops in database: {count}")

if count == 15:
    print("[SUCCESS] All 15 shops created successfully!")
else:
    print(f"[WARNING] Expected 15 shops but found {count}")

print_header("SETUP COMPLETE")

print("[NEXT STEPS]")
print("1. Make sure backend is running: python run.py")
print("2. Make sure frontend is running: npm run dev")
print("3. Go to http://localhost:3003/shops")
print("4. You should see all 15 shops!")

print("\n[HELP] If shops don't show:")
print("   - Run: python diagnose_shops_issue.py")
print("   - Check backend logs")
print("   - Check browser console (F12)")

client.close()
