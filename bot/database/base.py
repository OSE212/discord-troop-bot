from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


def make_engine(database_url: str, *, echo: bool = False):
    connect_args = {}
    if database_url.startswith("sqlite"):
        # Needed so the same SQLite connection can be used across the
        # async Discord event loop's worker threads.
        connect_args = {"check_same_thread": False}
    return create_engine(database_url, echo=echo, connect_args=connect_args)


class Database:
    """Thin wrapper bundling an engine + session factory together.

    A single instance of this is created at bot startup (see run.py)
    and handed to repositories/services via dependency injection, which
    keeps tests free of global state.
    """

    def __init__(self, database_url: str, *, echo: bool = False):
        self.engine = make_engine(database_url, echo=echo)
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    def create_all(self) -> None:
        Base.metadata.create_all(bind=self.engine)
        # Safe automatic column migration for existing databases
        try:
            from sqlalchemy import text
            with self.engine.connect() as conn:
                conn.execute(text("ALTER TABLE players ADD COLUMN guild_id VARCHAR(32)"))
                conn.commit()
        except Exception:
            # Column already exists or table freshly created with it
            pass


    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
