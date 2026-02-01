"""
Example test script for Flash service
Run with: python -m pytest app/services/flash/tests/test_flash.py -v
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_flash_health():
    """Test Flash service health endpoint"""
    response = client.get("/api/flash/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_job():
    """Test job analysis endpoint"""
    job_data = {
        "job_description": {
            "title": "Senior Backend Engineer",
            "company": "Tech Corp",
            "description": "We are looking for an experienced backend engineer with Python and FastAPI expertise.",
            "requirements": [
                "5+ years of Python experience",
                "Experience with FastAPI",
                "PostgreSQL knowledge"
            ],
            "url": "https://example.com/job/12345"
        }
    }
    
    response = client.post("/api/flash/analyze-job", json=job_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "job_id" in data
    assert "required_skills" in data
    assert "seniority_level" in data


def test_get_user_profile():
    """Test get user profile endpoint"""
    response = client.get("/api/flash/profile/test-user-123")
    assert response.status_code == 200
    
    data = response.json()
    assert data["user_id"] == "test-user-123"
    assert "full_name" in data
    assert "email" in data


def test_answer_question():
    """Test question answering endpoint"""
    question_data = {
        "question_context": {
            "question": "What is your email address?",
            "field_id": "email",
            "field_type": "email",
            "job_id": "job123"
        },
        "user_id": "test-user-123"
    }
    
    response = client.post("/api/flash/answer-question", json=question_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "answer" in data
    assert "confidence" in data
    assert "confidence_score" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
