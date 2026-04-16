#!/usr/bin/env python3
"""
MongoDB Connection Diagnostic Tool
Run this to check if MongoDB is running and accessible
Usage: python check_mongodb.py
"""

import sys
from pymongo import MongoClient
import socket

# Fix Unicode encoding on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("[*] MongoDB Connection Diagnostic Tool\n")

# Check if port 27017 is open
print("[1] Checking if MongoDB port (27017) is open...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('localhost', 27017))
    sock.close()
    
    if result == 0:
        print("[OK] Port 27017 is open - MongoDB is likely running\n")
    else:
        print("[FAIL] Port 27017 is closed - MongoDB is NOT running\n")
        print("[HELP] Start MongoDB:")
        print("   Windows: mongod.exe")
        print("   Mac: brew services start mongodb-community")
        print("   Linux: sudo systemctl start mongod")
        exit(1)
except Exception as e:
    print(f"[ERROR] Could not check port: {e}\n")
    exit(1)

# Try to connect without auth
print("[2] Trying to connect without authentication...")
try:
    client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=3000)
    client.admin.command('ping')
    print("[OK] Connected without authentication\n")
    client.close()
except Exception as e:
    print(f"[FAIL] {str(e)[:100]}\n")
    
    # Try with auth
    print("[3] Trying to connect with authentication (admin:admin123)...")
    try:
        client = MongoClient('mongodb://admin:admin123@localhost:27017', serverSelectionTimeoutMS=3000)
        client.admin.command('ping')
        print("[OK] Connected with authentication\n")
        print("[INFO] Your MongoDB has authentication enabled")
        print("[HELP] To disable auth temporarily, run: mongod --noauth")
        client.close()
    except Exception as e2:
        print(f"[FAIL] {str(e2)[:100]}\n")
        print("[ERROR] Could not connect to MongoDB with or without authentication")
        print("\n[HELP] Possible solutions:")
        print("   1. Make sure MongoDB is running")
        print("   2. Check if MongoDB is listening on port 27017")
        print("   3. If auth is enabled, disable it: mongod --noauth")
        print("   4. Check MongoDB logs for errors")
        exit(1)

print("[SUCCESS] MongoDB is accessible!")
print("\n[NEXT] Run: python seed_local.py")
