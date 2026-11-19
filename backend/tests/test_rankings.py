import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Film, FilmStatus, Rating, User

from .conftest import Headers

# Seed (badness, fun) per film, by Ann and Ben:
#   Alpha  Ann (10,2)  Ben (10,2)  -> bad 10, fun 2, combined 6   (2 ratings)
#   Bravo  Ann (8,9)   Ben (6,9)   -> bad 7,  fun 9, combined 8   (2 ratings)
#   Charlie Ann (7,5)              -> bad 7,  fun 5, combined 6   (1 rating)
#   Delta  Ben (3,3)               -> bad 3,  fun 3, combined 3   (1 rating)
#   Echo   watched, never rated    -> not ranked
#   Foxtrot on the watchlist       -> not ranked


@pytest.fixture()
def seeded(db: Session) -> None:
    ann = User(username="ann", display_name="Ann", password_hash="x")
    ben = User(username="ben", display_name="Ben", password_hash="x")
    db.add_all([ann, ben])
    db.flush()

    def film(title: str, status: FilmStatus = FilmStatus.watched) -> Film:
        f = Film(title=title, status=status, added_by=ann.id)
        db.add(f)
        db.flush()
        return f

    alpha, bravo, charlie, delta = (film(t) for t in ("Alpha", "Bravo", "Charlie", "Delta"))
    film("Echo")
    film("Foxtrot", FilmStatus.watchlist)

    for f, user, badness, fun in [
        (alpha, ann, 10, 2),
        (alpha, ben, 10, 2),
        (bravo, ann, 8, 9),
        (bravo, ben, 6, 9),
        (charlie, ann, 7, 5),
        (delta, ben, 3, 3),
    ]:
        db.add(Rating(film_id=f.id, user_id=user.id, badness=badness, fun=fun))
    db.flush()


def ranking(client: TestClient, headers: Headers, sort: str) -> list[tuple[int, str]]:
    r = client.get(f"/api/rankings?sort={sort}", headers=headers)
    assert r.status_code == 200
    return [(f["rank"], f["title"]) for f in r.json()]


def test_sort_by_badness_with_tie(client: TestClient, alice: Headers, seeded: None) -> None:
    # Bravo and Charlie tie on 7.0; more ratings first; the next rank skips to 4.
    assert ranking(client, alice, "badness") == [
        (1, "Alpha"),
        (2, "Bravo"),
        (2, "Charlie"),
        (4, "Delta"),
    ]


def test_sort_by_fun(client: TestClient, alice: Headers, seeded: None) -> None:
    assert ranking(client, alice, "fun") == [
        (1, "Bravo"),
        (2, "Charlie"),
        (3, "Delta"),
        (4, "Alpha"),
    ]


def test_sort_by_combined_with_tie(client: TestClient, alice: Headers, seeded: None) -> None:
    assert ranking(client, alice, "combined") == [
        (1, "Bravo"),
        (2, "Alpha"),
        (2, "Charlie"),
        (4, "Delta"),
    ]


def test_default_sort_is_combined(client: TestClient, alice: Headers, seeded: None) -> None:
    default = client.get("/api/rankings", headers=alice).json()
    assert [f["title"] for f in default][0] == "Bravo"


def test_ranking_row_contents(client: TestClient, alice: Headers, seeded: None) -> None:
    rows = client.get("/api/rankings?sort=badness", headers=alice).json()
    bravo = next(r for r in rows if r["title"] == "Bravo")
    assert bravo["avg_badness"] == 7.0
    assert bravo["avg_fun"] == 9.0
    assert bravo["avg_combined"] == 8.0
    assert bravo["rating_count"] == 2
    assert {(s["display_name"], s["badness"], s["fun"]) for s in bravo["scores"]} == {
        ("Ann", 8, 9),
        ("Ben", 6, 9),
    }


def test_unrated_and_watchlist_films_are_not_ranked(
    client: TestClient, alice: Headers, seeded: None
) -> None:
    titles = [t for _, t in ranking(client, alice, "badness")]
    assert "Echo" not in titles
    assert "Foxtrot" not in titles


def test_averages_are_rounded_to_two_decimals(client: TestClient, alice: Headers, db: Session):
    ann = User(username="ann", display_name="Ann", password_hash="x")
    db.add(ann)
    db.flush()
    f = Film(title="Thirds", status=FilmStatus.watched, added_by=ann.id)
    db.add(f)
    db.flush()
    for i, score in enumerate([1, 1, 2]):
        u = User(username=f"u{i}", display_name=f"U{i}", password_hash="x")
        db.add(u)
        db.flush()
        db.add(Rating(film_id=f.id, user_id=u.id, badness=score, fun=score))
    db.flush()
    row = client.get("/api/rankings?sort=badness", headers=alice).json()[0]
    assert row["avg_badness"] == 1.33


def test_empty_rankings(client: TestClient, alice: Headers) -> None:
    assert client.get("/api/rankings", headers=alice).json() == []


def test_invalid_sort_rejected(client: TestClient, alice: Headers) -> None:
    assert client.get("/api/rankings?sort=nope", headers=alice).status_code == 422


def test_rankings_end_to_end_through_the_api(
    client: TestClient, alice: Headers, bob: Headers
) -> None:
    ids = []
    for title in ("Good-Bad", "Bad-Bad"):
        r = client.post("/api/films", json={"title": title, "status": "watched"}, headers=alice)
        ids.append(r.json()["id"])
    for headers, (b1, f1, b2, f2) in [(alice, (9, 9, 5, 1)), (bob, (7, 9, 5, 3))]:
        client.put(f"/api/films/{ids[0]}/rating", json={"badness": b1, "fun": f1}, headers=headers)
        client.put(f"/api/films/{ids[1]}/rating", json={"badness": b2, "fun": f2}, headers=headers)
    assert ranking(client, alice, "badness") == [(1, "Good-Bad"), (2, "Bad-Bad")]
    assert ranking(client, alice, "fun") == [(1, "Good-Bad"), (2, "Bad-Bad")]


def test_rankings_require_auth(client: TestClient) -> None:
    assert client.get("/api/rankings").status_code == 401
    assert client.get("/api/stats").status_code == 401
    assert client.get("/api/export").status_code == 401


def test_stats(client: TestClient, alice: Headers, seeded: None) -> None:
    s = client.get("/api/stats", headers=alice).json()
    assert s["films_watched"] == 5
    assert s["films_on_watchlist"] == 1
    assert s["total_ratings"] == 6
    assert s["members"] == 3  # Ann, Ben and the logged-in alice
    # Ann: (10+8+7)/3 = 8.33, Ben: (10+6+3)/3 = 6.33
    assert s["harshest_critic"]["display_name"] == "Ann"
    assert s["harshest_critic"]["avg_badness"] == 8.33
    assert s["most_generous_critic"]["display_name"] == "Ben"
    assert s["worst_film"] == {"id": s["worst_film"]["id"], "title": "Alpha", "score": 10.0}
    assert s["most_fun_film"]["title"] == "Bravo"


def test_stats_on_empty_database(client: TestClient, alice: Headers) -> None:
    s = client.get("/api/stats", headers=alice).json()
    assert s["films_watched"] == 0
    assert s["harshest_critic"] is None
    assert s["worst_film"] is None


def test_export(client: TestClient, alice: Headers, seeded: None) -> None:
    r = client.get("/api/export", headers=alice)
    assert r.status_code == 200
    data = r.json()
    assert len(data["users"]) == 3
    assert len(data["films"]) == 6
    assert len(data["ratings"]) == 6
    assert "password" not in r.text
    assert "exported_at" in data
