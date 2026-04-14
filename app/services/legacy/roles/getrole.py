"""Role lookup helpers preserved for legacy-compatible payload generation."""

from __future__ import annotations

from app.core.constants import BASE_ROLE

def get_role(roleid):
    base_roles = BASE_ROLE
    for item in base_roles:
        if base_roles[item]["id"] == int(roleid):
            return item
    return None
