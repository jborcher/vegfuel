from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from database import get_db
from auth import get_current_user
import models, schemas
from models import gen_uuid

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/{log_date}", response_model=schemas.LogDay)
def get_log(
    log_date: date,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    entries = (
        db.query(models.FoodLog)
        .filter(
            models.FoodLog.user_id == current_user.id,
            models.FoodLog.log_date == log_date,
        )
        .order_by(models.FoodLog.position)
        .all()
    )
    return {"log_date": log_date, "entries": entries}


@router.post("/sync", response_model=schemas.LogDay)
def sync_log(
    body: schemas.BulkSyncRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Offline-first sync: client sends its full local list for a date.
    Server replaces the day's entries with the client's version.
    Returns the canonical server state.
    
    Strategy: last-write-wins per day. Good enough for a single-user
    nutrition tracker; upgrade to CRDT if multi-device conflicts matter.
    """
    # Delete existing entries for that day
    db.query(models.FoodLog).filter(
        models.FoodLog.user_id == current_user.id,
        models.FoodLog.log_date == body.log_date,
    ).delete()

    # Insert new entries
    new_entries = []
    for i, entry in enumerate(body.entries):
        log = models.FoodLog(
            id=entry.id or gen_uuid(),
            user_id=current_user.id,
            log_date=body.log_date,
            ingredient_name=entry.ingredient_name,
            amount=entry.amount,
            display_amount=entry.display_amount,
            unit=entry.unit,
            position=entry.position if entry.position else i,
        )
        db.add(log)
        new_entries.append(log)

    db.commit()
    for e in new_entries:
        db.refresh(e)

    return {"log_date": body.log_date, "entries": new_entries}


@router.delete("/{log_date}/{entry_id}", status_code=204)
def delete_entry(
    log_date: date,
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    entry = db.query(models.FoodLog).filter(
        models.FoodLog.id == entry_id,
        models.FoodLog.user_id == current_user.id,
        models.FoodLog.log_date == log_date,
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(entry)
    db.commit()


@router.delete("/{log_date}", status_code=204)
def clear_day(
    log_date: date,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db.query(models.FoodLog).filter(
        models.FoodLog.user_id == current_user.id,
        models.FoodLog.log_date == log_date,
    ).delete()
    db.commit()
