from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db
from auth import get_current_user
import models, schemas

router = APIRouter(prefix="/mixtures", tags=["mixtures"])


@router.get("/", response_model=list[schemas.MixtureOut])
def list_mixtures(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return db.query(models.Mixture).filter(
        models.Mixture.user_id == current_user.id
    ).order_by(models.Mixture.created_at).all()


@router.post("/", response_model=schemas.MixtureOut, status_code=201)
def create_mixture(
    body: schemas.MixtureIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Upsert by name — if a mixture with this name exists, update it
    existing = db.query(models.Mixture).filter(
        models.Mixture.user_id == current_user.id,
        models.Mixture.name == body.name,
    ).first()

    if existing:
        existing.yield_g     = body.yield_g
        existing.yield_unit  = body.yield_unit
        existing.per100g     = body.per100g
        existing.ingredients = body.ingredients
        db.commit()
        db.refresh(existing)
        return existing

    mixture = models.Mixture(
        user_id=current_user.id,
        name=body.name,
        yield_g=body.yield_g,
        yield_unit=body.yield_unit,
        per100g=body.per100g,
        ingredients=body.ingredients,
    )
    db.add(mixture)
    try:
        db.commit()
        db.refresh(mixture)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Mixture name conflict")
    return mixture


@router.put("/{mixture_id}", response_model=schemas.MixtureOut)
def update_mixture(
    mixture_id: str,
    body: schemas.MixtureIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    mixture = db.query(models.Mixture).filter(
        models.Mixture.id == mixture_id,
        models.Mixture.user_id == current_user.id,
    ).first()
    if not mixture:
        raise HTTPException(status_code=404, detail="Mixture not found")

    mixture.name        = body.name
    mixture.yield_g     = body.yield_g
    mixture.yield_unit  = body.yield_unit
    mixture.per100g     = body.per100g
    mixture.ingredients = body.ingredients
    db.commit()
    db.refresh(mixture)
    return mixture


@router.delete("/{mixture_id}", status_code=204)
def delete_mixture(
    mixture_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    mixture = db.query(models.Mixture).filter(
        models.Mixture.id == mixture_id,
        models.Mixture.user_id == current_user.id,
    ).first()
    if not mixture:
        raise HTTPException(status_code=404, detail="Mixture not found")
    db.delete(mixture)
    db.commit()
