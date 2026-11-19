from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.auth import DbSession, get_current_user
from app.models import Film, Rating, User
from app.schemas import ExportFilm, ExportOut, ExportRating, ExportUser

router = APIRouter(tags=["export"], dependencies=[Depends(get_current_user)])


@router.get("/export", response_model=ExportOut)
def export_everything(db: DbSession) -> ExportOut:
    """Full JSON dump (no password hashes), as an extra backup."""
    return ExportOut(
        exported_at=datetime.now(UTC),
        users=[ExportUser.model_validate(u) for u in db.scalars(select(User).order_by(User.id))],
        films=[ExportFilm.model_validate(f) for f in db.scalars(select(Film).order_by(Film.id))],
        ratings=[
            ExportRating.model_validate(r) for r in db.scalars(select(Rating).order_by(Rating.id))
        ],
    )
