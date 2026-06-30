import os

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor


load_dotenv()


class PostgreSQLConnection:
    """Small compatibility layer for the cursors used by the existing app."""

    def __init__(self, connection):
        self._connection = connection

    def cursor(self, dictionary=False):
        factory = RealDictCursor if dictionary else None
        return self._connection.cursor(cursor_factory=factory)

    def commit(self):
        return self._connection.commit()

    def rollback(self):
        return self._connection.rollback()

    def close(self):
        return self._connection.close()


def conectar():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL no esta configurada. Copia .env.example a .env y agrega la URL de Neon."
        )

    connection = psycopg2.connect(database_url, connect_timeout=10)
    return PostgreSQLConnection(connection)
