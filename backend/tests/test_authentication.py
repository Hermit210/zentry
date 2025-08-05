"""
Test authentication endpoints and functionality
"""

import pytest
from fastapi.testclient import TestClient


class TestUserSignup:
    """Test user registration functionality"""
    
    def test_successful_signup(self, simple_app, sample_user_data):
        """Test successful user registration"""
        response = simple_app.post("/auth/signup", json=sample_user_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Check response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "user" in data
        assert data["token_type"] == "bearer"
        
        # Check user data
        user = data["user"]
        assert user["email"] == sample_user_data["email"]
        assert user["name"] == sample_user_data["name"]
        assert user["credits"] == 50.0  # Welcome credits
        assert "id" in user
        assert "created_at" in user
        
    def test_signup_duplicate_email(self, simple_app, sample_user_data):
        """Test signup with duplicate email"""
        # First signup
        response1 = simple_app.post("/auth/signup", json=sample_user_data)
        assert response1.status_code == 201
        
        # Second signup with same email
        response2 = simple_app.post("/auth/signup", json=sample_user_data)
        assert response2.status_code == 400
        
    def test_signup_invalid_email(self, simple_app):
        """Test signup with invalid email"""
        invalid_data = {
            "email": "invalid-email",
            "name": "Test User",
            "password": "testpassword123"
        }
        
        response = simple_app.post("/auth/signup", json=invalid_data)
        assert response.status_code == 422  # Validation error
        
    def test_signup_short_password(self, simple_app):
        """Test signup with short password"""
        invalid_data = {
            "email": "test@example.com",
            "name": "Test User",
            "password": "short"
        }
        
        response = simple_app.post("/auth/signup", json=invalid_data)
        assert response.status_code == 422  # Validation error
        
    def test_signup_empty_name(self, simple_app):
        """Test signup with empty name"""
        invalid_data = {
            "email": "test@example.com",
            "name": "",
            "password": "testpassword123"
        }
        
        response = simple_app.post("/auth/signup", json=invalid_data)
        assert response.status_code == 422  # Validation error
        
    def test_signup_missing_fields(self, simple_app):
        """Test signup with missing required fields"""
        incomplete_data = {
            "email": "test@example.com"
            # Missing name and password
        }
        
        response = simple_app.post("/auth/signup", json=incomplete_data)
        assert response.status_code == 422  # Validation error


class TestUserLogin:
    """Test user login functionality"""
    
    def test_successful_login(self, simple_app, sample_user_data):
        """Test successful user login"""
        # First signup
        signup_response = simple_app.post("/auth/signup", json=sample_user_data)
        assert signup_response.status_code == 201
        
        # Then login
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        
        response = simple_app.post("/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert "user" in data
        assert data["token_type"] == "bearer"
        
        # Check user data matches signup
        user = data["user"]
        assert user["email"] == sample_user_data["email"]
        assert user["name"] == sample_user_data["name"]
        
    def test_login_nonexistent_user(self, simple_app):
        """Test login with non-existent user"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "somepassword"
        }
        
        response = simple_app.post("/auth/login", json=login_data)
        assert response.status_code == 404
        
    def test_login_invalid_email_format(self, simple_app):
        """Test login with invalid email format"""
        login_data = {
            "email": "invalid-email",
            "password": "somepassword"
        }
        
        response = simple_app.post("/auth/login", json=login_data)
        assert response.status_code == 422  # Validation error
        
    def test_login_missing_fields(self, simple_app):
        """Test login with missing fields"""
        incomplete_data = {
            "email": "test@example.com"
            # Missing password
        }
        
        response = simple_app.post("/auth/login", json=incomplete_data)
        assert response.status_code == 422  # Validation error


class TestCurrentUser:
    """Test current user endpoint"""
    
    def test_get_current_user_success(self, simple_app, sample_user_data):
        """Test getting current user information"""
        # First signup
        signup_response = simple_app.post("/auth/signup", json=sample_user_data)
        assert signup_response.status_code == 201
        
        # Get current user
        response = simple_app.get("/auth/me")
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["name"] == sample_user_data["name"]
        assert data["credits"] == 50.0
        assert "id" in data
        assert "created_at" in data
        
    def test_get_current_user_no_users(self, simple_app):
        """Test getting current user when no users exist"""
        response = simple_app.get("/auth/me")
        assert response.status_code == 404


class TestAuthenticationIntegration:
    """Test authentication integration and edge cases"""
    
    def test_token_format(self, simple_app, sample_user_data):
        """Test that tokens have expected format"""
        response = simple_app.post("/auth/signup", json=sample_user_data)
        assert response.status_code == 201
        
        data = response.json()
        token = data["access_token"]
        
        # Token should be a string and contain the email
        assert isinstance(token, str)
        assert len(token) > 10  # Should be reasonably long
        assert sample_user_data["email"] in token  # Demo token contains email
        
    def test_consistent_user_data(self, simple_app, sample_user_data):
        """Test that user data is consistent across endpoints"""
        # Signup
        signup_response = simple_app.post("/auth/signup", json=sample_user_data)
        signup_user = signup_response.json()["user"]
        
        # Login
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        login_response = simple_app.post("/auth/login", json=login_data)
        login_user = login_response.json()["user"]
        
        # Current user
        me_response = simple_app.get("/auth/me")
        me_user = me_response.json()
        
        # All should have same core data
        assert signup_user["id"] == login_user["id"] == me_user["id"]
        assert signup_user["email"] == login_user["email"] == me_user["email"]
        assert signup_user["name"] == login_user["name"] == me_user["name"]
        
    def test_multiple_users_signup(self, simple_app):
        """Test multiple users can sign up"""
        users_data = [
            {"email": "user1@example.com", "name": "User One", "password": "password123"},
            {"email": "user2@example.com", "name": "User Two", "password": "password456"},
            {"email": "user3@example.com", "name": "User Three", "password": "password789"}
        ]
        
        user_ids = []
        for user_data in users_data:
            response = simple_app.post("/auth/signup", json=user_data)
            assert response.status_code == 201
            
            user_id = response.json()["user"]["id"]
            user_ids.append(user_id)
            
        # All users should have unique IDs
        assert len(set(user_ids)) == len(user_ids)
        
    def test_welcome_credits_allocation(self, simple_app, sample_user_data):
        """Test that new users receive welcome credits"""
        response = simple_app.post("/auth/signup", json=sample_user_data)
        assert response.status_code == 201
        
        user = response.json()["user"]
        assert user["credits"] == 50.0  # Welcome credits amount
        
    def test_user_id_generation(self, simple_app):
        """Test that user IDs are generated correctly"""
        users_data = [
            {"email": "user1@example.com", "name": "User One", "password": "password123"},
            {"email": "user2@example.com", "name": "User Two", "password": "password456"}
        ]
        
        for i, user_data in enumerate(users_data, 1):
            response = simple_app.post("/auth/signup", json=user_data)
            assert response.status_code == 201
            
            user_id = response.json()["user"]["id"]
            assert user_id == i  # Sequential ID generation