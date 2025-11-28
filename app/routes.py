import os
import json
from flask import jsonify, request, send_from_directory, render_template, redirect, url_for
from .simulate import simulate
from .models import get_courses, get_lessons, get_course_by_slug, get_lesson_by_slug

def register_routes(app):
    def to_dict(row):
        try:
            return dict(row)
        except Exception:
            return row
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
        return render_template("landing.html", courses=courses)

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
            
        return render_template("index.html", 
                               course=course, 
                               lessons=lessons, 
                               current_lesson=current_lesson,
                               prev_lesson=prev_lesson,
                               next_lesson=next_lesson)

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

    @app.get("/assets/<path:path>")
    def assets(path):
        return send_from_directory(os.path.join(os.path.dirname(__file__), "../static"), path)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/debug/course/<slug>")
    def debug_course(slug):
        course = get_course_by_slug(slug)
        if not course:
            return jsonify({}), 404
        return jsonify(to_dict(course))

    @app.get("/debug/lessons/<course_slug>")
    def debug_lessons(course_slug):
        course = get_course_by_slug(course_slug)
        if not course:
            return jsonify({}), 404
        course_id = course['id'] if isinstance(course, dict) else course['id']
        lessons = get_lessons(course_id)
        return jsonify([to_dict(l) for l in lessons])
