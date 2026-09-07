"""Database layer: SQLAlchemy models + repositories.

Nothing outside this package should import sqlalchemy directly for
player data access -- go through bot.database.repositories instead.
That keeps the optimizer and Discord layers persistence-agnostic and
makes a future SQLite -> PostgreSQL migration a one-line change to
DATABASE_URL.
"""
