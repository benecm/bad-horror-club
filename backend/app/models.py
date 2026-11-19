import enum
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class FilmStatus(enum.StrEnum):
    watchlist = "watchlist"
    watched = "watched"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    display_name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Film(Base):
    __tablename__ = "films"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    year: Mapped[int | None] = mapped_column(Integer)
    poster_url: Mapped[str | None] = mapped_column(String(500))
    tmdb_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    status: Mapped[FilmStatus] = mapped_column(
        Enum(FilmStatus, name="film_status"), default=FilmStatus.watchlist
    )
    watched_on: Mapped[date | None] = mapped_column(Date)
    added_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ratings: Mapped[list["Rating"]] = relationship(
        back_populates="film", cascade="all, delete-orphan", passive_deletes=True
    )
    quotes: Mapped[list["Quote"]] = relationship(
        back_populates="film", cascade="all, delete-orphan", passive_deletes=True
    )
    votes: Mapped[list["Vote"]] = relationship(
        back_populates="film", cascade="all, delete-orphan", passive_deletes=True
    )


class Rating(Base):
    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint("film_id", "user_id", name="uq_rating_film_user"),
        CheckConstraint("badness BETWEEN 1 AND 10", name="ck_rating_badness"),
        CheckConstraint("fun BETWEEN 1 AND 10", name="ck_rating_fun"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    film_id: Mapped[int] = mapped_column(ForeignKey("films.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    badness: Mapped[int] = mapped_column(Integer)
    fun: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    film: Mapped[Film] = relationship(back_populates="ratings")
    user: Mapped[User] = relationship()


class Quote(Base):
    """A best line from the movie night."""

    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(primary_key=True)
    film_id: Mapped[int] = mapped_column(ForeignKey("films.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    film: Mapped[Film] = relationship(back_populates="quotes")
    user: Mapped[User] = relationship()


class Vote(Base):
    """A vote for which watchlist film to watch next. One per person per film."""

    __tablename__ = "votes"
    __table_args__ = (UniqueConstraint("film_id", "user_id", name="uq_vote_film_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    film_id: Mapped[int] = mapped_column(ForeignKey("films.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    film: Mapped[Film] = relationship(back_populates="votes")
