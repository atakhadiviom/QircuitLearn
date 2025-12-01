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
    ph = get_placeholder()
    db_type = os.getenv("DB_TYPE", "sqlite")

    try:
        if db_type == "postgres":
            query = f"""
                INSERT INTO progress (user_id, lesson_id, status, updated_at)
                VALUES ({ph}, {ph}, {ph}, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, lesson_id)
                DO UPDATE SET status = EXCLUDED.status, updated_at = CURRENT_TIMESTAMP
            """
            cur.execute(query, (user_id, lesson_id, status))
        elif db_type == "mysql":
            query = f"""
                INSERT INTO progress (user_id, lesson_id, status, updated_at)
                VALUES ({ph}, {ph}, {ph}, NOW())
                ON DUPLICATE KEY UPDATE status = VALUES(status), updated_at = NOW()
            """
            cur.execute(query, (user_id, lesson_id, status))
        else:
            # SQLite
            query = f"INSERT OR REPLACE INTO progress (user_id, lesson_id, status, updated_at) VALUES ({ph}, {ph}, {ph}, CURRENT_TIMESTAMP)"
            cur.execute(query, (user_id, lesson_id, status))
            
        if isinstance(conn, sqlite3.Connection):
            conn.commit()
    except Exception as e:
        print(f"Error upserting progress: {e}")
        raise e
    finally:
        cur.close()
        conn.close()

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

def get_quiz_by_id(quiz_id):
    conn = get_conn()
    cur = get_cursor(conn)
    ph = get_placeholder()
    cur.execute(f"SELECT * FROM quizzes WHERE id={ph}", (quiz_id,))
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

def submit_quiz_attempt(user_id, quiz_id, score, passed, answers_json=None):
    conn = get_conn()
    cur = get_cursor(conn)
    ph = get_placeholder()
    cur.execute(f"INSERT INTO user_quiz_attempts(user_id, quiz_id, score, passed, answers_json) VALUES({ph},{ph},{ph},{ph},{ph})", (user_id, quiz_id, score, passed, answers_json))
    if isinstance(conn, sqlite3.Connection):
        conn.commit()
    cur.close()
    conn.close()

def get_user_passed_quiz_attempt(user_id, quiz_id):
    conn = get_conn()
    cur = get_cursor(conn)
    ph = get_placeholder()
    # Check if passed is true. We use a parameter for portability.
    # SQLite uses 1/0, Postgres uses t/f, but the driver handles the python bool mapping.
    cur.execute(f"SELECT * FROM user_quiz_attempts WHERE user_id={ph} AND quiz_id={ph} AND passed={ph} ORDER BY attempted_at DESC LIMIT 1", (user_id, quiz_id, True))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

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

def upsert_forum_post(user_id, title, slug, meta_title, meta_description, content, post_id=None):
    conn = get_conn()
    cur = get_cursor(conn)
    ph = get_placeholder()
    if post_id:
        cur.execute(f"UPDATE forum_posts SET title={ph}, slug={ph}, meta_title={ph}, meta_description={ph}, content={ph} WHERE id={ph}", (title, slug, meta_title, meta_description, content, post_id))
    else:
        cur.execute(f"INSERT INTO forum_posts(user_id, title, slug, meta_title, meta_description, content) VALUES({ph},{ph},{ph},{ph},{ph},{ph})", (user_id, title, slug, meta_title, meta_description, content))
    if isinstance(conn, sqlite3.Connection):
        conn.commit()
    cur.close()
    conn.close()

def get_forum_post_by_slug(slug):
    conn = get_conn()
    cur = get_cursor(conn)
    ph = get_placeholder()
    cur.execute(f"SELECT p.*, u.username FROM forum_posts p JOIN users u ON p.user_id = u.id WHERE slug={ph}", (slug,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

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

def search_lessons(term):
    conn = get_conn()
    cur = get_cursor(conn)
    ph = get_placeholder()
    tlike = f"%{term}%"
    # Search by title or content; limit to reasonable number
    cur.execute(
        f"SELECT lessons.*, courses.title AS course_title, courses.slug AS course_slug "
        f"FROM lessons JOIN courses ON lessons.course_id = courses.id "
        f"WHERE lessons.title LIKE {ph} OR lessons.content LIKE {ph} "
        f"ORDER BY lessons.position LIMIT 50",
        (tlike, tlike)
    )
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
