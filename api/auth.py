from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import httpx

from config import get_settings
from database import get_db
import models

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()

GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
APPLE_CERTS_URL  = "https://appleid.apple.com/auth/keys"


# ── Password ──────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> str:
    """Returns user_id or raises HTTPException."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ── Current user dependency ───────────────────────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    user_id = decode_token(credentials.credentials)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ── Social token verification ─────────────────────────────────────────────────

async def verify_google_token(id_token: str) -> dict:
    """Verify a Google ID token and return the payload."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": id_token}
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Google token")
    data = resp.json()
    if "error" in data:
        raise HTTPException(status_code=401, detail=data.get("error_description", "Invalid Google token"))
    return data   # contains: sub, email, name, picture


async def verify_apple_token(id_token: str) -> dict:
    """
    Verify an Apple ID token.
    Apple tokens are JWTs signed with Apple's public keys.
    For a production app, fetch Apple's JWKS and verify the signature properly.
    Here we decode without verification as a starting point —
    replace with full JWKS verification before shipping.
    """
    try:
        # Decode header to get kid, then fetch Apple's public key
        header = jwt.get_unverified_header(id_token)
        async with httpx.AsyncClient() as client:
            jwks_resp = await client.get(APPLE_CERTS_URL)
        jwks = jwks_resp.json()

        # Find matching key
        key = next((k for k in jwks["keys"] if k["kid"] == header["kid"]), None)
        if not key:
            raise HTTPException(status_code=401, detail="Apple key not found")

        from jose.backends import RSAKey
        from jose import jwk
        public_key = jwk.construct(key)

        payload = jwt.decode(
            id_token,
            public_key,
            algorithms=["RS256"],
            audience="com.yourapp.vegfuel",   # ← replace with your Apple bundle ID
        )
        return payload   # contains: sub (Apple user ID), email
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Apple token: {e}")
