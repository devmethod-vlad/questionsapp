from functools import lru_cache

import oracledb

from app.core.settings import get_settings

SETTINGS = get_settings()


@lru_cache(maxsize=1)
def initialize_oracle_driver() -> None:
    try:
        oracledb.init_oracle_client()
    except Exception:
        # Fallback to thin mode when Oracle Client libraries are unavailable
        # or the driver is already initialized.
        pass


dsn = oracledb.makedsn(
    host=SETTINGS.etd2_db_host,
    port=SETTINGS.etd2_db_port,
    service_name=SETTINGS.etd2_db_servicename,
)
