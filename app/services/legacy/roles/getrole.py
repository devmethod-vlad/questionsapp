"""Role lookup helpers preserved for legacy-compatible payload generation."""

from __future__ import annotations

from app.core.runtime_config import get_base_roles

def get_role(roleid):
    base_roles = get_base_roles()
    for item in base_roles:
        if base_roles[item]["id"] == int(roleid):
            return item
    return None
