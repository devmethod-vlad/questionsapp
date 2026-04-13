import cx_Oracle
from flask import current_app as app

dsn = cx_Oracle.makedsn(host=app.config['ETD2_DB_HOST'], port=app.config['ETD2_DB_PORT'], service_name=app.config['ETD2_DB_SERVICENAME'])