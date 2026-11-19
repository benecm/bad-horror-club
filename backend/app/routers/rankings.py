from collections import defaultdict
from enum import StrEnum
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select

from app.auth import DbSession, get_current_user
from app.models import Film, FilmStatus, Rating, User
from app.schemas import CriticStat, FilmHighlight, RankedFilm, ScoreChip, StatsOut

router = APIRouter(tags=["rankings"], dependencies=[Depends(get_current_user)])


class SortMode(StrEnum):
    badness = "badness"  # Hall of shame: the worst film first
    fun = "fun"  # So bad it's good: the most fun film first
    combined = "combined"  # (badness + fun) / 2


def _avg(value: object) -> float:
    return round(float(value), 2)  # type: ignore[arg-type]


def rank_films(db: DbSession, sort: SortMode) -> list[RankedFilm]:
    """Watched films with at least one rating, best-of-the-worst first.

    Averages are computed in SQL. Ranking rules (kept deliberately simple and stable):
    - order by the chosen average, highest first (averages rounded to 2 decimals)
    - ties share a rank and the next rank is skipped (1, 2, 2, 4)
    - inside a tie, more ratings first, then title A-Z, then id
    """
    rows = db.execute(
        select(
            Film,
            func.avg(Rating.badness),
            func.avg(Rating.fun),
            func.count(Rating.id),
        )
        .join(Rating, Rating.film_id == Film.id)
        .where(Film.status == FilmStatus.watched)
        .group_by(Film.id)
    ).all()

    entries = []
    for film, avg_badness, avg_fun, count in rows:
        badness, fun = _avg(avg_badness), _avg(avg_fun)
        combined = round((badness + fun) / 2, 2)
        key = {SortMode.badness: badness, SortMode.fun: fun, SortMode.combined: combined}[sort]
        entries.append((key, film, badness, fun, combined, count))
    entries.sort(key=lambda e: (-e[0], -e[5], e[1].title.lower(), e[1].id))

    chips: dict[int, list[ScoreChip]] = defaultdict(list)
    chip_rows = db.execute(
        select(Rating.film_id, User.id, User.display_name, Rating.badness, Rating.fun)
        .join(User, User.id == Rating.user_id)
        .where(Rating.film_id.in_([e[1].id for e in entries]))
        .order_by(Rating.created_at, Rating.id)
    )
    for film_id, user_id, display_name, badness, fun in chip_rows:
        chips[film_id].append(
            ScoreChip(user_id=user_id, display_name=display_name, badness=badness, fun=fun)
        )

    ranked: list[RankedFilm] = []
    for position, (key, film, badness, fun, combined, count) in enumerate(entries, start=1):
        previous = ranked[-1] if ranked else None
        previous_key = entries[position - 2][0] if previous else None
        rank = previous.rank if previous is not None and previous_key == key else position
        ranked.append(
            RankedFilm(
                rank=rank,
                id=film.id,
                title=film.title,
                year=film.year,
                poster_url=film.poster_url,
                watched_on=film.watched_on,
                rating_count=count,
                avg_badness=badness,
                avg_fun=fun,
                avg_combined=combined,
                scores=chips[film.id],
            )
        )
    return ranked


@router.get("/rankings", response_model=list[RankedFilm])
def rankings(
    db: DbSession, sort: Annotated[SortMode, Query()] = SortMode.combined
) -> list[RankedFilm]:
    return rank_films(db, sort)


@router.get("/stats", response_model=StatsOut)
def stats(db: DbSession) -> StatsOut:
    films_watched = db.scalar(
        select(func.count()).select_from(Film).where(Film.status == FilmStatus.watched)
    )
    films_on_watchlist = db.scalar(
        select(func.count()).select_from(Film).where(Film.status == FilmStatus.watchlist)
    )
    total_ratings = db.scalar(select(func.count()).select_from(Rating))
    members = db.scalar(select(func.count()).select_from(User))

    critics = [
        CriticStat(
            user_id=user_id,
            display_name=display_name,
            rating_count=count,
            avg_badness=_avg(avg_badness),
            avg_fun=_avg(avg_fun),
        )
        for user_id, display_name, count, avg_badness, avg_fun in db.execute(
            select(
                User.id,
                User.display_name,
                func.count(Rating.id),
                func.avg(Rating.badness),
                func.avg(Rating.fun),
            )
            .join(Rating, Rating.user_id == User.id)
            .group_by(User.id)
        )
    ]
    # Harshest = rates films as the most terrible; most generous = the least terrible.
    harshest = max(critics, key=lambda c: (c.avg_badness, -c.user_id), default=None)
    generous = min(critics, key=lambda c: (c.avg_badness, c.user_id), default=None)

    worst = rank_films(db, SortMode.badness)[:1]
    most_fun = rank_films(db, SortMode.fun)[:1]
    return StatsOut(
        films_watched=films_watched or 0,
        films_on_watchlist=films_on_watchlist or 0,
        total_ratings=total_ratings or 0,
        members=members or 0,
        harshest_critic=harshest,
        most_generous_critic=generous,
        worst_film=FilmHighlight(id=worst[0].id, title=worst[0].title, score=worst[0].avg_badness)
        if worst
        else None,
        most_fun_film=FilmHighlight(
            id=most_fun[0].id, title=most_fun[0].title, score=most_fun[0].avg_fun
        )
        if most_fun
        else None,
    )
