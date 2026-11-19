"""The club's "Letterboxd bottom 250 horror films" list, from a snapshot in app/data.

Refresh the snapshot with `uv run python scripts/update_bottom250.py`.
"""

import json
import re
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.auth import DbSession, get_current_user
from app.models import Film
from app.schemas import Bottom250Entry, Bottom250List

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "bottom250.json"

router = APIRouter(tags=["bottom250"], dependencies=[Depends(get_current_user)])


@lru_cache
def _snapshot() -> dict:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def _normalize(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.casefold()).strip()


@router.get("/bottom250", response_model=Bottom250List)
def bottom250(db: DbSession) -> Bottom250List:
    snapshot = _snapshot()
    by_title: dict[str, list[Film]] = {}
    for film in db.scalars(select(Film)):
        by_title.setdefault(_normalize(film.title), []).append(film)

    entries = []
    for item in snapshot["films"]:
        # Same title, and the same year (or a club film that has no year yet).
        match = next(
            (
                f
                for f in by_title.get(_normalize(item["title"]), [])
                if f.year is None or f.year == item["year"]
            ),
            None,
        )
        entries.append(
            Bottom250Entry(
                position=item["position"],
                title=item["title"],
                year=item["year"],
                letterboxd_url=item["letterboxd_url"],
                film_id=match.id if match else None,
                status=match.status if match else None,
            )
        )
    return Bottom250List(
        source=snapshot["source"], fetched_on=snapshot["fetched_on"], films=entries
    )
