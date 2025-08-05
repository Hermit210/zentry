"""
Test project management endpoints
"""

import pytest
from fastapi.testclient import TestClient


class TestProjectCreation:
    """Test project creation functionality"""
    
    def test_create_project_success(self, simple_app, sample_project_data):
        """Test successful project creation"""
        response = simple_app.post("/projects", json=sample_project_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Check response structure
        assert "id" in data
        assert data["name"] == sample_project_data["name"]
        assert data["description"] == sample_project_data["description"]
        assert data["user_id"] == 1  # Demo user ID
        assert "created_at" in data
        
    def test_create_project_minimal_data(self, simple_app):
        """Test project creation with minimal required data"""
        minimal_data = {"name": "Minimal Project"}
        
        response = simple_app.post("/projects", json=minimal_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == "Minimal Project"
        assert data["description"] == ""  # Should default to empty string
        
    def test_create_project_empty_name(self, simple_app):
        """Test project creation with empty name"""
        invalid_data = {"name": "", "description": "Test description"}
        
        response = simple_app.post("/projects", json=invalid_data)
        assert response.status_code == 422  # Validation error
        
    def test_create_project_long_name(self, simple_app):
        """Test project creation with name too long"""
        invalid_data = {
            "name": "x" * 101,  # Exceeds 100 character limit
            "description": "Test description"
        }
        
        response = simple_app.post("/projects", json=invalid_data)
        assert response.status_code == 422  # Validation error
        
    def test_create_project_long_description(self, simple_app):
        """Test project creation with description too long"""
        invalid_data = {
            "name": "Test Project",
            "description": "x" * 501  # Exceeds 500 character limit
        }
        
        response = simple_app.post("/projects", json=invalid_data)
        assert response.status_code == 422  # Validation error
        
    def test_create_multiple_projects(self, simple_app):
        """Test creating multiple projects"""
        projects_data = [
            {"name": "Project 1", "description": "First project"},
            {"name": "Project 2", "description": "Second project"},
            {"name": "Project 3", "description": "Third project"}
        ]
        
        project_ids = []
        for project_data in projects_data:
            response = simple_app.post("/projects", json=project_data)
            assert response.status_code == 201
            
            project_id = response.json()["id"]
            project_ids.append(project_id)
            
        # All projects should have unique IDs
        assert len(set(project_ids)) == len(project_ids)
        
        # IDs should be sequential
        assert project_ids == [1, 2, 3]


class TestProjectRetrieval:
    """Test project retrieval functionality"""
    
    def test_get_projects_empty(self, simple_app):
        """Test getting projects when none exist"""
        response = simple_app.get("/projects")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
        
    def test_get_projects_with_data(self, simple_app, sample_project_data):
        """Test getting projects when some exist"""
        # Create a project first
        create_response = simple_app.post("/projects", json=sample_project_data)
        assert create_response.status_code == 201
        
        # Get projects
        response = simple_app.get("/projects")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        
        project = data[0]
        assert project["name"] == sample_project_data["name"]
        assert project["description"] == sample_project_data["description"]
        assert "vm_count" in project
        assert project["vm_count"] == 0  # No VMs yet
        
    def test_get_single_project_success(self, simple_app, sample_project_data):
        """Test getting a single project by ID"""
        # Create a project first
        create_response = simple_app.post("/projects", json=sample_project_data)
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]
        
        # Get the project
        response = simple_app.get(f"/projects/{project_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == sample_project_data["name"]
        assert "vms" in data
        assert isinstance(data["vms"], list)
        assert len(data["vms"]) == 0  # No VMs yet
        assert "vm_count" in data
        
    def test_get_single_project_not_found(self, simple_app):
        """Test getting a non-existent project"""
        response = simple_app.get("/projects/999")
        assert response.status_code == 404
        
    def test_projects_vm_count_accuracy(self, simple_app, sample_project_data, sample_vm_data):
        """Test that project VM counts are accurate"""
        # Create a project
        project_response = simple_app.post("/projects", json=sample_project_data)
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]
        
        # Create a user first (required for VM creation)
        user_data = {"email": "test@example.com", "name": "Test User", "password": "password123"}
        simple_app.post("/auth/signup", json=user_data)
        
        # Create VMs in the project
        vm_data = sample_vm_data.copy()
        vm_data["project_id"] = project_id
        
        for i in range(3):
            vm_data["name"] = f"test-vm-{i}"
            vm_response = simple_app.post("/vms", json=vm_data)
            assert vm_response.status_code == 201
            
        # Check project VM count
        response = simple_app.get("/projects")
        projects = response.json()
        
        project = next(p for p in projects if p["id"] == project_id)
        assert project["vm_count"] == 3


class TestProjectUpdate:
    """Test project update functionality"""
    
    def test_update_project_success(self, simple_app, sample_project_data):
        """Test successful project update"""
        # Create a project first
        create_response = simple_app.post("/projects", json=sample_project_data)
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]
        
        # Update the project
        update_data = {
            "name": "Updated Project Name",
            "description": "Updated description"
        }
        
        response = simple_app.put(f"/projects/{project_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert "updated_at" in data
        
    def test_update_project_partial(self, simple_app, sample_project_data):
        """Test partial project update"""
        # Create a project first
        create_response = simple_app.post("/projects", json=sample_project_data)
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]
        original_description = create_response.json()["description"]
        
        # Update only the name
        update_data = {"name": "New Name Only"}
        
        response = simple_app.put(f"/projects/{project_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == original_description  # Should remain unchanged
        
    def test_update_project_not_found(self, simple_app):
        """Test updating a non-existent project"""
        update_data = {"name": "Updated Name"}
        
        response = simple_app.put("/projects/999", json=update_data)
        assert response.status_code == 404
        
    def test_update_project_invalid_data(self, simple_app, sample_project_data):
        """Test updating project with invalid data"""
        # Create a project first
        create_response = simple_app.post("/projects", json=sample_project_data)
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]
        
        # Try to update with invalid data
        invalid_data = {"name": "x" * 101}  # Too long
        
        response = simple_app.put(f"/projects/{project_id}", json=invalid_data)
        assert response.status_code == 422  # Validation error


