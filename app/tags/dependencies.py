from core.database import engine


def get_connection():
    """Получение подключения к базе данных."""
    conn = engine.connect()
    try:
        yield conn
    finally:
        conn.close()