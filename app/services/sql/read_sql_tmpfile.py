"""Dataframe loader for heavy SQL reads via PostgreSQL COPY."""

from __future__ import annotations

import tempfile

import pandas as pd


def read_sql_tmpfile(query: str, db_engine):
    """Execute SQL using `COPY ... TO STDOUT` and return DataFrame."""

    with tempfile.TemporaryFile() as tmpfile:
        copy_sql = f"COPY ({query}) TO STDOUT WITH CSV HEADER"
        conn = db_engine.raw_connection()
        cur = conn.cursor()
        cur.copy_expert(copy_sql, tmpfile)
        tmpfile.seek(0)
        return pd.read_csv(tmpfile)
