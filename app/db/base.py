"""Declarative base and legacy-style query support for ORM models."""

from sqlalchemy.orm import declarative_base

from app.db.engine import SessionFactory

Base = declarative_base()
Base.query = SessionFactory.query_property()

__all__ = ["Base"]
