"""Legacy import shim for ORM models.

Model definitions were migrated to :mod:`app.db.models` so active FastAPI
runtime code can depend on the native `app` namespace.
"""

from app.db.models import *  # noqa: F401,F403
