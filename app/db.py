import sqlite3
import os

def get_conn():
    db_type = os.getenv("DB_TYPE", "sqlite")
    
    if db_type == "mysql":
        import pymysql
        return pymysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASS", ""),
            database=os.getenv("DB_NAME", "qircuitlearn"),
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
    else:
        # SQLite fallback for local dev
        db_path = os.path.join(os.path.dirname(__file__), "../qircuit.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        return conn
