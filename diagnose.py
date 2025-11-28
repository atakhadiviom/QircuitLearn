import os
import sys
import json

def _safe_row_get(row, key, index=0):
    try:
        return row[key]
    except Exception:
        try:
            return row[index]
        except Exception:
            return None

def main():
    info = {}
    info["cwd"] = os.getcwd()
    info["exe"] = sys.executable
    info["version"] = sys.version
    info["pythonpath"] = os.getenv("PYTHONPATH", "")
    info["env"] = {
        "DB_TYPE": os.getenv("DB_TYPE", ""),
        "DB_HOST": os.getenv("DB_HOST", ""),
        "DB_NAME": os.getenv("DB_NAME", ""),
        "DB_USER": os.getenv("DB_USER", ""),
        "DB_PORT": os.getenv("DB_PORT", ""),
    }
    try:
        from app import create_app
        app = create_app()
        rules = []
        for r in app.url_map.iter_rules():
            rules.append(str(r))
        info["routes"] = rules
    except Exception as e:
        info["routes_error"] = str(e)
    try:
        from app.db import get_conn
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM courses")
        c = cur.fetchone()
        count_courses = _safe_row_get(c, 0, 0)
        cur.execute("SELECT slug FROM courses ORDER BY created_at LIMIT 1")
        r = cur.fetchone()
        first_slug = _safe_row_get(r, "slug", 0)
        info["db"] = {"courses_count": count_courses, "first_course_slug": first_slug}
        cur.close()
        conn.close()
    except Exception as e:
        info["db_error"] = str(e)
    print(json.dumps(info, indent=2))

if __name__ == "__main__":
    main()

