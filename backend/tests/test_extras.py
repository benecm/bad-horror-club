from fastapi.testclient import TestClient

from .conftest import Headers


def add_film(client: TestClient, headers: Headers, status: str) -> int:
    r = client.post("/api/films", json={"title": "Troll 2", "status": status}, headers=headers)
    return r.json()["id"]


# ---- quotes ----
def test_add_and_list_quotes(client: TestClient, alice: Headers, bob: Headers) -> None:
    film_id = add_film(client, alice, "watched")
    r = client.post(
        f"/api/films/{film_id}/quotes",
        json={"text": "  They're eating her... and then  "},
        headers=bob,
    )
    assert r.status_code == 201
    assert r.json()["text"] == "They're eating her... and then"
    assert r.json()["user"]["username"] == "bob"

    client.post(f"/api/films/{film_id}/quotes", json={"text": "Oh my God!"}, headers=alice)
    detail = client.get(f"/api/films/{film_id}", headers=alice).json()
    assert [q["text"] for q in detail["quotes"]] == [
        "They're eating her... and then",
        "Oh my God!",
    ]


def test_quote_validation(client: TestClient, alice: Headers) -> None:
    film_id = add_film(client, alice, "watched")
    url = f"/api/films/{film_id}/quotes"
    assert client.post(url, json={"text": "   "}, headers=alice).status_code == 422
    assert client.post(url, json={"text": "x" * 501}, headers=alice).status_code == 422


def test_cannot_quote_a_watchlist_film(client: TestClient, alice: Headers) -> None:
    film_id = add_film(client, alice, "watchlist")
    r = client.post(f"/api/films/{film_id}/quotes", json={"text": "hi"}, headers=alice)
    assert r.status_code == 409


def test_quote_on_missing_film(client: TestClient, alice: Headers) -> None:
    assert (
        client.post("/api/films/9999/quotes", json={"text": "hi"}, headers=alice).status_code == 404
    )


def test_only_author_can_delete_a_quote(client: TestClient, alice: Headers, bob: Headers) -> None:
    film_id = add_film(client, alice, "watched")
    quote_id = client.post(
        f"/api/films/{film_id}/quotes", json={"text": "Goblins!"}, headers=alice
    ).json()["id"]
    assert client.delete(f"/api/quotes/{quote_id}", headers=bob).status_code == 403
    assert client.delete(f"/api/quotes/{quote_id}", headers=alice).status_code == 204
    assert client.delete(f"/api/quotes/{quote_id}", headers=alice).status_code == 404
    assert client.get(f"/api/films/{film_id}", headers=alice).json()["quotes"] == []


def test_deleting_a_film_removes_its_quotes_and_votes(
    client: TestClient, alice: Headers, bob: Headers
) -> None:
    watched = add_film(client, alice, "watched")
    client.post(f"/api/films/{watched}/quotes", json={"text": "x"}, headers=bob)
    planned = add_film(client, alice, "watchlist")
    client.put(f"/api/films/{planned}/vote", headers=bob)
    assert client.delete(f"/api/films/{watched}", headers=alice).status_code == 204
    assert client.delete(f"/api/films/{planned}", headers=alice).status_code == 204


# ---- votes ----
def test_vote_and_unvote(client: TestClient, alice: Headers, bob: Headers) -> None:
    film_id = add_film(client, alice, "watchlist")
    assert client.put(f"/api/films/{film_id}/vote", headers=alice).status_code == 204
    assert client.put(f"/api/films/{film_id}/vote", headers=bob).status_code == 204

    films = client.get("/api/films?status=watchlist", headers=alice).json()
    me = client.get("/api/auth/me", headers=alice).json()["id"]
    assert len(films[0]["vote_user_ids"]) == 2
    assert me in films[0]["vote_user_ids"]

    assert client.delete(f"/api/films/{film_id}/vote", headers=alice).status_code == 204
    detail = client.get(f"/api/films/{film_id}", headers=alice).json()
    assert me not in detail["vote_user_ids"]
    assert len(detail["vote_user_ids"]) == 1


def test_voting_twice_counts_once(client: TestClient, alice: Headers) -> None:
    film_id = add_film(client, alice, "watchlist")
    assert client.put(f"/api/films/{film_id}/vote", headers=alice).status_code == 204
    assert client.put(f"/api/films/{film_id}/vote", headers=alice).status_code == 204
    assert len(client.get(f"/api/films/{film_id}", headers=alice).json()["vote_user_ids"]) == 1


def test_removing_a_vote_you_never_cast_is_fine(client: TestClient, alice: Headers) -> None:
    film_id = add_film(client, alice, "watchlist")
    assert client.delete(f"/api/films/{film_id}/vote", headers=alice).status_code == 204


def test_cannot_vote_for_a_watched_film(client: TestClient, alice: Headers) -> None:
    film_id = add_film(client, alice, "watched")
    assert client.put(f"/api/films/{film_id}/vote", headers=alice).status_code == 409


def test_vote_missing_film_and_auth(client: TestClient, alice: Headers) -> None:
    assert client.put("/api/films/9999/vote", headers=alice).status_code == 404
    assert client.put("/api/films/1/vote").status_code == 401
    assert client.post("/api/films/1/quotes", json={"text": "x"}).status_code == 401
