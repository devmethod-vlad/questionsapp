import cx_Oracle

from app.core.runtime_config import get_config_value

dsn = cx_Oracle.makedsn(
    host=get_config_value('ETD2_DB_HOST'),
    port=get_config_value('ETD2_DB_PORT'),
    service_name=get_config_value('ETD2_DB_SERVICENAME'),
)
