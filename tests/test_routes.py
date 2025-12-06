import json
import os
import sys

import pytest

# Ensure project root is on sys.path so `app` can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app


@pytest.fixture
def app_instance():
    """Create a fresh Flask app instance for each test."""
    app = create_app()
    app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret-key",
    )
    return app


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def test_health_route(client):
    """Basic smoke test for health endpoint."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_robots_txt(client):
    """robots.txt should exist and include a Sitemap line."""
    resp = client.get("/robots.txt")
    assert resp.status_code == 200
    body = resp.data.decode("utf-8")
    # Basic directives
    assert "User-agent: *" in body
    assert "Allow: /" in body
    # Should reference sitemap
    assert "Sitemap:" in body


def test_search_no_query(client):
    """When no query is supplied, search should render successfully with empty results."""
    resp = client.get("/search")
    assert resp.status_code == 200


def test_search_with_query_monkeypatched(client, monkeypatch):
    """Search with a query string should pass results to the template."""
    import app.routes as routes_module

    # Fake rows returned from the DB layer
    fake_rows = [
        {
            "title": "Quantum Gates",
            "slug": "quantum-gates",
            "course_slug": "fundamentals",
            "course_title": "Quantum Fundamentals",
        }
    ]

    def fake_search_lessons(term):
        # Ensure the query term is passed through
        assert term == "quantum"
        return fake_rows

    monkeypatch.setattr(routes_module, "search_lessons", fake_search_lessons)

    resp = client.get("/search?q=quantum")
    assert resp.status_code == 200
    # The rendered HTML should include the lesson title
    assert b"Quantum Gates" in resp.data


def test_api_quiz_not_found(client, monkeypatch):
    """If no quiz exists for a lesson, API should respond with 404."""
    import app.routes as routes_module

    def fake_get_quiz_for_lesson(lesson_id):
        # Simulate no quiz for any lesson
        return None

    monkeypatch.setattr(routes_module, "get_quiz_for_lesson", fake_get_quiz_for_lesson)

    resp = client.get("/api/quiz/123")
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["error"] == "No quiz found"


def test_api_quiz_happy_path(client, monkeypatch):
    """Happy path for fetching quiz details."""
    import app.routes as routes_module

    fake_quiz = {"id": 1, "title": "Sample Quiz"}
    fake_questions = [
        {
            "id": 10,
            "question_text": "What is |0> after X gate?",
            "options_json": json.dumps(["|0>", "|1>"]),
        }
    ]

    def fake_get_quiz_for_lesson(lesson_id):
        assert lesson_id == 42
        return fake_quiz

    def fake_get_quiz_questions(quiz_id):
        assert quiz_id == 1
        return fake_questions

    monkeypatch.setattr(routes_module, "get_quiz_for_lesson", fake_get_quiz_for_lesson)
    monkeypatch.setattr(routes_module, "get_quiz_questions", fake_get_quiz_questions)

    resp = client.get("/api/quiz/42")
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["id"] == 1
    assert payload["title"] == "Sample Quiz"
    assert len(payload["questions"]) == 1
    q = payload["questions"][0]
    assert q["id"] == 10
    assert q["text"] == "What is |0> after X gate?"
    assert q["options"] == ["|0>", "|1>"]


def test_api_quiz_submit_grades_and_saves_progress(client, monkeypatch, app_instance):
    """Submitting a quiz should grade correctly and call persistence helpers when logged in."""
    import app.routes as routes_module

    # Fake questions: one correct answer, one incorrect
    fake_questions = [
        {
            "id": 1,
            "question_text": "Q1",
            "options_json": json.dumps(["a", "b"]),
            "correct_option_index": 0,
        },
        {
            "id": 2,
            "question_text": "Q2",
            "options_json": json.dumps(["a", "b"]),
            "correct_option_index": 1,
        },
    ]

    def fake_get_quiz_questions(quiz_id):
        assert quiz_id == 7
        return fake_questions

    # Track calls instead of touching the real database
    calls = {"submit_quiz_attempt": [], "upsert_progress": []}

    def fake_submit_quiz_attempt(user_id, quiz_id, score, passed, answers_json):
        calls["submit_quiz_attempt"].append(
            {
                "user_id": user_id,
                "quiz_id": quiz_id,
                "score": score,
                "passed": passed,
                "answers_json": answers_json,
            }
        )

    def fake_get_quiz_by_id(quiz_id):
        # Return mapping to a fictitious lesson for progress tracking
        return {"id": quiz_id, "lesson_id": 99}

    def fake_upsert_progress(user_id, lesson_id, status):
        calls["upsert_progress"].append(
            {"user_id": user_id, "lesson_id": lesson_id, "status": status}
        )

    monkeypatch.setattr(routes_module, "get_quiz_questions", fake_get_quiz_questions)
    monkeypatch.setattr(routes_module, "submit_quiz_attempt", fake_submit_quiz_attempt)
    monkeypatch.setattr(routes_module, "get_quiz_by_id", fake_get_quiz_by_id)
    monkeypatch.setattr(routes_module, "upsert_progress", fake_upsert_progress)

    with app_instance.test_client() as client_with_session:
        # Log in a fake user by manipulating the session
        with client_with_session.session_transaction() as sess:
            sess["user_id"] = 123

        answers = {"1": 0, "2": 1}  # both correct
        resp = client_with_session.post(
            "/api/quiz/submit",
            json={"quiz_id": 7, "answers": answers},
        )

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["score"] == 2
        assert data["total"] == 2
        assert data["passed"] is True

    # Ensure our fake persistence functions were invoked correctly
    assert len(calls["submit_quiz_attempt"]) == 1
    attempt = calls["submit_quiz_attempt"][0]
    assert attempt["user_id"] == 123
    assert attempt["quiz_id"] == 7
    assert attempt["score"] == 2
    assert attempt["passed"] is True

    assert len(calls["upsert_progress"]) == 1
    progress = calls["upsert_progress"][0]
    assert progress["user_id"] == 123
    assert progress["lesson_id"] == 99
    assert progress["status"] == "completed"


