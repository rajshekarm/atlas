"""
Quick test script for Flash service
Run: python test_flash_quick.py
"""
import httpx
import json

BASE_URL = "http://localhost:8000/api/flash"

def test_health():
    """Test health endpoint"""
    print("🏥 Testing health endpoint...")
    response = httpx.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print()

def test_analyze_job():
    """Test job analysis"""
    print("💼 Testing job analysis...")
    
    job_data = {
        "job_description": {
            "title": "Senior Backend Engineer",
            "company": "Tech Corp",
            "location": "San Francisco, CA",
            "description": "We're looking for an experienced backend engineer with Python expertise",
            "requirements": [
                "5+ years Python experience",
                "FastAPI framework",
                "PostgreSQL database"
            ],
            "responsibilities": [
                "Design and implement backend services",
                "Lead technical discussions"
            ],
            "preferred_qualifications": [
                "AWS experience",
                "Kubernetes knowledge"
            ],
            "url": "https://example.com/job/12345"
        }
    }
    
    response = httpx.post(f"{BASE_URL}/analyze-job", json=job_data, timeout=10.0)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Job ID: {data['job_id']}")
        print(f"   Required Skills: {', '.join(data['required_skills'][:5])}")
        print(f"   Seniority: {data['seniority_level']}")
        print(f"   Role Focus: {data['role_focus']}")
    else:
        print(f"   Error: {response.text}")
    print()

def test_get_profile():
    """Test get profile"""
    print("👤 Testing get user profile...")
    
    response = httpx.get(f"{BASE_URL}/profile/test-user-123", timeout=10.0)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Name: {data['full_name']}")
        print(f"   Email: {data['email']}")
        print(f"   Title: {data['current_title']}")
        print(f"   Experience: {data['years_of_experience']} years")
    else:
        print(f"   Error: {response.text}")
    print()

def test_answer_question():
    """Test question answering"""
    print("❓ Testing question answering...")
    
    question_data = {
        "question_context": {
            "question": "What is your email address?",
            "field_id": "email_field",
            "field_type": "email",
            "job_id": "test-job-123"
        },
        "user_id": "test-user-123"
    }
    
    response = httpx.post(f"{BASE_URL}/answer-question", json=question_data, timeout=10.0)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Question: {data['question']}")
        print(f"   Answer: {data['answer']}")
        print(f"   Confidence: {data['confidence']} ({data['confidence_score']:.2f})")
        print(f"   Requires Review: {data['requires_review']}")
    else:
        print(f"   Error: {response.text}")
    print()

def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Flash Service Quick Test")
    print("=" * 60)
    print()
    
    try:
        # Test 1: Health Check
        test_health()
        
        # Test 2: Job Analysis
        test_analyze_job()
        
        # Test 3: User Profile
        test_get_profile()
        
        # Test 4: Question Answering
        test_answer_question()
        
        print("=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except httpx.ConnectError:
        print("❌ Error: Could not connect to server")
        print("   Make sure the server is running:")
        print("   uvicorn app.main:app --reload --port 8000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
