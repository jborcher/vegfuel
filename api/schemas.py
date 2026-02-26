from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, Any
from datetime import date, datetime


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SocialAuthRequest(BaseModel):
    """Accepts an ID token from Google or Apple and exchanges for a VegFuel JWT."""
    provider: str          # "google" | "apple"
    id_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


# ── User ──────────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: str
    email: Optional[str]
    display_name: Optional[str]
    provider: str
    body_weight: Optional[float]
    weight_unit: str
    goal_cal: Optional[int]
    goal_protein: Optional[float]
    goal_carbs: Optional[float]
    goal_fat: Optional[float]

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    body_weight: Optional[float] = None
    weight_unit: Optional[str] = None
    goal_cal: Optional[int] = None
    goal_protein: Optional[float] = None
    goal_carbs: Optional[float] = None
    goal_fat: Optional[float] = None


# ── Food Log ──────────────────────────────────────────────────────────────────

class LogEntryIn(BaseModel):
    id: Optional[str] = None          # client can supply its own UUID for sync
    ingredient_name: str
    amount: float
    display_amount: float
    unit: str
    position: int = 0


class LogEntryOut(BaseModel):
    id: str
    ingredient_name: str
    amount: float
    display_amount: float
    unit: str
    position: int
    synced_at: datetime

    class Config:
        from_attributes = True


class LogDay(BaseModel):
    log_date: date
    entries: list[LogEntryOut]


class BulkSyncRequest(BaseModel):
    """Client sends its full local log for a date; server merges and returns canonical list."""
    log_date: date
    entries: list[LogEntryIn]


# ── Mixtures ──────────────────────────────────────────────────────────────────

class MixtureIn(BaseModel):
    name: str
    yield_g: float
    yield_unit: str = "g"
    per100g: dict[str, Any]
    ingredients: list[dict[str, Any]]


class MixtureOut(BaseModel):
    id: str
    name: str
    yield_g: float
    yield_unit: str
    per100g: dict[str, Any]
    ingredients: list[dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Custom Ingredients ────────────────────────────────────────────────────────

class CustomIngredientIn(BaseModel):
    name: str
    nutrition: dict[str, Any]        # per-100g nutrition object


class CustomIngredientOut(BaseModel):
    id: str
    name: str
    nutrition: dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
