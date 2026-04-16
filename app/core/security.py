from datetime import datetime, timedelta
from typing import Optional
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import random
import string
import hashlib
import hmac
from cryptography.fernet import Fernet

from app.core.config import settings
from app.core.database import get_database

security = HTTPBearer()

otp_storage = {}
otp_attempts = {}


def generate_otp(length: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=length))


def hash_otp(otp: str, identifier: str) -> str:
    return hashlib.sha256(f"{otp}{identifier}{settings.OTP_SECRET_KEY}".encode()).hexdigest()


def store_otp(identifier: str, otp: str):
    """Store OTP keyed by phone or email."""
    otp_hash = hash_otp(otp, identifier)
    otp_storage[identifier] = {
        "otp_hash": otp_hash,
        "expires_at": datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
        "attempts": 0,
        "created_at": datetime.utcnow()
    }
    otp_attempts[identifier] = {"failed_attempts": 0, "last_attempt": None}
    print(f"[OTP] Stored OTP for {identifier} (hashed)")


def verify_otp(identifier: str, otp: str) -> bool:
    """Verify OTP — works for both phone and email identifiers."""
    print(f"[OTP] Verifying OTP for {identifier}")
    if identifier in otp_attempts:
        if otp_attempts[identifier]["failed_attempts"] >= settings.OTP_MAX_ATTEMPTS:
            print(f"[OTP] Rate limit exceeded for {identifier}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Please try again later."
            )
    if identifier not in otp_storage:
        print(f"[OTP] Identifier not found in storage")
        return False
    stored = otp_storage[identifier]
    if datetime.utcnow() > stored["expires_at"]:
        print(f"[OTP] OTP expired")
        del otp_storage[identifier]
        if identifier in otp_attempts:
            del otp_attempts[identifier]
        return False
    provided_hash = hash_otp(otp, identifier)
    if not hmac.compare_digest(provided_hash, stored["otp_hash"]):
        print(f"[OTP] OTP mismatch")
        if identifier not in otp_attempts:
            otp_attempts[identifier] = {"failed_attempts": 0, "last_attempt": None}
        otp_attempts[identifier]["failed_attempts"] += 1
        otp_attempts[identifier]["last_attempt"] = datetime.utcnow()
        return False
    print(f"[OTP] OTP verified successfully!")
    del otp_storage[identifier]
    if identifier in otp_attempts:
        del otp_attempts[identifier]
    return True


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except InvalidTokenError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Get current authenticated user — supports phone AND email login."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token   = credentials.credentials
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    sub: str = payload.get("sub")
    if not sub:
        raise credentials_exception

    db = get_database()
    # sub can be a phone (+91...) or an email
    if sub.startswith("+"):
        user = await db.users.find_one({"phone": sub})
    elif "@" in sub:
        user = await db.users.find_one({"email": sub})
    else:
        user = await db.users.find_one({"phone": sub})

    if user is None:
        raise credentials_exception

    # Back-fill roles list for legacy documents
    if not user.get("roles"):
        old_role = user.get("role", "player")
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"roles": [old_role] if old_role else ["player"]}},
        )
        user["roles"] = [old_role] if old_role else ["player"]

    return user
