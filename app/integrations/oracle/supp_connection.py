import cx_Oracle

from app.core.settings import get_settings

SETTINGS = get_settings()

dsn = cx_Oracle.makedsn(
    host=SETTINGS.etd2_db_host,
    port=SETTINGS.etd2_db_port,
    service_name=SETTINGS.etd2_db_servicename,
)
