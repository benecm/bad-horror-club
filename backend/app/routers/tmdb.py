from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app import tmdb
from app.auth import get_current_user
from app.schemas import TmdbResult

router = APIRouter(prefix="/tmdb", tags=["tmdb"], dependencies=[Depends(get_current_user)])


@router.get("/search", response_model=list[TmdbResult])
def search(q: Annotated[str, Query(min_length=2, max_length=100)]) -> list[TmdbResult]:
    try:
        return tmdb.search_movies(q.strip())
    except tmdb.TmdbNotConfiguredError:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Film search isn't set up on this server"
        ) from None
    except tmdb.TmdbUnavailableError:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Film search is unavailable right now. Try again soon."
        ) from None
