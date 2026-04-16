"""
database.py — MongoDB connection for Sports Diary API

ROOT CAUSE FIX:
  The old version called os.getenv("MONGODB_URL") at module-load time,
  which ran BEFORE python-dotenv had loaded .env, so it always fell back
  to "mongodb://localhost:27017".

  This version imports `settings` from config.py instead.  pydantic-settings
  loads .env during Settings() construction (which happens once at import
  time of config.py), so by the time database.py is imported the value is
  already correctly set from .env.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from urllib.parse import quote_plus

# ── Import settings (loads .env via pydantic-settings) ───────────────────────
from app.core.config import settings


def encode_mongodb_url(url: str) -> str:
    """
    Percent-encode credentials in a MongoDB URL if they are not already encoded.
    Detects existing encoding by checking for a '%' sign — if present, skips.
    Handles passwords containing '@' by splitting on the LAST '@' in the
    credentials section.
    """
    if not url or "%" in url or "@" not in url:
        return url

    try:
        if url.startswith("mongodb+srv://"):
            protocol, rest = "mongodb+srv://", url[14:]
        elif url.startswith("mongodb://"):
            protocol, rest = "mongodb://", url[10:]
        else:
            return url

        last_at = rest.rfind("@")
        if last_at == -1:
            return url

        credentials, host = rest[:last_at], rest[last_at + 1:]
        colon = credentials.find(":")
        if colon == -1:
            return f"{protocol}{quote_plus(credentials)}@{host}"

        username = credentials[:colon]
        password = credentials[colon + 1:]
        return f"{protocol}{quote_plus(username)}:{quote_plus(password)}@{host}"

    except Exception as exc:
        print(f"[MONGO] Warning: could not encode URL — {exc}")
        return url


# ── Build the connection URL once at import time ──────────────────────────────
print("[STARTUP] Loading MongoDB configuration...")
MONGODB_URL   = encode_mongodb_url(settings.MONGODB_URL)
DATABASE_NAME = settings.DATABASE_NAME
print(f"[STARTUP] MongoDB URL configured | database: {DATABASE_NAME}")

# ── Global client ─────────────────────────────────────────────────────────────
mongodb_client: Optional[AsyncIOMotorClient] = None


def get_database():
    """Return the Motor database instance."""
    return mongodb_client[DATABASE_NAME]


def get_collection(collection_name: str):
    """Return a specific collection."""
    return get_database()[collection_name]


async def connect_to_mongo():
    """Open the MongoDB connection on FastAPI startup."""
    global mongodb_client
    try:
        print("[MONGO] Connecting to MongoDB...")
        print(f"[MONGO] Database: {DATABASE_NAME}")

        # Strip any ssl_cert_reqs param that breaks Atlas connections
        clean_url = MONGODB_URL
        if "ssl_cert_reqs=" in clean_url:
            base, _, qs = clean_url.partition("?")
            params = [p for p in qs.split("&") if not p.startswith("ssl_cert_reqs=")]
            clean_url = base + ("?" + "&".join(params) if params else "")

        print("[MONGO] Creating MongoDB client...")

        if clean_url.startswith("mongodb+srv://"):
            # Atlas — TLS/SSL is automatic with SRV
            mongodb_client = AsyncIOMotorClient(
                clean_url,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                retryWrites=True,
            )
        else:
            # Local MongoDB
            mongodb_client = AsyncIOMotorClient(
                clean_url,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
            )

        print("[MONGO] Verifying connection with ping...")
        await mongodb_client.admin.command("ping")
        print("[MONGO] ✅ Connected to MongoDB successfully")
        print(f"[MONGO] ✅ Using database: {DATABASE_NAME}")

        await create_indexes()
        print("[MONGO] ✅ Database indexes created")

    except Exception as exc:
        print(f"[MONGO] ❌ FAILED to connect to MongoDB")
        print(f"[MONGO] Error: {exc}")
        print("[MONGO] Check: MONGODB_URL in .env, Atlas Network Access whitelist, password encoding")
        raise


async def close_mongo_connection():
    """Close the MongoDB connection on FastAPI shutdown."""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        print("✅ MongoDB connection closed")


async def create_indexes():
    """Create indexes for all collections."""
    db = get_database()

    await db.users.create_index("phone", unique=True)
    await db.users.create_index("email", unique=True, sparse=True)
    await db.users.create_index([("city", 1), ("state", 1)])
    await db.users.create_index([("latitude", 1), ("longitude", 1)])

    await db.venues.create_index("city")
    await db.venues.create_index([("latitude", 1), ("longitude", 1)])
    await db.venues.create_index("is_active")

    await db.tournaments.create_index("city")
    await db.tournaments.create_index("sport_type")
    await db.tournaments.create_index([("latitude", 1), ("longitude", 1)])
    await db.tournaments.create_index("status")

    await db.shops.create_index("city")
    await db.shops.create_index("category")
    await db.shops.create_index([("latitude", 1), ("longitude", 1)])

    await db.jobs.create_index("city")
    await db.jobs.create_index("job_type")
    await db.jobs.create_index("status")

    await db.job_applications.create_index("job_id")
    await db.job_applications.create_index("applicant_id")

    await db.matches.create_index("tournament_id")
    await db.matches.create_index([("tournament_id", 1), ("round_number", 1)])

    await db.dictionary.create_index("sport")
    await db.dictionary.create_index("term")
    await db.dictionary.create_index("city")
    await db.dictionary.create_index("slug", unique=True, sparse=True)

    await db.bookings.create_index("booking_number", unique=True)
    await db.bookings.create_index("user_id")
    await db.bookings.create_index("venue_id")
    await db.bookings.create_index([("booking_date", 1), ("venue_id", 1)])


async def get_db():
    """Dependency injection helper."""
    return get_database()


async def init_db():
    """Alias kept for backwards compat."""
    await connect_to_mongo()