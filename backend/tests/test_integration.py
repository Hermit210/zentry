"""
Integration tests for the Zentry Cloud API
Tests complete workflows and interactions between components
"""

import pytest
from fastapi.testclient import TestClient


class TestUserWorkflow:
    """Test complete user workflow from signup to VM management"""
    
    def test_complete_user_journey(self, simple_app):
        """Test a complete user journey through the API"""
        # 1. User signup
        user_data = {
            "email": "journey@example.com",
            "name": "Journey User",
            "password": "password123"
        }
        
        signup_response = simple_app.post("/auth/signup", json=user_data)
        assert signup_response.status_code == 201
        
        user = signup_response.json()["user"]
        token = signup_response.json()["access_token"]
        
        # Verify user starts with welcome credits
        assert user["credits"] == 50.0
        
        # 2. Create a project
        project_data = {
            "name": "My First Project",
            "description": "A test project for my VMs"
        }
        
        project_response = simple_app.post("/projects", json=project_data)
        assert project_response.status_code == 201
        
        project = project_response.json()
        project_id = project["id"]
        
        # 3. Create multiple VMs in the project
        vm_configs = [
            {"name": "web-server", "instance_type": "small", "image": "ubuntu-22.04"},
            {"name": "database", "instance_type": "medium", "image": "ubuntu-22.04"},
            {"name": "cache", "instance_type": "small", "image": "ubuntu-22.04"}
        ]
        
        vm_ids = []
        for vm_config in vm_configs:
            vm_config["project_id"] = project_id
            
            vm_response = simple_app.post("/vms", json=vm_config)
            assert vm_response.status_code == 201
            
            vm = vm_response.json()
            vm_ids.append(vm["id"])
            assert vm["status"] == "running"
            
        # 4. Verify project shows correct VM count
        project_detail_response = simple_app.get(f"/projects/{project_id}")
        project_detail = project_detail_response.json()
        
        assert len(project_detail["vms"]) == 3
        assert project_detail["vm_count"] == 3
        
        # 5. Test VM operations
        # Stop one VM
        stop_response = simple_app.post(f"/vms/{vm_ids[0]}/stop")
        assert stop_response.status_code == 200
        
        # Restart another VM
        restart_response = simple_app.post(f"/vms/{vm_ids[1]}/restart")
        assert restart_response.status_code == 200
        
        # 6. Check VM status summary
        summary_response = simple_app.get("/vms/status/summary")
        summary = summary_response.json()
        
        assert summary["total_vms"] == 3
        assert summary["status_breakdown"]["running"] == 2
        assert summary["status_breakdown"]["stopped"] == 1
        
        # 7. Get VM metrics
        metrics_response = simple_app.get(f"/vms/{vm_ids[0]}/metrics")
        assert metrics_response.status_code == 200  # Stopped VM (metrics still available)
        
        metrics_response = simple_app.get(f"/vms/{vm_ids[1]}/metrics")
        assert metrics_response.status_code == 200  # Running VM
        
        # 8. Delete one VM
        delete_response = simple_app.delete(f"/vms/{vm_ids[2]}")
        assert delete_response.status_code == 200
        
        # 9. Verify final state
        final_summary = simple_app.get("/vms/status/summary").json()
        assert final_summary["total_vms"] == 3
        assert final_summary["status_breakdown"]["terminated"] == 1
        
    def test_credit_management_workflow(self, simple_app):
        """Test credit management throughout VM lifecycle"""
        # Create user
        user_data = {
            "email": "credits@example.com",
            "name": "Credit User",
            "password": "password123"
        }
        
        signup_response = simple_app.post("/auth/signup", json=user_data)
        initial_credits = signup_response.json()["user"]["credits"]
        
        # Create project
        project_response = simple_app.post("/projects", json={
            "name": "Credit Test Project"
        })
        project_id = project_response.json()["id"]
        
        # Create VM (should deduct creation cost)
        vm_response = simple_app.post("/vms", json={
            "name": "credit-test-vm",
            "instance_type": "small",
            "project_id": project_id,
            "image": "ubuntu-22.04"
        })
        assert vm_response.status_code == 201
        vm_id = vm_response.json()["id"]
        
        # Check that credits were deducted
        user_response = simple_app.get("/auth/me")
        current_credits = user_response.json()["credits"]
        assert current_credits < initial_credits
        
        # Perform operations that cost credits
        simple_app.post(f"/vms/{vm_id}/stop")
        simple_app.post(f"/vms/{vm_id}/start")
        simple_app.post(f"/vms/{vm_id}/restart")
        
        # Final credit check
        final_user_response = simple_app.get("/auth/me")
        final_credits = final_user_response.json()["credits"]
        assert final_credits < current_credits


