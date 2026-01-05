"""Database module for Content Intelligence System."""

from .schema import init_db, get_connection, DB_PATH

__all__ = ["init_db", "get_connection", "DB_PATH"]
