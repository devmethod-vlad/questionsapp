"""External integrations gateways."""

from .confluence_gateway import ConfluenceGateway
from .telegram_gateway import TelegramGateway

__all__ = ["ConfluenceGateway", "TelegramGateway"]
