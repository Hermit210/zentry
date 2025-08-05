"""
Test system-level functionality and health endpoints
"""

import pytest
from fastapi.testclient import TestClient


class TestSystemHealth:
    """Test system health and monitoring endpoints"""
    
    def test_root_endpoint(self, simple_app):
        """Test API root endpoint"""
        response = simple_app.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Zentry Cloud API"
        assert data["status"] == "running"
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/docs"
        
    def test_health_check_endpoint(self, simple_app):
        """Test health check endpoint"""
        response = simple_app.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["database"] == "in-memory"
        assert "users_count" in data
        assert isinstance(data["users_count"], int)
        
    def test_health_check_with_users(self, simple_app, sample_user_data):
        """Test health check reflects user count"""
        # Initial health check
        initial_response = simple_app.get("/health")
        initial_count = initial_response.json()["users_count"]
        
        # Create user
        simple_app.post("/auth/signup", json=sample_user_data)
        
        # Health check should reflect new user
        updated_response = simple_app.get("/health")
        updated_count = updated_response.json()["users_count"]
        
        assert updated_count == initial_count + 1
        
    def test_system_health_endpoint(self, simple_app):
        """Test system health endpoint"""
        response = simple_app.get("/system/health")
        
        # This endpoint might not exist in simple_main.py, so check if it's implemented
        if response.status_code == 404:
            pytest.skip("System health endpoint not implemented in simple backend")
        else:
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "timestamp" in data


class TestSystemMetrics:
    """Test system-wide metrics and statistics"""
    
    def test_vm_status_summary_empty_system(self, simple_app):
        """Test VM status summary on empty system"""
        response = simple_app.get("/vms/status/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_vms"] == 0
        assert data["status_breakdown"] == {}
        assert data["total_cost"] == 0
        assert data["total_uptime_hours"] == 0
        assert data["currently_running"] == []
        assert data["estimated_hourly_cost"] == 0
        
    def test_vm_status_summary_with_data(self, simple_app, sample_user_data, sample_project_data):
        """Test VM status summary with actual data"""
        # Setup
        simple_app.post("/auth/signup", json=sample_user_data)
        project_response = simple_app.post("/projects", json=sample_project_data)
        project_id = project_response.json()["id"]
        
        # Create VMs with different statuses
        vm_configs = [
            {"name": "running-vm", "instance_type": "small"},
            {"name": "medium-vm", "instance_type": "medium"},
            {"name": "large-vm", "instance_type": "large"}
        ]
        
        vm_ids = []
        for config in vm_configs:
            config.update({
                "image": "ubuntu-22.04",
                "project_id": project_id
            })
            
            response = simple_app.post("/vms", json=config)
            vm_ids.append(response.json()["id"])
            
        # Stop one VM
        simple_app.post(f"/vms/{vm_ids[0]}/stop")
        
        # Terminate one VM
        simple_app.delete(f"/vms/{vm_ids[1]}")
        
        # Get summary
        response = simple_app.get("/vms/status/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_vms"] == 3
        assert data["status_breakdown"]["running"] == 1
        assert data["status_breakdown"]["stopped"] == 1
        assert data["status_breakdown"]["terminated"] == 1
        assert len(data["currently_running"]) == 1
        assert data["estimated_hourly_cost"] > 0
        
    def test_pricing_information(self, simple_app):
        """Test VM pricing information endpoint"""
        response = simple_app.get("/vms/pricing")
        assert response.status_code == 200
        
        data = response.json()
        assert "pricing" in data
        assert "currency" in data
        assert "billing" in data
        assert "description" in data
        assert "specs" in data
        
        # Verify pricing structure
        pricing = data["pricing"]
        expected_types = ["small", "medium", "large", "xlarge"]
        expected_prices = [0.05, 0.10, 0.20, 0.40]
        
        for vm_type, expected_price in zip(expected_types, expected_prices):
            assert vm_type in pricing
            assert pricing[vm_type] == expected_price
            
        # Verify specs structure
        specs = data["specs"]
        for vm_type in expected_types:
            assert vm_type in specs
            spec = specs[vm_type]
            assert "cpu" in spec
            assert "ram" in spec
            assert "storage" in spec


