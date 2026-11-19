"""Quotes (best lines from movie night) and votes (what to watch next)."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select

from app.auth import CurrentUser, DbSession, get_current_user
from app.models import Film, FilmStatus, Quote, Vote
from app.schemas import QuoteIn, QuoteOut

router = APIRouter(tags=["extras"], dependencies=[Depends(get_current_user)])


def _film_or_404(db: DbSession, film_id: int) -> Film:
    film = db.get(Film, film_id)
    if film is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Film not found")
    return film


# ---- quotes ----
@router.post(
    "/films/{film_id}/quotes", response_model=QuoteOut, status_code=status.HTTP_201_CREATED
)
def add_quote(film_id: int, body: QuoteIn, db: DbSession, user: CurrentUser) -> Quote:
    film = _film_or_404(db, film_id)
    if film.status != FilmStatus.watched:
        raise HTTPException(status.HTTP_409_CONFLICT, "Quotes come from films that were watched")
    quote = Quote(film_id=film_id, user_id=user.id, text=body.text)
    db.add(quote)
    db.commit()
    db.refresh(quote)
    return quote


@router.delete("/quotes/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quote(quote_id: int, db: DbSession, user: CurrentUser) -> Response:
    quote = db.get(Quote, quote_id)
    if quote is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Quote not found")
    if quote.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only delete your own quotes")
    db.delete(quote)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---- votes ----
@router.put("/films/{film_id}/vote", status_code=status.HTTP_204_NO_CONTENT)
def cast_vote(film_id: int, db: DbSession, user: CurrentUser) -> Response:
    film = _film_or_404(db, film_id)
    if film.status != FilmStatus.watchlist:
        raise HTTPException(status.HTTP_409_CONFLICT, "You can only vote for watchlist films")
    exists = db.scalar(select(Vote.id).where(Vote.film_id == film_id, Vote.user_id == user.id))
    if exists is None:  # voting twice is a no-op
        db.add(Vote(film_id=film_id, user_id=user.id))
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/films/{film_id}/vote", status_code=status.HTTP_204_NO_CONTENT)
def remove_vote(film_id: int, db: DbSession, user: CurrentUser) -> Response:
    _film_or_404(db, film_id)
    vote = db.scalar(select(Vote).where(Vote.film_id == film_id, Vote.user_id == user.id))
    if vote is not None:  # removing a vote you never cast is a no-op
        db.delete(vote)
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
