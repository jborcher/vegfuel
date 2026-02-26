from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db
import models, schemas, auth as auth_utils

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.TokenResponse)
def register(body: schemas.RegisterRequest, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = models.User(
        email=body.email,
        display_name=body.display_name or body.email.split("@")[0],
        password_hash=auth_utils.hash_password(body.password),
        provider="email",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = auth_utils.create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/login", response_model=schemas.TokenResponse)
def login(body: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.email == body.email,
        models.User.provider == "email"
    ).first()

    if not user or not auth_utils.verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = auth_utils.create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/social", response_model=schemas.TokenResponse)
async def social_auth(body: schemas.SocialAuthRequest, db: Session = Depends(get_db)):
    """
    Exchange a Google or Apple ID token for a VegFuel JWT.
    Creates a new user account on first login.
    """
    if body.provider == "google":
        payload = await auth_utils.verify_google_token(body.id_token)
        provider_id = payload["sub"]
        email       = payload.get("email")
        name        = payload.get("name")
    elif body.provider == "apple":
        payload = await auth_utils.verify_apple_token(body.id_token)
        provider_id = payload["sub"]
        email       = payload.get("email")   # only provided on first Apple login
        name        = None
    else:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    # Look up by provider + provider_id first (most reliable)
    user = db.query(models.User).filter(
        models.User.provider == body.provider,
        models.User.provider_id == provider_id,
    ).first()

    if not user and email:
        # Check if they registered with email first — link accounts
        user = db.query(models.User).filter(models.User.email == email).first()
        if user:
            user.provider    = body.provider
            user.provider_id = provider_id
            db.commit()

    if not user:
        # New user — create account
        user = models.User(
            email=email,
            display_name=name or (email.split("@")[0] if email else "Athlete"),
            provider=body.provider,
            provider_id=provider_id,
        )
        db.add(user)
        try:
            db.commit()
            db.refresh(user)
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Account conflict")

    token = auth_utils.create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer", "user": user}


import os, secrets, resend
from datetime import datetime, timedelta, timezone

@router.post("/forgot-password")
async def forgot_password(body: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.email == body.email,
        models.User.provider == "email"
    ).first()
    # Always return success to prevent email enumeration
    if user:
        # Clean up old tokens for this email
        db.query(models.PasswordResetToken).filter(
            models.PasswordResetToken.email == body.email
        ).delete()
        token = secrets.token_urlsafe(32)
        db_token = models.PasswordResetToken(
            token=token,
            email=body.email,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        db.add(db_token)
        db.commit()
        reset_url = f"https://jborcher.github.io/vegfuel/?reset={token}"
        resend.api_key = os.environ.get("RESEND_API_KEY", "")
        resend.Emails.send({
            "from": "VegFuel <onboarding@resend.dev>",
            "to": body.email,
            "subject": "Reset your VegFuel password",
            "html": f"""
                <h2>🥦 VegFuel Password Reset</h2>
                <p>Click the link below to reset your password. This link expires in 1 hour.</p>
                <p><a href="{reset_url}" style="background:#2d8c4e;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold;">Reset Password</a></p>
                <p>If you didn't request this, you can safely ignore this email.</p>
            """
        })
    return {"message": "If that email exists, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(body: schemas.PasswordResetConfirm, db: Session = Depends(get_db)):
    entry = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.token == body.token,
        models.PasswordResetToken.used == False
    ).first()
    if not entry or datetime.now(timezone.utc) > entry.expires_at.replace(tzinfo=timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    user = db.query(models.User).filter(
        models.User.email == entry.email,
        models.User.provider == "email"
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.password_hash = auth_utils.hash_password(body.new_password)
    entry.used = True
    db.commit()
    return {"message": "Password reset successfully"}
