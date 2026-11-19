import httpx
import pytest
from fastapi.testclient import TestClient

from app import tmdb
from app.config import get_settings

from .conftest import Headers

SECRET = "super-secret-tmdb-key"


class FakeResponse:
    def __init__(self, payload: dict, status: int = 200) -> None:
        self._payload, self.status_code = payload, status

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"boom https://api.themoviedb.org/3/search/movie?api_key={SECRET}",
                request=httpx.Request("GET", "https://x"),
                response=httpx.Response(self.status_code),
            )

    def json(self) -> dict:
        return self._payload


@pytest.fixture()
def with_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "tmdb_api_key", SECRET)


def test_search_maps_results(
    client: TestClient, alice: Headers, with_key: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: dict = {}

    def fake_get(url: str, params: dict, timeout: float) -> FakeResponse:
        seen.update(params)
        return FakeResponse(
            {
                "results": [
                    {
                        "id": 1,
                        "title": "Sharknado",
                        "release_date": "2013-07-11",
                        "poster_path": "/abc.jpg",
                        "overview": "Sharks. Tornado.",
                    },
                    {"id": 2, "title": "No Date Or Poster", "release_date": ""},
                ]
            }
        )

    monkeypatch.setattr(tmdb.httpx, "get", fake_get)
    r = client.get("/api/tmdb/search?q=shark", headers=alice)
    assert r.status_code == 200
    first, second = r.json()
    assert first == {
        "tmdb_id": 1,
        "title": "Sharknado",
        "year": 2013,
        "poster_url": "https://image.tmdb.org/t/p/w342/abc.jpg",
        "overview": "Sharks. Tornado.",
    }
    assert second["year"] is None and second["poster_url"] is None
    assert seen["query"] == "shark"
    assert SECRET not in r.text  # the key never goes to the browser


def test_search_without_key_is_503(
    client: TestClient, alice: Headers, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(get_settings(), "tmdb_api_key", "")
    assert client.get("/api/tmdb/search?q=shark", headers=alice).status_code == 503


def test_upstream_failure_is_502_and_does_not_leak_the_key(
    client: TestClient, alice: Headers, with_key: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(tmdb.httpx, "get", lambda *a, **k: FakeResponse({}, status=401))
    r = client.get("/api/tmdb/search?q=shark", headers=alice)
    assert r.status_code == 502
    assert SECRET not in r.text


def test_network_error_is_502(
    client: TestClient, alice: Headers, with_key: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(*a: object, **k: object) -> None:
        raise httpx.ConnectTimeout(f"timeout for api_key={SECRET}")

    monkeypatch.setattr(tmdb.httpx, "get", boom)
    r = client.get("/api/tmdb/search?q=shark", headers=alice)
    assert r.status_code == 502
    assert SECRET not in r.text


def test_search_validation_and_auth(client: TestClient, alice: Headers) -> None:
    assert client.get("/api/tmdb/search?q=a", headers=alice).status_code == 422
    assert client.get("/api/tmdb/search").status_code == 401
    assert client.get("/api/tmdb/search?q=shark").status_code == 401


def test_film_can_be_created_from_a_tmdb_result(client: TestClient, alice: Headers) -> None:
    r = client.post(
        "/api/films",
        json={
            "title": "Sharknado",
            "year": 2013,
            "tmdb_id": 1,
            "poster_url": "https://image.tmdb.org/t/p/w342/abc.jpg",
        },
        headers=alice,
    )
    assert r.status_code == 201
    assert r.json()["poster_url"].endswith("/abc.jpg")
