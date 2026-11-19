import json

from fastapi.testclient import TestClient

from app.routers.bottom250 import DATA_FILE

from .conftest import Headers


def test_snapshot_file_is_a_complete_ranked_list() -> None:
    films = json.loads(DATA_FILE.read_text(encoding="utf-8"))["films"]
    assert [f["position"] for f in films] == list(range(1, 251))
    assert all(f["title"] and f["year"] for f in films)
    assert len({f["letterboxd_url"] for f in films}) == 250
    assert all(f["letterboxd_url"].startswith("https://letterboxd.com/film/") for f in films)


def test_list_endpoint(client: TestClient, alice: Headers) -> None:
    r = client.get("/api/bottom250", headers=alice)
    assert r.status_code == 200
    body = r.json()
    assert len(body["films"]) == 250
    assert body["films"][0]["position"] == 1
    assert body["source"].startswith("https://letterboxd.com/")
    assert all(f["film_id"] is None and f["status"] is None for f in body["films"])


def test_requires_auth(client: TestClient) -> None:
    assert client.get("/api/bottom250").status_code == 401


def test_marks_films_the_club_already_has(client: TestClient, alice: Headers) -> None:
    first = client.get("/api/bottom250", headers=alice).json()["films"]
    one, two, three = first[0], first[1], first[2]
    # Added by hand: different capitalisation and punctuation, same year.
    watched = client.post(
        "/api/films",
        json={
            "title": one["title"].upper().replace(":", ""),
            "year": one["year"],
            "status": "watched",
        },
        headers=alice,
    ).json()
    # Added without a year: still matches on the title.
    planned = client.post("/api/films", json={"title": two["title"]}, headers=alice).json()
    # Same title but a different year is a different film.
    client.post(
        "/api/films", json={"title": three["title"], "year": three["year"] - 20}, headers=alice
    )

    films = {f["position"]: f for f in client.get("/api/bottom250", headers=alice).json()["films"]}
    assert films[1]["film_id"] == watched["id"] and films[1]["status"] == "watched"
    assert films[2]["film_id"] == planned["id"] and films[2]["status"] == "watchlist"
    assert films[3]["film_id"] is None