class TestProjectVMIntegration:
    """Test integration between projects and VMs"""
    
    def test_project_vm_lifecycle(self, simple_app, sample_user_data):
        """Test complete project and VM lifecycle"""
        # Setup
        simple_app.post("/auth/signup", json=sample_user_data)
        
        # Create multiple projects
        projects = []
        for i in range(2):
            project_response = simple_app.post("/projects", json={
                "name": f"Project {i+1}",
                "description": f"Test project {i+1}"
            })
            projects.append(project_response.json())
            
        # Create VMs in different projects
        vm_counts = [2, 3]  # Project 1: 2 VMs, Project 2: 3 VMs
        
        for project_idx, (project, vm_count) in enumerate(zip(projects, vm_counts)):
            for vm_idx in range(vm_count):
                vm_response = simple_app.post("/vms", json={
                    "name": f"vm-p{project_idx+1}-{vm_idx+1}",
                    "instance_type": "small",
                    "image": "ubuntu-22.04",
                    "project_id": project["id"]
                })
                assert vm_response.status_code == 201
                
        # Verify project VM counts
        for project_idx, (project, expected_count) in enumerate(zip(projects, vm_counts)):
            project_detail = simple_app.get(f"/projects/{project['id']}").json()
            assert len(project_detail["vms"]) == expected_count
            assert project_detail["vm_count"] == expected_count
            
        # Test project deletion with VMs
        delete_response = simple_app.delete(f"/projects/{projects[0]['id']}")
        assert delete_response.status_code == 200
        assert "VMs were terminated" in delete_response.json()["message"]
        
        # Verify VMs in deleted project are terminated
        all_vms = simple_app.get("/vms").json()["vms"]
        project_1_vms = [vm for vm in all_vms if vm["project_id"] == projects[0]["id"]]
        
        for vm in project_1_vms:
            assert vm["status"] == "terminated"
            
    def test_cross_project_vm_isolation(self, simple_app, sample_user_data):
        """Test that VMs are properly isolated between projects"""
        # Setup
        simple_app.post("/auth/signup", json=sample_user_data)
        
        # Create two projects
        project1 = simple_app.post("/projects", json={"name": "Project 1"}).json()
        project2 = simple_app.post("/projects", json={"name": "Project 2"}).json()
        
        # Create VMs with same name in different projects (should be allowed)
        vm_data = {
            "name": "duplicate-name-vm",
            "instance_type": "small",
            "image": "ubuntu-22.04"
        }
        
        # Create in project 1
        vm1_data = vm_data.copy()
        vm1_data["project_id"] = project1["id"]
        vm1_response = simple_app.post("/vms", json=vm1_data)
        assert vm1_response.status_code == 201
        
        # Create in project 2 (should succeed despite same name)
        vm2_data = vm_data.copy()
        vm2_data["project_id"] = project2["id"]
        vm2_response = simple_app.post("/vms", json=vm2_data)
        assert vm2_response.status_code == 201
        
        # Verify both VMs exist and are in correct projects
        vm1 = vm1_response.json()
        vm2 = vm2_response.json()
        
        assert vm1["project_id"] == project1["id"]
        assert vm2["project_id"] == project2["id"]
        assert vm1["name"] == vm2["name"]  # Same name allowed in different projects


