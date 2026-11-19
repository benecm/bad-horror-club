from datetime import date

from fastapi.testclient import TestClient

from .conftest import Headers


def add_film(client: TestClient, headers: Headers, **kwargs: object) -> dict:
    r = client.post("/api/films", json={"title": "Sharknado", **kwargs}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def test_create_watchlist_film(client: TestClient, alice: Headers) -> None:
    film = add_film(client, alice, year=2013)
    assert film["status"] == "watchlist"
    assert film["watched_on"] is None
    assert film["rating_count"] == 0


def test_create_watched_film_defaults_date_to_today(client: TestClient, alice: Headers) -> None:
    film = add_film(client, alice, status="watched")
    assert film["watched_on"] == date.today().isoformat()


def test_duplicate_tmdb_id_conflicts(client: TestClient, alice: Headers) -> None:
    add_film(client, alice, tmdb_id=123)
    r = client.post("/api/films", json={"title": "Again", "tmdb_id": 123}, headers=alice)
    assert r.status_code == 409


def test_create_validation(client: TestClient, alice: Headers) -> None:
    assert client.post("/api/films", json={"title": "  "}, headers=alice).status_code == 422
    r = client.post("/api/films", json={"title": "X", "year": 1500}, headers=alice)
    assert r.status_code == 422


def test_list_and_filter_by_status(client: TestClient, alice: Headers) -> None:
    add_film(client, alice, title="Planned")
    add_film(client, alice, title="Seen", status="watched")
    assert len(client.get("/api/films", headers=alice).json()) == 2
    r = client.get("/api/films?status=watched", headers=alice)
    assert [f["title"] for f in r.json()] == ["Seen"]
    assert client.get("/api/films?status=bogus", headers=alice).status_code == 422


def test_get_film_detail_and_404(client: TestClient, alice: Headers) -> None:
    film = add_film(client, alice)
    r = client.get(f"/api/films/{film['id']}", headers=alice)
    assert r.status_code == 200
    assert r.json()["ratings"] == []
    assert client.get("/api/films/999999", headers=alice).status_code == 404


def test_mark_as_watched_via_patch(client: TestClient, alice: Headers, bob: Headers) -> None:
    film = add_film(client, alice)
    r = client.patch(f"/api/films/{film['id']}", json={"status": "watched"}, headers=bob)
    assert r.status_code == 200  # anyone in the club can edit
    assert r.json()["status"] == "watched"
    assert r.json()["watched_on"] == date.today().isoformat()


def test_patch_back_to_watchlist_clears_date(client: TestClient, alice: Headers) -> None:
    film = add_film(client, alice, status="watched")
    r = client.patch(f"/api/films/{film['id']}", json={"status": "watchlist"}, headers=alice)
    assert r.json()["watched_on"] is None


def test_patch_rejects_null_title(client: TestClient, alice: Headers) -> None:
    film = add_film(client, alice)
    r = client.patch(f"/api/films/{film['id']}", json={"title": None}, headers=alice)
    assert r.status_code == 422


def test_only_adder_can_delete(client: TestClient, alice: Headers, bob: Headers) -> None:
    film = add_film(client, alice)
    assert client.delete(f"/api/films/{film['id']}", headers=bob).status_code == 403
    assert client.delete(f"/api/films/{film['id']}", headers=alice).status_code == 204
    assert client.get(f"/api/films/{film['id']}", headers=alice).status_code == 404


def test_delete_film_cascades_to_ratings(client: TestClient, alice: Headers, bob: Headers) -> None:
    film = add_film(client, alice, status="watched")
    r = client.put(f"/api/films/{film['id']}/rating", json={"badness": 5, "fun": 5}, headers=bob)
    assert r.status_code == 200
    assert client.delete(f"/api/films/{film['id']}", headers=alice).status_code == 204
