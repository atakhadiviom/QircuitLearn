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
    if db_type == "postgres":
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASS", ""),
            dbname=os.getenv("DB_NAME", "qircuitlearn"),
            port=int(os.getenv("DB_PORT", "5432"))
        )
        conn.autocommit = True
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.close()
        return conn
    db_path = os.path.join(os.path.dirname(__file__), "../qircuit.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
