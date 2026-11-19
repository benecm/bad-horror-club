from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.auth import CurrentUser, DbSession, get_current_user
from app.models import Film, FilmStatus, Rating
from app.schemas import FilmCreate, FilmDetail, FilmOut, FilmUpdate

router = APIRouter(prefix="/films", tags=["films"], dependencies=[Depends(get_current_user)])


def _out(film: Film) -> FilmOut:
    out = FilmOut.model_validate(film)
    out.rating_count = len(film.ratings)
    return out


def _detail(film: Film) -> FilmDetail:
    out = FilmDetail.model_validate(film)
    out.rating_count = len(film.ratings)
    out.ratings.sort(key=lambda r: r.created_at)
    return out


def get_film_or_404(db: DbSession, film_id: int) -> Film:
    film = db.scalar(
        select(Film)
        .where(Film.id == film_id)
        .options(selectinload(Film.ratings).selectinload(Rating.user))
    )
    if film is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Film not found")
    return film


@router.get("", response_model=list[FilmOut])
def list_films(
    db: DbSession, status_filter: Annotated[FilmStatus | None, Query(alias="status")] = None
) -> list[FilmOut]:
    stmt = select(Film).options(selectinload(Film.ratings)).order_by(Film.created_at.desc())
    if status_filter is not None:
        stmt = stmt.where(Film.status == status_filter)
    return [_out(f) for f in db.scalars(stmt)]


@router.post("", response_model=FilmOut, status_code=status.HTTP_201_CREATED)
def create_film(body: FilmCreate, db: DbSession, user: CurrentUser) -> FilmOut:
    data = body.model_dump()
    if body.status == FilmStatus.watched and body.watched_on is None:
        data["watched_on"] = date.today()
    if body.status == FilmStatus.watchlist:
        data["watched_on"] = None
    film = Film(**data, added_by=user.id)
    db.add(film)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "That TMDB film is already added") from None
    return _out(film)


@router.get("/{film_id}", response_model=FilmDetail)
def read_film(film_id: int, db: DbSession) -> FilmDetail:
    return _detail(get_film_or_404(db, film_id))


@router.patch("/{film_id}", response_model=FilmDetail)
def update_film(film_id: int, body: FilmUpdate, db: DbSession) -> FilmDetail:
    film = get_film_or_404(db, film_id)
    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if value is None and field in ("title", "status"):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"{field} cannot be null")
        setattr(film, field, value)
    if film.status == FilmStatus.watched and film.watched_on is None:
        film.watched_on = date.today()
    if film.status == FilmStatus.watchlist:
        film.watched_on = None
    db.commit()
    return _detail(film)


@router.delete("/{film_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_film(film_id: int, db: DbSession, user: CurrentUser) -> Response:
    film = get_film_or_404(db, film_id)
    if film.added_by != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the person who added it can delete it")
    db.delete(film)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
