from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.models import FilmStatus

Score = Annotated[int, Field(ge=1, le=10)]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- auth ----
class RegisterIn(BaseModel):
    username: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=50)]
    display_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]
    password: Annotated[str, Field(min_length=8, max_length=128)]
    join_code: str

    @field_validator("username")
    @classmethod
    def _normalize_username(cls, v: str) -> str:
        v = v.lower()
        if not all(c.isalnum() or c in "_-." for c in v):
            raise ValueError("username may only contain letters, digits, '_', '-' and '.'")
        return v


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(ORMModel):
    id: int
    username: str
    display_name: str


# ---- ratings ----
class RatingIn(BaseModel):
    badness: Score
    fun: Score
    comment: Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)] | None = None


class RatingOut(ORMModel):
    id: int
    film_id: int
    user: UserOut
    badness: int
    fun: int
    comment: str | None
    created_at: datetime
    updated_at: datetime


# ---- films ----
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]


class FilmCreate(BaseModel):
    title: Title
    year: Annotated[int, Field(ge=1888, le=2100)] | None = None
    poster_url: Annotated[str, Field(max_length=500)] | None = None
    tmdb_id: int | None = None
    status: FilmStatus = FilmStatus.watchlist
    watched_on: date | None = None


class FilmUpdate(BaseModel):
    title: Title | None = None
    year: Annotated[int, Field(ge=1888, le=2100)] | None = None
    poster_url: Annotated[str, Field(max_length=500)] | None = None
    status: FilmStatus | None = None
    watched_on: date | None = None


class QuoteIn(BaseModel):
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class QuoteOut(ORMModel):
    id: int
    film_id: int
    user: UserOut
    text: str
    created_at: datetime


class FilmOut(ORMModel):
    id: int
    title: str
    year: int | None
    poster_url: str | None
    tmdb_id: int | None
    status: FilmStatus
    watched_on: date | None
    added_by: int
    created_at: datetime
    rating_count: int = 0
    # Ids of the members voting for this film as the next one to watch.
    vote_user_ids: list[int] = []


class FilmDetail(FilmOut):
    ratings: list[RatingOut]
    quotes: list[QuoteOut]


class TmdbResult(BaseModel):
    tmdb_id: int
    title: str
    year: int | None
    poster_url: str | None
    overview: str | None


# ---- rankings / stats / export ----
class ScoreChip(BaseModel):
    user_id: int
    display_name: str
    badness: int
    fun: int


class RankedFilm(BaseModel):
    rank: int
    id: int
    title: str
    year: int | None
    poster_url: str | None
    watched_on: date | None
    rating_count: int
    avg_badness: float
    avg_fun: float
    avg_combined: float
    scores: list[ScoreChip]


class CriticStat(BaseModel):
    user_id: int
    display_name: str
    rating_count: int
    avg_badness: float
    avg_fun: float


class FilmHighlight(BaseModel):
    id: int
    title: str
    score: float


class StatsOut(BaseModel):
    films_watched: int
    films_on_watchlist: int
    total_ratings: int
    members: int
    harshest_critic: CriticStat | None
    most_generous_critic: CriticStat | None
    worst_film: FilmHighlight | None
    most_fun_film: FilmHighlight | None


class ExportUser(ORMModel):
    id: int
    username: str
    display_name: str
    created_at: datetime


class ExportFilm(ORMModel):
    id: int
    title: str
    year: int | None
    poster_url: str | None
    tmdb_id: int | None
    status: FilmStatus
    watched_on: date | None
    added_by: int
    created_at: datetime


class ExportRating(ORMModel):
    id: int
    film_id: int
    user_id: int
    badness: int
    fun: int
    comment: str | None
    created_at: datetime
    updated_at: datetime


class ExportOut(BaseModel):
    exported_at: datetime
    users: list[ExportUser]
    films: list[ExportFilm]
    ratings: list[ExportRating]
