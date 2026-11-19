import pytest
from fastapi.testclient import TestClient

from .conftest import Headers


@pytest.fixture()
def watched_id(client: TestClient, alice: Headers) -> int:
    r = client.post("/api/films", json={"title": "Troll 2", "status": "watched"}, headers=alice)
    return r.json()["id"]


def rate(client: TestClient, headers: Headers, film_id: int, **body: object):
    return client.put(
        f"/api/films/{film_id}/rating",
        json={"badness": 8, "fun": 9, **body},
        headers=headers,
    )


def test_create_rating(client: TestClient, alice: Headers, watched_id: int) -> None:
    r = rate(client, alice, watched_id, comment="Oh my god, goblins")
    assert r.status_code == 200
    body = r.json()
    assert (body["badness"], body["fun"]) == (8, 9)
    assert body["user"]["username"] == "alice"

    detail = client.get(f"/api/films/{watched_id}", headers=alice).json()
    assert detail["rating_count"] == 1
    assert detail["ratings"][0]["comment"] == "Oh my god, goblins"


def test_rating_twice_updates_instead_of_duplicating(
    client: TestClient, alice: Headers, watched_id: int
) -> None:
    first = rate(client, alice, watched_id, badness=3, fun=3).json()
    second = rate(client, alice, watched_id, badness=10, fun=1, comment="changed my mind").json()
    assert second["id"] == first["id"]
    detail = client.get(f"/api/films/{watched_id}", headers=alice).json()
    assert detail["rating_count"] == 1
    assert (detail["ratings"][0]["badness"], detail["ratings"][0]["fun"]) == (10, 1)


def test_each_user_has_their_own_rating(
    client: TestClient, alice: Headers, bob: Headers, watched_id: int
) -> None:
    rate(client, alice, watched_id, badness=2)
    rate(client, bob, watched_id, badness=9)
    detail = client.get(f"/api/films/{watched_id}", headers=alice).json()
    assert sorted(r["badness"] for r in detail["ratings"]) == [2, 9]


@pytest.mark.parametrize("field", ["badness", "fun"])
@pytest.mark.parametrize("value", [0, 11, -1])
def test_scores_must_be_1_to_10(
    client: TestClient, alice: Headers, watched_id: int, field: str, value: int
) -> None:
    assert rate(client, alice, watched_id, **{field: value}).status_code == 422


def test_cannot_rate_a_watchlist_film(client: TestClient, alice: Headers) -> None:
    film = client.post("/api/films", json={"title": "Not yet"}, headers=alice).json()
    assert rate(client, alice, film["id"]).status_code == 409


def test_rate_missing_film(client: TestClient, alice: Headers) -> None:
    assert rate(client, alice, 999999).status_code == 404


def test_rating_requires_auth(client: TestClient, watched_id: int) -> None:
    r = client.put(f"/api/films/{watched_id}/rating", json={"badness": 5, "fun": 5})
    assert r.status_code == 401


def test_delete_own_rating_only(
    client: TestClient, alice: Headers, bob: Headers, watched_id: int
) -> None:
    rate(client, alice, watched_id)
    # bob hasn't rated, so he has nothing to delete (and can't touch alice's)
    assert client.delete(f"/api/films/{watched_id}/rating", headers=bob).status_code == 404
    assert client.delete(f"/api/films/{watched_id}/rating", headers=alice).status_code == 204
    assert client.get(f"/api/films/{watched_id}", headers=alice).json()["rating_count"] == 0
    assert client.delete(f"/api/films/{watched_id}/rating", headers=alice).status_code == 404
