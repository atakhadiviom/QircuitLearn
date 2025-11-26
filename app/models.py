from .db import get_conn
import os
import sqlite3

def get_placeholder():
    return "?" if os.getenv("DB_TYPE", "sqlite") != "mysql" else "%s"

def execute_script(conn, script):
    if isinstance(conn, sqlite3.Connection):
        conn.executescript(script)
    else:
        # MySQL doesn't support executescript, need to split by ; or use specific method
        # For simplicity, assuming the schema file has individual statements or we split manually
        # But MySQL cursor.execute usually handles multiple statements if enabled, but let's be safe:
        cur = conn.cursor()
        statements = script.split(';')
        for stmt in statements:
            if stmt.strip():
                cur.execute(stmt)
        cur.close()

def create_tables(schema_sql_path):
    conn = get_conn()
    with open(schema_sql_path, "r") as f:
        execute_script(conn, f.read())
    conn.close()

def upsert_progress(user_id, lesson_id, status):
    conn = get_conn()
    cur = conn.cursor()
    ph = get_placeholder()
    
    if os.getenv("DB_TYPE", "sqlite") == "mysql":
        query = f"INSERT INTO progress(user_id, lesson_id, status) VALUES({ph},{ph},{ph}) ON DUPLICATE KEY UPDATE status=VALUES(status)"
    else:
        # SQLite
        query = f"INSERT INTO progress(user_id, lesson_id, status) VALUES({ph},{ph},{ph}) ON CONFLICT(user_id, lesson_id) DO UPDATE SET status=excluded.status"
        
    cur.execute(query, (user_id, lesson_id, status))
    # Commit is autocommit for MySQL in db.py, but for SQLite?
    if isinstance(conn, sqlite3.Connection):
        conn.commit()
    cur.close()
    conn.close()

def get_courses():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM courses ORDER BY created_at")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_course_by_slug(slug):
    conn = get_conn()
    cur = conn.cursor()
    ph = get_placeholder()
    cur.execute(f"SELECT * FROM courses WHERE slug={ph}", (slug,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def get_lessons(course_id):
    conn = get_conn()
    cur = conn.cursor()
    ph = get_placeholder()
    cur.execute(f"SELECT * FROM lessons WHERE course_id={ph} ORDER BY position", (course_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_lesson_by_slug(course_id, slug):
    conn = get_conn()
    cur = conn.cursor()
    ph = get_placeholder()
    cur.execute(f"SELECT * FROM lessons WHERE course_id={ph} AND slug={ph}", (course_id, slug))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def save_circuit(user_id, name, data):
    conn = get_conn()
    cur = conn.cursor()
    ph = get_placeholder()
    cur.execute(
        f"INSERT INTO circuits(user_id, name, data) VALUES({ph},{ph},{ph})",
        (user_id, name, data)
    )
    if isinstance(conn, sqlite3.Connection):
        conn.commit()
    cur.close()
    conn.close()
