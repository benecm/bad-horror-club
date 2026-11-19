import jwt
from fastapi.testclient import TestClient

from app.config import get_settings

from .conftest import make_user

REGISTER = {
    "username": "Carol",
    "display_name": "Carol",
    "password": "correct-horse",
}


def test_register_login_me(client: TestClient) -> None:
    code = get_settings().join_code
    r = client.post("/api/auth/register", json={**REGISTER, "join_code": code})
    assert r.status_code == 201
    assert r.json()["username"] == "carol"  # normalized to lowercase
    assert "password" not in r.text

    r = client.post("/api/auth/login", json={"username": "CAROL", "password": "correct-horse"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["display_name"] == "Carol"


def test_register_wrong_join_code(client: TestClient) -> None:
    r = client.post("/api/auth/register", json={**REGISTER, "join_code": "nope"})
    assert r.status_code == 403
    assert (
        client.post(
            "/api/auth/login", json={"username": "carol", "password": "correct-horse"}
        ).status_code
        == 401
    )  # no account was created


def test_register_duplicate_username(client: TestClient) -> None:
    code = get_settings().join_code
    assert (
        client.post("/api/auth/register", json={**REGISTER, "join_code": code}).status_code == 201
    )
    r = client.post("/api/auth/register", json={**REGISTER, "username": "CAROL", "join_code": code})
    assert r.status_code == 409


def test_register_validation(client: TestClient) -> None:
    code = get_settings().join_code
    r = client.post("/api/auth/register", json={**REGISTER, "password": "short", "join_code": code})
    assert r.status_code == 422
    r = client.post("/api/auth/register", json={**REGISTER, "username": "a b!", "join_code": code})
    assert r.status_code == 422


def test_login_wrong_password_and_unknown_user(client: TestClient) -> None:
    make_user(client, "dave")
    r = client.post("/api/auth/login", json={"username": "dave", "password": "wrong-password"})
    assert r.status_code == 401
    r = client.post("/api/auth/login", json={"username": "ghost", "password": "correct-horse"})
    assert r.status_code == 401


def test_protected_routes_need_a_valid_token(client: TestClient) -> None:
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/films").status_code == 401
    bad = {"Authorization": "Bearer not-a-jwt"}
    assert client.get("/api/auth/me", headers=bad).status_code == 401


def test_token_signed_with_other_secret_is_rejected(client: TestClient) -> None:
    make_user(client, "erin")
    forged = jwt.encode({"sub": "1"}, "some-other-secret-that-is-long-enough!", "HS256")
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401