class TestProjectDeletion:
    """Test project deletion functionality"""
    
    def test_delete_project_success(self, simple_app, sample_project_data):
        """Test successful project deletion"""
        # Create a project first
        create_response = simple_app.post("/projects", json=sample_project_data)
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]
        
        # Delete the project
        response = simple_app.delete(f"/projects/{project_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "message" in data
        
        # Verify project is deleted
        get_response = simple_app.get(f"/projects/{project_id}")
        assert get_response.status_code == 404
        
    def test_delete_project_not_found(self, simple_app):
        """Test deleting a non-existent project"""
        response = simple_app.delete("/projects/999")
        assert response.status_code == 404
        
    def test_delete_project_with_vms(self, simple_app, sample_project_data, sample_vm_data):
        """Test deleting a project that contains VMs"""
        # Create a user first
        user_data = {"email": "test@example.com", "name": "Test User", "password": "password123"}
        simple_app.post("/auth/signup", json=user_data)
        
        # Create a project
        project_response = simple_app.post("/projects", json=sample_project_data)
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]
        
        # Create a VM in the project
        vm_data = sample_vm_data.copy()
        vm_data["project_id"] = project_id
        vm_response = simple_app.post("/vms", json=vm_data)
        assert vm_response.status_code == 201
        vm_id = vm_response.json()["id"]
        
        # Delete the project
        response = simple_app.delete(f"/projects/{project_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "VMs were terminated" in data["message"]
        
        # Verify VM is terminated
        vm_response = simple_app.get(f"/vms/{vm_id}")
        assert vm_response.status_code == 200
        vm_data = vm_response.json()
        assert vm_data["status"] == "terminated"


class TestProjectIntegration:
    """Test project integration with other components"""
    
    def test_project_vm_relationship(self, simple_app, sample_project_data, sample_vm_data):
        """Test the relationship between projects and VMs"""
        # Create user and project
        user_data = {"email": "test@example.com", "name": "Test User", "password": "password123"}
        simple_app.post("/auth/signup", json=user_data)
        
        project_response = simple_app.post("/projects", json=sample_project_data)
        project_id = project_response.json()["id"]
        
        # Create VM in project
        vm_data = sample_vm_data.copy()
        vm_data["project_id"] = project_id
        vm_response = simple_app.post("/vms", json=vm_data)
        assert vm_response.status_code == 201
        
        # Get project with VMs
        response = simple_app.get(f"/projects/{project_id}")
        project = response.json()
        
        assert len(project["vms"]) == 1
        assert project["vm_count"] == 1
        assert project["vms"][0]["project_id"] == project_id
        
    def test_project_id_validation_in_vm_creation(self, simple_app, sample_vm_data):
        """Test that VM creation validates project ID"""
        # Create user first
        user_data = {"email": "test@example.com", "name": "Test User", "password": "password123"}
        simple_app.post("/auth/signup", json=user_data)
        
        # Try to create VM with non-existent project ID
        vm_data = sample_vm_data.copy()
        vm_data["project_id"] = 999  # Non-existent project
        
        response = simple_app.post("/vms", json=vm_data)
        assert response.status_code == 404  # Project not found