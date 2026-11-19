from collections.abc import Iterator

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from alembic import command
from app.config import get_settings
from app.db import get_db
from app.main import app

TEST_URL = get_settings().test_database_url


@pytest.fixture(scope="session")
def engine():
    """Test database, built from the real Alembic migrations."""
    eng = create_engine(TEST_URL)
    with eng.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", TEST_URL.replace("%", "%%"))
    command.upgrade(cfg, "head")
    yield eng
    eng.dispose()


@pytest.fixture()
def db(engine) -> Iterator[Session]:
    """Each test runs in a transaction that is rolled back afterwards."""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(
        bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


Headers = dict[str, str]


def make_user(client: TestClient, username: str) -> Headers:
    """Register + log in; returns Authorization headers."""
    r = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "display_name": username.title(),
            "password": "correct-horse",
            "join_code": get_settings().join_code,
        },
    )
    assert r.status_code == 201, r.text
    r = client.post("/api/auth/login", json={"username": username, "password": "correct-horse"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def alice(client: TestClient) -> Headers:
    return make_user(client, "alice")


@pytest.fixture()
def bob(client: TestClient) -> Headers:
    return make_user(client, "bob")


@pytest.fixture()
def client(db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