class TestErrorHandlingIntegration:
    """Test error handling across different components"""
    
    def test_cascading_error_scenarios(self, simple_app, sample_user_data):
        """Test error scenarios that affect multiple components"""
        # Setup
        simple_app.post("/auth/signup", json=sample_user_data)
        project_response = simple_app.post("/projects", json={"name": "Error Test Project"})
        project_id = project_response.json()["id"]
        
        # Create VM
        vm_response = simple_app.post("/vms", json={
            "name": "error-test-vm",
            "instance_type": "small",
            "image": "ubuntu-22.04",
            "project_id": project_id
        })
        vm_id = vm_response.json()["id"]
        
        # Test operations on non-existent resources
        error_scenarios = [
            ("GET", "/projects/99999", 404),
            ("PUT", "/projects/99999", 404),
            ("DELETE", "/projects/99999", 404),
            ("GET", "/vms/99999", 404),
            ("POST", "/vms/99999/start", 404),
            ("POST", "/vms/99999/stop", 404),
            ("DELETE", "/vms/99999", 404),
        ]
        
        for method, endpoint, expected_status in error_scenarios:
            if method == "GET":
                response = simple_app.get(endpoint)
            elif method == "POST":
                response = simple_app.post(endpoint, json={})
            elif method == "PUT":
                response = simple_app.put(endpoint, json={})
            elif method == "DELETE":
                response = simple_app.delete(endpoint)
                
            assert response.status_code == expected_status
            
        # Test invalid state transitions
        # Terminate VM first
        simple_app.delete(f"/vms/{vm_id}")
        
        # Try operations on terminated VM
        terminated_operations = [
            ("POST", f"/vms/{vm_id}/start", 400),
            ("POST", f"/vms/{vm_id}/stop", 400),
            ("POST", f"/vms/{vm_id}/restart", 400),
            ("GET", f"/vms/{vm_id}/metrics", 400),
        ]
        
        for method, endpoint, expected_status in terminated_operations:
            if method == "POST":
                response = simple_app.post(endpoint)
            elif method == "GET":
                response = simple_app.get(endpoint)
                
            assert response.status_code == expected_status
            
    def test_validation_error_consistency(self, simple_app):
        """Test that validation errors are consistent across endpoints"""
        # Test consistent validation error format
        validation_tests = [
            ("POST", "/auth/signup", {"email": "invalid-email"}),
            ("POST", "/projects", {"name": ""}),
            ("POST", "/vms", {"name": "test", "instance_type": "invalid"}),
        ]
        
        for method, endpoint, invalid_data in validation_tests:
            response = simple_app.post(endpoint, json=invalid_data)
            assert response.status_code == 422
            
            # All validation errors should have consistent structure
            # (This depends on FastAPI's default validation error format)


class TestPerformanceIntegration:
    """Test performance aspects of integrated workflows"""
    
    def test_bulk_operations_performance(self, simple_app, sample_user_data):
        """Test performance with multiple resources"""
        import time
        
        # Setup
        simple_app.post("/auth/signup", json=sample_user_data)
        
        # Create multiple projects
        start_time = time.time()
        project_ids = []
        
        for i in range(5):
            response = simple_app.post("/projects", json={
                "name": f"Bulk Project {i}",
                "description": f"Bulk test project {i}"
            })
            project_ids.append(response.json()["id"])
            
        project_creation_time = time.time() - start_time
        assert project_creation_time < 2.0  # Should complete in under 2 seconds
        
        # Create multiple VMs across projects
        start_time = time.time()
        vm_ids = []
        
        for i, project_id in enumerate(project_ids):
            for j in range(2):  # 2 VMs per project
                response = simple_app.post("/vms", json={
                    "name": f"bulk-vm-{i}-{j}",
                    "instance_type": "small",
                    "image": "ubuntu-22.04",
                    "project_id": project_id
                })
                vm_ids.append(response.json()["id"])
                
        vm_creation_time = time.time() - start_time
        assert vm_creation_time < 5.0  # Should complete in under 5 seconds
        
        # Test bulk retrieval performance
        start_time = time.time()
        
        projects_response = simple_app.get("/projects")
        vms_response = simple_app.get("/vms")
        summary_response = simple_app.get("/vms/status/summary")
        
        retrieval_time = time.time() - start_time
        assert retrieval_time < 1.0  # Should complete in under 1 second
        
        # Verify data integrity
        assert len(projects_response.json()) == 5
        assert len(vms_response.json()["vms"]) == 10
        assert summary_response.json()["total_vms"] == 10
        
    def test_concurrent_operations_simulation(self, simple_app, sample_user_data):
        """Simulate concurrent operations (basic test)"""
        # Setup
        simple_app.post("/auth/signup", json=sample_user_data)
        project_response = simple_app.post("/projects", json={"name": "Concurrent Test"})
        project_id = project_response.json()["id"]
        
        # Create VM
        vm_response = simple_app.post("/vms", json={
            "name": "concurrent-vm",
            "instance_type": "small",
            "image": "ubuntu-22.04",
            "project_id": project_id
        })
        vm_id = vm_response.json()["id"]
        
        # Simulate rapid operations (in sequence, but testing state consistency)
        operations = [
            ("POST", f"/vms/{vm_id}/stop"),
            ("POST", f"/vms/{vm_id}/start"),
            ("POST", f"/vms/{vm_id}/restart"),
            ("GET", f"/vms/{vm_id}"),
            ("GET", f"/vms/{vm_id}/metrics"),
        ]
        
        for method, endpoint in operations:
            if method == "POST":
                response = simple_app.post(endpoint)
            else:
                response = simple_app.get(endpoint)
                
            # All operations should either succeed or fail gracefully
            assert response.status_code in [200, 400, 404]
            
        # Final state should be consistent
        final_vm = simple_app.get(f"/vms/{vm_id}").json()
        assert final_vm["status"] in ["running", "stopped", "terminated"]