class TestSystemLimits:
    """Test system limits and constraints"""
    
    def test_user_creation_limits(self, simple_app):
        """Test system handles multiple user creation"""
        users_to_create = 10
        created_users = []
        
        for i in range(users_to_create):
            user_data = {
                "email": f"user{i}@example.com",
                "name": f"User {i}",
                "password": "password123"
            }
            
            response = simple_app.post("/auth/signup", json=user_data)
            assert response.status_code == 201
            created_users.append(response.json()["user"])
            
        # Verify all users have unique IDs
        user_ids = [user["id"] for user in created_users]
        assert len(set(user_ids)) == users_to_create
        
        # Verify health check reflects correct count
        health_response = simple_app.get("/health")
        assert health_response.json()["users_count"] == users_to_create
        
    def test_project_creation_limits(self, simple_app, sample_user_data):
        """Test project creation limits"""
        # Setup user
        simple_app.post("/auth/signup", json=sample_user_data)
        
        # Create multiple projects
        projects_to_create = 15
        created_projects = []
        
        for i in range(projects_to_create):
            project_data = {
                "name": f"Project {i}",
                "description": f"Test project number {i}"
            }
            
            response = simple_app.post("/projects", json=project_data)
            assert response.status_code == 201
            created_projects.append(response.json())
            
        # Verify all projects were created
        projects_response = simple_app.get("/projects")
        assert len(projects_response.json()) == projects_to_create
        
    def test_vm_creation_with_credit_limits(self, simple_app, sample_user_data, sample_project_data):
        """Test VM creation respects credit limits"""
        # Setup
        simple_app.post("/auth/signup", json=sample_user_data)
        project_response = simple_app.post("/projects", json=sample_project_data)
        project_id = project_response.json()["id"]
        
        # Create VMs until credits run out
        created_vms = 0
        max_attempts = 2000  # Prevent infinite loop
        
        for i in range(max_attempts):
            vm_data = {
                "name": f"credit-test-vm-{i}",
                "instance_type": "small",  # Cheapest option
                "image": "ubuntu-22.04",
                "project_id": project_id
            }
            
            response = simple_app.post("/vms", json=vm_data)
            
            if response.status_code == 201:
                created_vms += 1
            elif response.status_code == 400:
                # Should fail due to insufficient credits
                error_message = response.json().get("detail", "")
                assert "Insufficient credits" in error_message
                break
            else:
                pytest.fail(f"Unexpected response code: {response.status_code}")
                
        # Should have created some VMs before running out of credits
        assert created_vms > 0
        assert created_vms < max_attempts  # Should have hit credit limit
        
        # Verify final user credits
        user_response = simple_app.get("/auth/me")
        final_credits = user_response.json()["credits"]
        assert final_credits < 50.0  # Should be less than starting credits


class TestSystemStability:
    """Test system stability under various conditions"""
    
    def test_rapid_sequential_requests(self, simple_app):
        """Test system handles rapid sequential requests"""
        # Make rapid requests to different endpoints
        endpoints = [
            "/",
            "/health",
            "/vms/pricing",
            "/vms/status/summary"
        ]
        
        for _ in range(10):  # 10 rapid cycles
            for endpoint in endpoints:
                response = simple_app.get(endpoint)
                assert response.status_code == 200
                
    def test_mixed_operation_stability(self, simple_app, sample_user_data, sample_project_data):
        """Test system stability with mixed operations"""
        # Setup
        simple_app.post("/auth/signup", json=sample_user_data)
        project_response = simple_app.post("/projects", json=sample_project_data)
        project_id = project_response.json()["id"]
        
        # Perform mixed operations
        operations = []
        
        # Create some VMs
        for i in range(3):
            vm_data = {
                "name": f"stability-vm-{i}",
                "instance_type": "small",
                "image": "ubuntu-22.04",
                "project_id": project_id
            }
            
            response = simple_app.post("/vms", json=vm_data)
            if response.status_code == 201:
                vm_id = response.json()["id"]
                operations.append(("vm_created", vm_id))
                
        # Perform various operations on created VMs
        for operation_type, vm_id in operations:
            if operation_type == "vm_created":
                # Test various VM operations
                simple_app.get(f"/vms/{vm_id}")
                simple_app.post(f"/vms/{vm_id}/stop")
                simple_app.get(f"/vms/{vm_id}")
                simple_app.post(f"/vms/{vm_id}/start")
                simple_app.get(f"/vms/{vm_id}")
                
        # System should remain stable
        health_response = simple_app.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"
        
    def test_error_recovery(self, simple_app, sample_user_data, sample_project_data):
        """Test system recovers gracefully from errors"""
        # Setup
        simple_app.post("/auth/signup", json=sample_user_data)
        project_response = simple_app.post("/projects", json=sample_project_data)
        project_id = project_response.json()["id"]
        
        # Create VM
        vm_response = simple_app.post("/vms", json={
            "name": "recovery-test-vm",
            "instance_type": "small",
            "image": "ubuntu-22.04",
            "project_id": project_id
        })
        vm_id = vm_response.json()["id"]
        
        # Generate various errors
        error_operations = [
            ("GET", "/vms/99999"),  # Non-existent VM
            ("POST", "/vms/99999/start"),  # Non-existent VM operation
            ("DELETE", "/projects/99999"),  # Non-existent project
            ("POST", "/vms"),  # Invalid VM data
        ]
        
        for method, endpoint in error_operations:
            if method == "GET":
                response = simple_app.get(endpoint)
            elif method == "POST":
                response = simple_app.post(endpoint, json={})
            elif method == "DELETE":
                response = simple_app.delete(endpoint)
                
            # Should get appropriate error codes, not crash
            assert response.status_code in [400, 404, 422]
            
        # System should still be healthy after errors
        health_response = simple_app.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"
        
        # Normal operations should still work
        vm_response = simple_app.get(f"/vms/{vm_id}")
        assert vm_response.status_code == 200