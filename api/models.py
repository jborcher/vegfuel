from sqlalchemy import (
    Column, String, Float, Integer, Boolean,
    DateTime, Date, ForeignKey, JSON, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id           = Column(String, primary_key=True, default=gen_uuid)
    email        = Column(String, unique=True, nullable=True, index=True)
    display_name = Column(String, nullable=True)
    password_hash= Column(String, nullable=True)      # null for social-only users
    provider     = Column(String, default="email")    # email | google | apple
    provider_id  = Column(String, nullable=True)      # sub from Google/Apple JWT
    body_weight  = Column(Float, nullable=True)       # in kg
    weight_unit  = Column(String, default="kg")       # kg | lbs
    goal_cal     = Column(Integer, nullable=True)
    goal_protein = Column(Float, nullable=True)
    goal_carbs   = Column(Float, nullable=True)
    goal_fat     = Column(Float, nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())

    logs        = relationship("FoodLog",         back_populates="user", cascade="all, delete-orphan")
    mixtures    = relationship("Mixture",         back_populates="user", cascade="all, delete-orphan")
    ingredients = relationship("CustomIngredient",back_populates="user", cascade="all, delete-orphan")


class FoodLog(Base):
    """One row per ingredient entry per day per user."""
    __tablename__ = "food_logs"

    id             = Column(String, primary_key=True, default=gen_uuid)
    user_id        = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    log_date       = Column(Date, nullable=False, index=True)
    ingredient_name= Column(String, nullable=False)
    amount         = Column(Float, nullable=False)          # always in grams
    display_amount = Column(Float, nullable=False)
    unit           = Column(String, nullable=False)
    position       = Column(Integer, default=0)             # ordering in the log
    synced_at      = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="logs")

    __table_args__ = (
        UniqueConstraint("id", "user_id", name="uq_log_user"),
    )


class Mixture(Base):
    __tablename__ = "mixtures"

    id          = Column(String, primary_key=True, default=gen_uuid)
    user_id     = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name        = Column(String, nullable=False)
    yield_g     = Column(Float, nullable=False)
    yield_unit  = Column(String, default="g")
    per100g     = Column(JSON, nullable=False)        # {cal, protein, carbs, fat, ...}
    ingredients = Column(JSON, nullable=False)        # [{name, amount, displayAmount, unit}]
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="mixtures")

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_mixture_user_name"),
    )


class CustomIngredient(Base):
    __tablename__ = "custom_ingredients"

    id          = Column(String, primary_key=True, default=gen_uuid)
    user_id     = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name        = Column(String, nullable=False)
    nutrition   = Column(JSON, nullable=False)         # per-100g nutrition object
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="ingredients")

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_ingredient_user_name"),
    )


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    token      = Column(String, primary_key=True)
    email      = Column(String, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used       = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
