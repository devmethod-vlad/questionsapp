"""Compatibility export for legacy DB object access.

Legacy handlers historically imported ``db`` directly from the ``database``
package. This module keeps the same object available from the native app
namespace and helps remove direct legacy imports from service modules.
"""

from database import db

__all__ = ["db"]

