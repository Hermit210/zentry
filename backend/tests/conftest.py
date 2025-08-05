"""
Pytest configuration and fixtures for Zentry Cloud API tests
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
import os
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment variables
os.environ["USE_IN_MEMORY_DB"] = "true"
os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def simple_app():
    """Create FastAPI test client for simple_main.py"""
    from simple_main import app
    return TestClient(app)

@pytest.fixture
def main_app():
    """Create FastAPI test client for main.py"""
    from main import app
    return TestClient(app)

@pytest.fixture
async def async_simple_client():
    """Create async HTTP client for simple_main.py"""
    from simple_main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def async_main_client():
    """Create async HTTP client for main.py"""
    from main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "password": "testpassword123"
    }

@pytest.fixture
def sample_project_data():
    """Sample project data for testing"""
    return {
        "name": "Test Project",
        "description": "A test project for API testing"
    }

@pytest.fixture
def sample_vm_data():
    """Sample VM data for testing"""
    return {
        "name": "test-vm",
        "instance_type": "small",
        "image": "ubuntu-22.04",
        "project_id": 1
    }

@pytest.fixture
def auth_headers(simple_app, sample_user_data):
    """Get authentication headers for testing"""
    # First signup
    response = simple_app.post("/auth/signup", json=sample_user_data)
    assert response.status_code == 201
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(autouse=True)
def reset_storage():
    """Reset in-memory storage before each test"""
    try:
        from simple_main import users, projects, vms, billing_records
        users.clear()
        projects.clear()
        vms.clear()
        billing_records.clear()
    except ImportError:
        pass
    
    yield
    
    # Clean up after test
    try:
        from simple_main import users, projects, vms, billing_records
        users.clear()
        projects.clear()
        vms.clear()
        billing_records.clear()
    except ImportError:
        pass

@pytest.fixture
def mock_database():
    """Mock database for testing"""
    return {
        "users": {},
        "projects": [],
        "vms": [],
        "billing_records": []
    }