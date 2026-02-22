from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db
from auth import get_current_user
import models, schemas

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get("/", response_model=list[schemas.CustomIngredientOut])
def list_ingredients(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return db.query(models.CustomIngredient).filter(
        models.CustomIngredient.user_id == current_user.id
    ).order_by(models.CustomIngredient.name).all()


@router.post("/", response_model=schemas.CustomIngredientOut, status_code=201)
def create_ingredient(
    body: schemas.CustomIngredientIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Upsert by name
    existing = db.query(models.CustomIngredient).filter(
        models.CustomIngredient.user_id == current_user.id,
        models.CustomIngredient.name == body.name,
    ).first()

    if existing:
        existing.nutrition = body.nutrition
        db.commit()
        db.refresh(existing)
        return existing

    ingredient = models.CustomIngredient(
        user_id=current_user.id,
        name=body.name,
        nutrition=body.nutrition,
    )
    db.add(ingredient)
    try:
        db.commit()
        db.refresh(ingredient)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ingredient name conflict")
    return ingredient


@router.delete("/{ingredient_id}", status_code=204)
def delete_ingredient(
    ingredient_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ingredient = db.query(models.CustomIngredient).filter(
        models.CustomIngredient.id == ingredient_id,
        models.CustomIngredient.user_id == current_user.id,
    ).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    db.delete(ingredient)
    db.commit()
