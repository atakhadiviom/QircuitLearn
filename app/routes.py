import os
import json
from flask import jsonify, request, send_from_directory, render_template, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from .simulate import simulate
from .models import (
    get_courses, get_lessons, get_course_by_slug, get_lesson_by_slug, upsert_progress,
    create_user, get_user_by_email, get_quiz_for_lesson, get_quiz_questions, 
    submit_quiz_attempt, get_forum_posts, create_forum_post, get_user_progress,
    get_forum_post, update_forum_post, delete_forum_post
)

def register_routes(app):
    def to_dict(row):
        try:
            return dict(row)
        except Exception:
            return row

    @app.context_processor
    def inject_user():
        return dict(user=session.get('username'), is_superuser=session.get('is_superuser'))

    @app.get("/")
    def index():
        try:
            courses = get_courses()
        except Exception:
            courses = []
        return render_template("landing.html", courses=courses)

    @app.get("/learn")
    def learn_no_slash():
        return redirect(url_for('learn_root'))

    @app.get("/learn/")
    def learn_root():
        try:
            courses = get_courses()
        except Exception:
            courses = []
        if courses:
            return redirect(url_for('course_overview', course_slug=courses[0]['slug']))
        return redirect(url_for('index'))

    @app.get("/learn/<course_slug>")
    def course_overview(course_slug):
        course = get_course_by_slug(course_slug)
        if not course:
            return "Course not found", 404
        
        lessons = get_lessons(course['id'])
        if lessons:
             return redirect(url_for('lesson_view', course_slug=course_slug, lesson_slug=lessons[0]['slug']))
        
        return render_template("index.html", course=course, lessons=[])

    @app.get("/learn/<course_slug>/<lesson_slug>")
    def lesson_view(course_slug, lesson_slug):
        course = get_course_by_slug(course_slug)
        if not course:
            return "Course not found", 404
            
        lessons = get_lessons(course['id'])
        current_lesson = None
        prev_lesson = None
        next_lesson = None
        
        for i, l in enumerate(lessons):
            if l['slug'] == lesson_slug:
                current_lesson = l
                if i > 0:
                    prev_lesson = lessons[i-1]
                if i < len(lessons) - 1:
                    next_lesson = lessons[i+1]
                break
        
        if not current_lesson:
            return "Lesson not found", 404
            
        user_progress = {}
        if 'user_id' in session:
            user_progress = get_user_progress(session['user_id'])

        return render_template("index.html", 
                               course=course, 
                               lessons=lessons, 
                               current_lesson=current_lesson,
                               prev_lesson=prev_lesson,
                               next_lesson=next_lesson,
                               user_progress=user_progress)

    @app.post("/api/simulate")
    def api_simulate():
        payload = request.get_json(silent=True) or {}
        shots = int(payload.get("shots", 0))
        data = payload.get("circuit", {})
        try:
            res = simulate(data, shots)
            return jsonify(res)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.post("/api/progress")
    def api_progress():
        payload = request.get_json(silent=True) or {}
        # Get real user_id from session
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
            
        lesson_id = payload.get("lesson_id")
        status = payload.get("status") # 'completed'
        
        if not lesson_id or not status:
            return jsonify({"error": "Missing lesson_id or status"}), 400
            
        try:
            upsert_progress(user_id, lesson_id, status)
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # --- Auth Routes ---
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")
            if create_user(username, email, password):
                flash("Registration successful! Please login.", "success")
                return redirect(url_for('login'))
            flash("Registration failed. Username or email might be taken.", "error")
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")
            user = get_user_by_email(email)
            if user:
                # Handle both dict and row access
                pwd_hash = user['password_hash'] if isinstance(user, dict) or hasattr(user, 'keys') else user[3]
                if check_password_hash(pwd_hash, password):
                    session['user_id'] = user['id'] if isinstance(user, dict) or hasattr(user, 'keys') else user[0]
                    session['username'] = user['username'] if isinstance(user, dict) or hasattr(user, 'keys') else user[1]
                    # Handle is_superuser. It might be index 4 or key 'is_superuser'
                    if isinstance(user, dict):
                        session['is_superuser'] = bool(user.get('is_superuser', False))
                    elif hasattr(user, 'keys'):
                        # sqlite3.Row
                        session['is_superuser'] = bool(dict(user).get('is_superuser', False))
                    else:
                        # Tuple index 4 if it exists, else False
                        session['is_superuser'] = bool(user[4]) if len(user) > 4 else False
                    
                    return redirect(url_for('index'))
            flash("Invalid credentials", "error")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for('index'))

    # --- Blog Routes ---
    @app.route("/forum")
    def forum_redirect():
        return redirect(url_for('blog'))

    @app.route("/blog")
    def blog():
        try:
            raw_posts = get_forum_posts()
            posts = [to_dict(p) for p in raw_posts]
        except Exception:
            posts = []
        return render_template("blog.html", posts=posts)
        
    @app.route("/blog/new", methods=["GET", "POST"])
    def new_blog_post():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # Simple admin check (replace with role-based auth later)
        if not session.get('is_superuser'):
            flash("Only admins can post articles.", "error")
            return redirect(url_for('blog'))
            
        if request.method == "POST":
            title = request.form.get("title")
            content = request.form.get("content")
            create_forum_post(session['user_id'], title, content)
            return redirect(url_for('blog'))
        return render_template("new_blog_post.html")

    @app.route("/blog/edit/<int:post_id>", methods=["GET", "POST"])
    def edit_blog_post(post_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
            
        if not session.get('is_superuser'):
            flash("Only admins can edit articles.", "error")
            return redirect(url_for('blog'))
            
        post = get_forum_post(post_id)
        if not post:
            flash("Post not found.", "error")
            return redirect(url_for('blog'))
            
        if request.method == "POST":
            title = request.form.get("title")
            content = request.form.get("content")
            update_forum_post(post_id, title, content)
            flash("Article updated successfully.", "success")
            return redirect(url_for('blog'))
            
        # Reuse the new_blog_post template but pass the post object
        return render_template("new_blog_post.html", post=to_dict(post))

    @app.post("/blog/delete/<int:post_id>")
    def delete_blog_post(post_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
            
        if not session.get('is_superuser'):
            flash("Only admins can delete articles.", "error")
            return redirect(url_for('blog'))
            
        delete_forum_post(post_id)
        flash("Article deleted successfully.", "success")
        return redirect(url_for('blog'))

    # --- Quiz Routes ---
    @app.route("/api/quiz/<int:lesson_id>")
    def get_quiz(lesson_id):
        quiz = get_quiz_for_lesson(lesson_id)
        if not quiz:
            return jsonify({"error": "No quiz found"}), 404
        
        quiz_dict = to_dict(quiz)
        questions = get_quiz_questions(quiz_dict['id'])
        
        q_list = []
        for q in questions:
            qd = to_dict(q)
            q_list.append({
                "id": qd['id'],
                "text": qd['question_text'],
                "options": json.loads(qd['options_json'])
            })
        return jsonify({"id": quiz_dict['id'], "title": quiz_dict['title'], "questions": q_list})

    @app.post("/api/quiz/submit")
    def submit_quiz():
        payload = request.get_json(silent=True) or {}
        quiz_id = payload.get("quiz_id")
        answers = payload.get("answers") # {question_id: option_index}
        
        if not quiz_id or not answers:
            return jsonify({"error": "Invalid data"}), 400
            
        # Grade it
        questions = get_quiz_questions(quiz_id)
        score = 0
        total = 0
        for q in questions:
            qd = to_dict(q)
            qid = str(qd['id'])
            if qid in answers:
                total += 1
                if answers[qid] == qd['correct_option_index']:
                    score += 1
        
        passed = (score / total) >= 0.7 if total > 0 else False
        
        # Only save attempt if user is logged in
        if 'user_id' in session:
            submit_quiz_attempt(session['user_id'], quiz_id, score, passed)
        
        return jsonify({"score": score, "total": total, "passed": passed})

    @app.get("/assets/<path:path>")
    def assets(path):
        return send_from_directory(os.path.join(os.path.dirname(__file__), "../static"), path)

    @app.get("/health")
    @app.get("/qircuitapp/health")
    def health():
        return jsonify({"status": "ok"})
