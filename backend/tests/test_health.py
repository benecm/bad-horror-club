from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.orm import Session


def test_health(client: TestClient) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_migrations_created_tables(db: Session) -> None:
    tables = set(inspect(db.connection()).get_table_names())
    assert {"users", "films", "ratings"} <= tables
