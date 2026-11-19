from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select

from app.auth import CurrentUser, DbSession, get_current_user
from app.models import Film, FilmStatus, Rating
from app.schemas import RatingIn, RatingOut

router = APIRouter(prefix="/films", tags=["ratings"], dependencies=[Depends(get_current_user)])


def _film_or_404(db: DbSession, film_id: int) -> Film:
    film = db.get(Film, film_id)
    if film is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Film not found")
    return film


@router.put("/{film_id}/rating", response_model=RatingOut)
def upsert_rating(film_id: int, body: RatingIn, db: DbSession, user: CurrentUser) -> Rating:
    film = _film_or_404(db, film_id)
    if film.status != FilmStatus.watched:
        raise HTTPException(status.HTTP_409_CONFLICT, "You can only rate films that were watched")
    rating = db.scalar(select(Rating).where(Rating.film_id == film_id, Rating.user_id == user.id))
    if rating is None:
        rating = Rating(film_id=film_id, user_id=user.id)
        db.add(rating)
    rating.badness = body.badness
    rating.fun = body.fun
    rating.comment = body.comment or None
    db.commit()
    db.refresh(rating)
    return rating


@router.delete("/{film_id}/rating", status_code=status.HTTP_204_NO_CONTENT)
def delete_rating(film_id: int, db: DbSession, user: CurrentUser) -> Response:
    _film_or_404(db, film_id)
    rating = db.scalar(select(Rating).where(Rating.film_id == film_id, Rating.user_id == user.id))
    if rating is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "You haven't rated this film")
    db.delete(rating)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
