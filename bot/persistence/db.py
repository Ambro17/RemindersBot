import logging
import psycopg2

logger = logging.getLogger()


class PSQLDatabase(object):
    """PSQL Database class to ease querys, opening and closing"""

    def __init__(self, connection_string):
        self._conn = psycopg2.connect(connection_string)
        self._cursor = self._conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._conn.close()

    def query(self, query, *params):
        return self._cursor.execute(query, *params)

    def close(self):
        return self._conn.close()

    def commit(self):
        return self._conn.commit()

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()
