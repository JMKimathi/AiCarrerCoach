"""Run isolated API integration checks with: python -m backend.test_api"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

_test_dir = tempfile.TemporaryDirectory(prefix="career-coach-api-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_test_dir.name, 'test.db').as_posix()}"
os.environ["SECRET_KEY"] = "integration-test-signing-key-32-bytes-minimum"

from fastapi.testclient import TestClient

from backend.app.database import SessionLocal, User, engine
from backend.app.main import app
from backend.app.rag_engine import RAGEngine
from backend.app.security import hash_password


def run_tests() -> None:
    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200
        assert client.get("/api/resources").status_code == 401
        assert client.get("/api/admin/overview").status_code == 401

        registration = {
            "full_name": "Test Student",
            "email": "student@example.edu",
            "password": "correct-horse-42",
            "course": "BSc Computer Science",
            "career_goal": "Data engineering",
        }
        response = client.post("/api/auth/register", json=registration)
        assert response.status_code == 200, response.text
        student = response.json()
        assert student["user"]["role"] == "student"
        assert client.post("/api/auth/register", json=registration).status_code == 400
        assert client.post("/api/auth/login", json={"email": registration["email"], "password": "wrong-password"}).status_code == 401
        login = client.post("/api/auth/login", json={"email": registration["email"], "password": registration["password"]})
        assert login.status_code == 200, login.text
        student_headers = {"Authorization": f"Bearer {login.json()['token']}"}

        resources = client.get("/api/resources", headers=student_headers)
        assert resources.status_code == 200, resources.text
        assert len(resources.json()) >= 1
        assert client.get("/api/admin/overview", headers=student_headers).status_code == 403

        # Exercise chat's resource fallback without loading optional transformer assets.
        with patch.object(RAGEngine, "get_instance", side_effect=RuntimeError("RAG unavailable")):
            chat = client.post("/api/chat", json={"query": "portfolio website career"}, headers=student_headers)
            assert chat.status_code == 200, chat.text
            chat_data = chat.json()
            assert chat_data["sources"]
            assert "portfolio" in chat_data["response"].lower()
            session_id = chat_data["session_id"]
            assert client.get("/api/chat/sessions", headers=student_headers).json()[0]["session_id"] == session_id
            feedback = client.post(
                "/api/feedback",
                json={"rating": 5, "is_accurate": False, "comments": "Needs review", "session_id": session_id},
                headers=student_headers,
            )
            assert feedback.status_code == 200, feedback.text
            assessment = client.post(
                "/api/career/assess",
                json={"skills": ["python", "sql"], "interests": ["data", "systems"], "preferred_activities": ["building data pipelines"]},
                headers=student_headers,
            )
            assert assessment.status_code == 200, assessment.text
            assert assessment.json()["recommendations"]

        db = SessionLocal()
        try:
            db.add(User(
                full_name="Test Admin",
                email="admin@example.edu",
                password_hash=hash_password("admin-password-42"),
                role="admin",
                course="Staff",
                career_goal="Administration",
            ))
            db.commit()
        finally:
            db.close()

        admin_login = client.post("/api/auth/login", json={"email": "admin@example.edu", "password": "admin-password-42"})
        assert admin_login.status_code == 200, admin_login.text
        assert admin_login.json()["user"]["role"] == "admin"
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['token']}"}
        overview = client.get("/api/admin/overview", headers=admin_headers)
        assert overview.status_code == 200, overview.text
        assert overview.json()["active_students"] == 1
        assert overview.json()["chats_this_week"] == 1
        assert overview.json()["flagged_responses"] == 1
        created = client.post(
            "/api/resources",
            json={"title": "Test Career Guide", "category": "Career Paths", "content": "A real resource saved by an administrator."},
            headers=admin_headers,
        )
        assert created.status_code == 200, created.text
        assert client.get("/api/resources", headers=student_headers).status_code == 200

    print("All backend API integration checks passed.")
    engine.dispose()
    _test_dir.cleanup()


if __name__ == "__main__":
    run_tests()
