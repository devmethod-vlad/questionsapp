import cx_Oracle
from flask import current_app as app

dsn = cx_Oracle.makedsn(host=app.config['SUPP_DB_HOST'], port=app.config['SUPP_DB_PORT'], sid=app.config['SUPP_DB_SID'])