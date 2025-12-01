import os
import json
from flask import jsonify, request, send_from_directory, render_template, redirect, url_for, session, flash, make_response
from werkzeug.security import check_password_hash
from .simulate import simulate
from .models import (
    get_courses, get_lessons, get_course_by_slug, get_lesson_by_slug, upsert_progress,
    create_user, get_user_by_email, get_quiz_for_lesson, get_quiz_questions, 
    submit_quiz_attempt, get_forum_posts, get_user_progress,
    get_forum_post, delete_forum_post, get_quiz_by_id,
    get_user_passed_quiz_attempt, search_lessons, upsert_forum_post, get_forum_post_by_slug
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
        related_lessons = []
        
        for i, l in enumerate(lessons):
            if l['slug'] == lesson_slug:
                current_lesson = l
                if i > 0:
                    prev_lesson = lessons[i-1]
                if i < len(lessons) - 1:
                    next_lesson = lessons[i+1]
                # Related lessons: same section excluding current
                if l['section']:
                    related_lessons = [rl for rl in lessons if rl['section'] == l['section'] and rl['slug'] != l['slug']][:4]
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
                               related_lessons=related_lessons,
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
            meta_title = request.form.get("meta_title")
            meta_description = request.form.get("meta_description")
            slug = request.form.get("slug")
            if not slug and title:
                base = ''.join(c.lower() if c.isalnum() else '-' for c in title).strip('-')
                slug = '-'.join([s for s in base.split('-') if s])
            try:
                upsert_forum_post(session['user_id'], title, slug, meta_title, meta_description, content)
            except Exception as e:
                flash(f"Error publishing: {e}", "error")
                return render_template("new_blog_post.html", tinymce_api_key=os.getenv("TINYMCE_API_KEY", "3r5vbmw3vcozuhk57cjfcbes2u4mkwe09lo24uj0h4g73lsa"))
            return redirect(url_for('blog'))
        return render_template("new_blog_post.html", tinymce_api_key=os.getenv("TINYMCE_API_KEY", "3r5vbmw3vcozuhk57cjfcbes2u4mkwe09lo24uj0h4g73lsa"))

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
            meta_title = request.form.get("meta_title")
            meta_description = request.form.get("meta_description")
            slug = request.form.get("slug")
            if not slug and title:
                base = ''.join(c.lower() if c.isalnum() else '-' for c in title).strip('-')
                slug = '-'.join([s for s in base.split('-') if s])
            upsert_forum_post(session['user_id'], title, slug, meta_title, meta_description, content, post_id=post_id)
            flash("Article updated successfully.", "success")
            return redirect(url_for('blog'))
            
        # Reuse the new_blog_post template but pass the post object
        return render_template("new_blog_post.html", post=to_dict(post), tinymce_api_key=os.getenv("TINYMCE_API_KEY", "3r5vbmw3vcozuhk57cjfcbes2u4mkwe09lo24uj0h4g73lsa"))

    @app.route('/blog/<slug>')
    def blog_detail(slug):
        post = get_forum_post_by_slug(slug)
        if not post:
            return redirect(url_for('blog'))
        pd = to_dict(post)
        return render_template('post_detail.html', post=pd)

    @app.post('/api/upload')
    def upload_media():
        if 'user_id' not in session or not session.get('is_superuser'):
            return jsonify({"error": "Unauthorized"}), 401
        f = request.files.get('file')
        if not f:
            return jsonify({"error": "No file"}), 400
        name = f.filename
        allowed = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}
        ext = os.path.splitext(name)[1].lower()
        if ext not in allowed:
            return jsonify({"error": "Unsupported file type"}), 400
        upload_dir = os.path.join(os.path.dirname(__file__), '../static/uploads')
        os.makedirs(upload_dir, exist_ok=True)
        safe_name = ''.join(c if c.isalnum() or c in ('.','-','_') else '-' for c in name)
        original_path = os.path.join(upload_dir, safe_name)

        # Attempt WebP conversion for raster images
        convert_exts = {'.png', '.jpg', '.jpeg'}
        if ext in convert_exts:
            try:
                from PIL import Image
                f.stream.seek(0)
                im = Image.open(f.stream)
                im = im.convert('RGB')
                base = os.path.splitext(safe_name)[0]
                webp_name = base + '.webp'
                webp_path = os.path.join(upload_dir, webp_name)
                im.save(webp_path, 'WEBP', quality=82, method=6)
                url = url_for('assets', path=f'uploads/{webp_name}', _external=True)
                return jsonify({"location": url, "format": "webp"})
            except Exception:
                # Fallback: save original
                f.save(original_path)
                url = url_for('assets', path=f'uploads/{safe_name}', _external=True)
                return jsonify({"location": url, "format": ext.strip('.')})
        else:
            # For webp, svg, gif: save as-is
            f.save(original_path)
            url = url_for('assets', path=f'uploads/{safe_name}', _external=True)
            return jsonify({"location": url, "format": ext.strip('.')})

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

    @app.get("/api/quiz/status/<int:quiz_id>")
    def api_quiz_status(quiz_id):
        if 'user_id' not in session:
            return jsonify({"passed": False, "authenticated": False})
            
        attempt = get_user_passed_quiz_attempt(session['user_id'], quiz_id)
        if attempt:
            # attempt is a Row or dict
            return jsonify({"passed": True, "authenticated": True})
        return jsonify({"passed": False, "authenticated": True})

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
            answers_json = json.dumps(answers)
            submit_quiz_attempt(session['user_id'], quiz_id, score, passed, answers_json)
            if passed:
                quiz = get_quiz_by_id(quiz_id)
                if quiz:
                    # Handle both dict and row access
                    lesson_id = quiz['lesson_id'] if isinstance(quiz, dict) or hasattr(quiz, 'keys') else quiz[1]
                    upsert_progress(session['user_id'], lesson_id, 'completed')
        
        return jsonify({"score": score, "total": total, "passed": passed})

    @app.get("/assets/<path:path>")
    def assets(path):
        return send_from_directory(os.path.join(os.path.dirname(__file__), "../static"), path)

    @app.get("/health")
    @app.get("/qircuitapp/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route('/sitemap.xml')
    def sitemap():
        urls = []

        # Static pages
        urls.append(url_for('index', _external=True))
        urls.append(url_for('blog', _external=True))
        urls.append(url_for('register', _external=True))
        urls.append(url_for('login', _external=True))

        # Courses and Lessons
        try:
            courses = get_courses()
            for course in courses:
                c = to_dict(course)
                # Course overview page
                urls.append(url_for('course_overview', course_slug=c['slug'], _external=True))
                
                # Lessons
                lessons = get_lessons(c['id'])
                for lesson in lessons:
                    l = to_dict(lesson)
                    urls.append(url_for('lesson_view', course_slug=c['slug'], lesson_slug=l['slug'], _external=True))
        except Exception:
            pass

        # Blog posts
        try:
            posts = get_forum_posts()
            for p in posts:
                d = to_dict(p)
                if d.get('slug'):
                    urls.append(url_for('blog_detail', slug=d['slug'], _external=True))
        except Exception:
            pass

        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        for url in urls:
            xml += '  <url>\n'
            xml += f'    <loc>{url}</loc>\n'
            xml += '    <changefreq>weekly</changefreq>\n'
            xml += '  </url>\n'
        xml += '</urlset>'

        response = make_response(xml)
        response.headers["Content-Type"] = "application/xml"
        return response

    @app.get('/search')
    def search():
        q = request.args.get('q', '').strip()
        results = []
        if q:
            try:
                raw = search_lessons(q)
                # rows can be Row or dict; normalize
                results = []
                for r in raw:
                    d = dict(r) if hasattr(r, 'keys') else r
                    results.append({
                        'title': d['title'],
                        'slug': d['slug'],
                        'course_slug': d.get('course_slug'),
                        'course_title': d.get('course_title')
                    })
            except Exception:
                results = []
        return render_template('search.html', q=q, results=results)

    @app.route('/robots.txt')
    def robots_txt():
        lines = [
            "User-agent: *",
            "Allow: /",
            "Disallow: /api/",
            "Disallow: /qircuitapp/",
            "Disallow: /register",
            "Disallow: /login",
            f"Sitemap: {url_for('sitemap', _external=True)}",
        ]
        response = make_response("\n".join(lines))
        response.headers["Content-Type"] = "text/plain"
        return response
