from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("PG_CONTAINER", "localhost")
os.environ.setdefault("PG_BASE", "test")
os.environ.setdefault("QUESTIONS_ATTACHMENTS", "/tmp")
