
import os
import sqlite3
from app.models import upsert_progress, get_user_progress, get_courses, get_lessons, create_user, get_user_by_email

# Setup context
os.environ["DB_TYPE"] = "sqlite"

# 1. Setup User and Data
email = "debug_types@example.com"
user = get_user_by_email(email)
if not user:
    user_id = create_user("debug_types", email, "password")
else:
    user_id = user['id'] if isinstance(user, dict) else user[0]

courses = get_courses()
if not courses:
    print("No courses found.")
    exit(1)
course_id = courses[0]['id'] if isinstance(courses[0], dict) else courses[0][0]

lessons = get_lessons(course_id)
if not lessons:
    print("No lessons found.")
    exit(1)
    
lesson = lessons[0]
# Handle row access
lesson_id = lesson['id'] if isinstance(lesson, dict) or hasattr(lesson, 'keys') else lesson[0]

print(f"User ID: {user_id} (Type: {type(user_id)})")
print(f"Lesson ID: {lesson_id} (Type: {type(lesson_id)})")

# 2. Insert Progress with Integer ID
print("\n--- Test 1: Insert with Integer ID ---")
upsert_progress(user_id, lesson_id, "completed")
progress = get_user_progress(user_id)
print(f"Progress Keys: {list(progress.keys())}")
print(f"Key Type: {[type(k) for k in progress.keys()]}")

if lesson_id in progress:
    print("Match found with integer key.")
else:
    print("NO match with integer key.")

# 3. Insert Progress with String ID (Simulating JSON payload)
print("\n--- Test 2: Insert with String ID ---")
lesson_id_str = str(lesson_id)
upsert_progress(user_id, lesson_id_str, "completed")
progress = get_user_progress(user_id)
print(f"Progress Keys: {list(progress.keys())}")
print(f"Key Type: {[type(k) for k in progress.keys()]}")

if lesson_id in progress:
    print("Match found with integer key after string insert.")
else:
    print("NO match with integer key after string insert.")

# 4. Check Template Logic Simulation
# Template uses user_progress.get(l.id)
# Assuming l.id is from get_lessons() which returns Rows/dicts with integer IDs (usually)

print("\n--- Template Logic Check ---")
# In the template loop:
# l in lessons
# user_progress.get(l.id)

# Let's verify what get_lessons returns exactly
print(f"Lesson object from DB: {lesson}")
# If it's sqlite3.Row, it behaves like a dict but accessing attributes might vary in Jinja
# But locally in python:
try:
    print(f"lesson['id']: {lesson['id']} (Type: {type(lesson['id'])})")
except:
    print("lesson['id'] failed")

# If we use user_progress.get(lesson['id'])
val = progress.get(lesson['id'])
print(f"user_progress.get(lesson['id']): {val}")

