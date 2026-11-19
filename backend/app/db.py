from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


# pool_pre_ping: Neon suspends idle computes, so connections can go stale.
# prepare_threshold=None: no server-side prepared statements, which keeps psycopg safe
# behind Neon's PgBouncer pooler.
engine = create_engine(
    get_settings().database_url,
    pool_pre_ping=True,
    connect_args={"prepare_threshold": None},
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
