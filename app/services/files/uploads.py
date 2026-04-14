"""Native upload abstraction for FastAPI file flows.

The legacy business logic only needs a small, explicit API surface for uploads.
This module provides that contract so save flows do not depend on Flask/Werkzeug
file semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Protocol

from fastapi import UploadFile


class UploadLike(Protocol):
    """Minimal upload contract required by question write business logic."""

    @property
    def filename(self) -> str | None:
        """Original uploaded file name."""

    @property
    def size_bytes(self) -> int:
        """File size in bytes."""

    def save_to(self, dst: str | Path) -> None:
        """Persist upload to an absolute or relative destination path."""


@dataclass(slots=True)
class AppUpload:
    """Application-level wrapper around FastAPI uploads.

    Attributes:
        source: Incoming FastAPI upload object.
    """

    source: UploadFile

    @property
    def filename(self) -> str | None:
        return self.source.filename

    @property
    def size_bytes(self) -> int:
        stream: BinaryIO = self.source.file
        current_offset = stream.tell()
        stream.seek(0, 2)
        size = stream.tell()
        stream.seek(current_offset)
        return int(size)

    def save_to(self, dst: str | Path) -> None:
        path = Path(dst)
        path.parent.mkdir(parents=True, exist_ok=True)
        stream: BinaryIO = self.source.file
        stream.seek(0)
        path.write_bytes(stream.read())
