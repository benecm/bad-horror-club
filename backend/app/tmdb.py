"""Thin TMDB client. The API key stays on the server and never reaches the browser."""

import httpx

from app.config import get_settings
from app.schemas import TmdbResult

SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
POSTER_BASE = "https://image.tmdb.org/t/p/w342"
MAX_RESULTS = 8


class TmdbNotConfiguredError(Exception):
    pass


class TmdbUnavailableError(Exception):
    pass


def search_movies(query: str) -> list[TmdbResult]:
    api_key = get_settings().tmdb_api_key
    if not api_key:
        raise TmdbNotConfiguredError
    try:
        response = httpx.get(
            SEARCH_URL,
            params={"api_key": api_key, "query": query, "include_adult": "false"},
            timeout=8.0,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError):
        # Deliberately no details: httpx error messages contain the request URL, key included.
        raise TmdbUnavailableError from None

    results = []
    for item in payload.get("results", [])[:MAX_RESULTS]:
        release = item.get("release_date") or ""
        poster = item.get("poster_path")
        results.append(
            TmdbResult(
                tmdb_id=item["id"],
                title=item.get("title") or item.get("original_title") or "Untitled",
                year=int(release[:4]) if release[:4].isdigit() else None,
                poster_url=f"{POSTER_BASE}{poster}" if poster else None,
                overview=(item.get("overview") or None),
            )
        )
    return results
