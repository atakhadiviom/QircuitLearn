from .db import get_conn
import os
import sqlite3
try:
    from psycopg2.extras import RealDictCursor
except Exception:
    RealDictCursor = None

def get_placeholder():
    t = os.getenv("DB_TYPE", "sqlite")
    return "%s" if t in ("mysql", "postgres") else "?"

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

def get_cursor(conn):
    t = os.getenv("DB_TYPE", "sqlite")
    if isinstance(conn, sqlite3.Connection):
        return conn.cursor()
    if t == "postgres" and RealDictCursor is not None:
        return conn.cursor(cursor_factory=RealDictCursor)
    return conn.cursor()

def create_tables(schema_sql_path):
    conn = get_conn()
    with open(schema_sql_path, "r") as f:
        execute_script(conn, f.read())
    conn.close()

def upsert_progress(user_id, lesson_id, status):
    conn = get_conn()
    cur = get_cursor(conn)

from werkzeug.security import generate_password_hash, check_password_hash

def create_user(username, email, password, is_superuser=False):
    conn = get_conn()
    cur = get_cursor(conn)
    ph = get_placeholder()
    pwd_hash = generate_password_hash(password, method='pbkdf2:sha256')
    try:
        # Simple check for DB type to handle RETURNING vs lastrowid
        if os.getenv("DB_TYPE", "sqlite") == "postgres":
            cur.execute(f"INSERT INTO users(username, email, password_hash, is_superuser) VALUES({ph},{ph},{ph},{ph}) RETURNING id", (username, email, pwd_hash, is_superuser))
            row = cur.fetchone()
            user_id = row['id'] if row else None
        else:
            cur.execute(f"INSERT INTO users(username, email, password_hash, is_superuser) VALUES({ph},{ph},{ph},{ph})", (username, email, pwd_hash, is_superuser))
            user_id = cur.lastrowid
        
        if isinstance(conn, sqlite3.Connection):
            conn.commit()
        cur.close()
        conn.close()
        return user_id
    except Exception as e:
        print(f"Error creating user: {e}")
        if cur: cur.close()
        if conn: conn.close()
        return None

def get_user_by_email(email):
    conn = get_conn()
    cur = get_cursor(conn)
    ph = get_placeholder()
    cur.execute(f"SELECT * FROM users WHERE email={ph}", (email,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def get_user_by_id(user_id):
    conn = get_conn()
    cur = get_cursor(conn)
    ph = get_placeholder()
    cur.execute(f"SELECT * FROM users WHERE id={ph}", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def get_quiz_for_lesson(lesson_id):
    conn = get_conn()
    cur = get_cursor(conn)
    ph = get_placeholder()
    cur.execute(f"SELECT * FROM quizzes WHERE lesson_id={ph}", (lesson_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def get_quiz_questions(quiz_id):
    conn = get_conn()
    cur = get_cursor(conn)
    ph = get_placeholder()
    cur.execute(f"SELECT * FROM quiz_questions WHERE quiz_id={ph}", (quiz_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def submit_quiz_attempt(user_id, quiz_id, score, passed):
    conn = get_conn()
    cur = get_cursor(conn)
    ph = get_placeholder()
    cur.execute(f"INSERT INTO user_quiz_attempts(user_id, quiz_id, score, passed) VALUES({ph},{ph},{ph},{ph})", (user_id, quiz_id, score, passed))
    if isinstance(conn, sqlite3.Connection):
        conn.commit()
    cur.close()
    conn.close()

def get_forum_posts():
    conn = get_conn()
    cur = get_cursor(conn)
    cur.execute("SELECT p.*, u.username FROM forum_posts p JOIN users u ON p.user_id = u.id ORDER BY p.created_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def create_forum_post(user_id, title, content):
    conn = get_conn()
    cur = get_cursor(conn)
    ph = get_placeholder()
    cur.execute(f"INSERT INTO forum_posts(user_id, title, content) VALUES({ph},{ph},{ph})", (user_id, title, content))
    if isinstance(conn, sqlite3.Connection):
        conn.commit()
    cur.close()
    conn.close()

def get_forum_post(post_id):
    conn = get_conn()
    cur = get_cursor(conn)
    ph = get_placeholder()
    cur.execute(f"SELECT * FROM forum_posts WHERE id={ph}", (post_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def update_forum_post(post_id, title, content):
    conn = get_conn()
    cur = get_cursor(conn)
    ph = get_placeholder()
    cur.execute(f"UPDATE forum_posts SET title={ph}, content={ph} WHERE id={ph}", (title, content, post_id))
    if isinstance(conn, sqlite3.Connection):
        conn.commit()
    cur.close()
    conn.close()

def delete_forum_post(post_id):
    conn = get_conn()
    cur = get_cursor(conn)
    ph = get_placeholder()
    cur.execute(f"DELETE FROM forum_posts WHERE id={ph}", (post_id,))
    if isinstance(conn, sqlite3.Connection):
        conn.commit()
    cur.close()
    conn.close()

def get_courses():
    conn = get_conn()
    cur = get_cursor(conn)
    cur.execute("SELECT * FROM courses ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_user_progress(user_id):
    conn = get_conn()
    cur = get_cursor(conn)
    ph = get_placeholder()
    cur.execute(f"SELECT lesson_id, status FROM progress WHERE user_id={ph}", (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {row['lesson_id']: row['status'] for row in rows} if rows else {}

def get_course_by_slug(slug):
    conn = get_conn()
    cur = get_cursor(conn)
    ph = get_placeholder()
    cur.execute(f"SELECT * FROM courses WHERE slug={ph}", (slug,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def get_lessons(course_id):
    conn = get_conn()
    cur = get_cursor(conn)
    ph = get_placeholder()
    cur.execute(f"SELECT * FROM lessons WHERE course_id={ph} ORDER BY position", (course_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_lesson_by_slug(course_id, slug):
    conn = get_conn()
    cur = get_cursor(conn)
    ph = get_placeholder()
    cur.execute(f"SELECT * FROM lessons WHERE course_id={ph} AND slug={ph}", (course_id, slug))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def save_circuit(user_id, name, data):
    conn = get_conn()
    cur = get_cursor(conn)
    ph = get_placeholder()
    cur.execute(
        f"INSERT INTO circuits(user_id, name, data) VALUES({ph},{ph},{ph})",
        (user_id, name, data)
    )
    if isinstance(conn, sqlite3.Connection):
        conn.commit()
    cur.close()
    conn.close()
