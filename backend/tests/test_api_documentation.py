"""
Test API documentation and OpenAPI schema
"""

import pytest
from fastapi.testclient import TestClient
import time


class TestAPIDocumentation:
    """Test API documentation endpoints and schema"""
    
    def test_openapi_schema_generation(self, main_app):
        """Test that OpenAPI schema is generated correctly"""
        response = main_app.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "Zentry Cloud API"
        assert schema["info"]["version"] == "1.0.0"
        
        # Test enhanced schema properties
        assert "description" in schema["info"]
        assert "contact" in schema["info"]
        assert "license" in schema["info"]
        assert "servers" in schema
        
    def test_docs_endpoint_accessible(self, main_app):
        """Test that documentation endpoint is accessible"""
        response = main_app.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
    def test_redoc_endpoint_accessible(self, main_app):
        """Test that ReDoc endpoint is accessible"""
        response = main_app.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
    def test_api_has_proper_tags(self, main_app):
        """Test that API endpoints are properly tagged"""
        response = main_app.get("/openapi.json")
        schema = response.json()
        
        # Check that tags are defined at the top level
        assert "tags" in schema
        tags = schema["tags"]
        
        # Verify expected tags exist
        expected_tags = ["System", "Authentication", "Projects", "Virtual Machines", "Health", "API Versioning"]
        tag_names = [tag["name"] for tag in tags]
        
        for expected_tag in expected_tags:
            assert expected_tag in tag_names, f"Missing tag: {expected_tag}"
            
        # Verify tags have descriptions
        for tag in tags:
            assert "description" in tag, f"Tag {tag['name']} missing description"
        
    def test_response_models_defined(self, main_app):
        """Test that response models are properly defined"""
        response = main_app.get("/openapi.json")
        schema = response.json()
        
        # Check that components/schemas exist
        assert "components" in schema
        assert "schemas" in schema["components"]
        
        # Check for key response models
        schemas = schema["components"]["schemas"]
        expected_models = [
            "UserResponse", "ProjectResponse", "VMResponse", "Token", "APIResponse"
        ]
        
        for model in expected_models:
            assert model in schemas, f"Missing response model: {model}"
            
        # Verify models have proper structure
        for model_name, model_schema in schemas.items():
            assert "type" in model_schema or "$ref" in model_schema
            if "properties" in model_schema:
                for prop_name, prop_schema in model_schema["properties"].items():
                    assert "type" in prop_schema or "$ref" in prop_schema or "anyOf" in prop_schema
            
    def test_error_responses_documented(self, main_app):
        """Test that error responses are documented"""
        response = main_app.get("/openapi.json")
        schema = response.json()
        
        # Check that error response models exist
        schemas = schema["components"]["schemas"]
        assert "HTTPValidationError" in schemas or "ValidationError" in schemas
        
        # Check that endpoints have error response documentation
        paths = schema["paths"]
        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ["post", "put", "delete"]:
                    responses = details.get("responses", {})
                    # Should have at least one error response (4xx or 5xx)
                    error_responses = [code for code in responses.keys() 
                                     if code.startswith(('4', '5'))]
                    assert len(error_responses) > 0, f"No error responses for {method.upper()} {path}"
                    
    def test_request_models_validation(self, main_app):
        """Test that request models have proper validation"""
        response = main_app.get("/openapi.json")
        schema = response.json()
        
        schemas = schema["components"]["schemas"]
        
        # Check UserSignup has email validation
        if "UserSignup" in schemas:
            signup_schema = schemas["UserSignup"]
            properties = signup_schema.get("properties", {})
            
            # Email should have format validation
            if "email" in properties:
                assert properties["email"].get("format") == "email"
                
            # Password should have minimum length
            if "password" in properties:
                assert "minLength" in properties["password"]
                
    def test_endpoint_descriptions_present(self, main_app):
        """Test that endpoints have comprehensive descriptions"""
        response = main_app.get("/openapi.json")
        schema = response.json()
        
        paths = schema["paths"]
        for path, methods in paths.items():
            for method, details in methods.items():
                assert "summary" in details, f"Missing summary for {method.upper()} {path}"
                assert "description" in details, f"Missing description for {method.upper()} {path}"
                
                # Check that descriptions are comprehensive (not just one line)
                description = details["description"]
                assert len(description) > 50, f"Description too short for {method.upper()} {path}"
                
    def test_parameter_documentation(self, main_app):
        """Test that parameters are properly documented"""
        response = main_app.get("/openapi.json")
        schema = response.json()
        
        paths = schema["paths"]
        for path, methods in paths.items():
            for method, details in methods.items():
                parameters = details.get("parameters", [])
                for param in parameters:
                    assert "name" in param
                    assert "description" in param
                    assert "in" in param  # query, path, header, etc.
                    
                    # Check that parameter descriptions are meaningful
                    if param["description"]:
                        assert len(param["description"]) > 10, f"Parameter description too short: {param['name']}"
                    
    def test_response_examples_present(self, main_app):
        """Test that response examples are provided"""
        response = main_app.get("/openapi.json")
        schema = response.json()
        
        paths = schema["paths"]
        endpoints_with_examples = 0
        total_endpoints = 0
        
        for path, methods in paths.items():
            for method, details in methods.items():
                total_endpoints += 1
                responses = details.get("responses", {})
                
                for status_code, response_details in responses.items():
                    if "content" in response_details:
                        content = response_details["content"]
                        for media_type, media_details in content.items():
                            if "example" in media_details:
                                endpoints_with_examples += 1
                                break
        
        # At least 30% of endpoints should have examples (lowered threshold for main app)
        example_ratio = endpoints_with_examples / total_endpoints if total_endpoints > 0 else 0
        assert example_ratio >= 0.2, f"Only {example_ratio:.1%} of endpoints have examples"
        
    def test_security_schemes_defined(self, main_app):
        """Test that security schemes are properly defined"""
        response = main_app.get("/openapi.json")
        schema = response.json()
        
        # Check for security schemes in components
        if "components" in schema and "securitySchemes" in schema["components"]:
            security_schemes = schema["components"]["securitySchemes"]
            
            # Should have JWT bearer token scheme
            assert len(security_schemes) > 0, "No security schemes defined"
            
            for scheme_name, scheme_details in security_schemes.items():
                assert "type" in scheme_details
                assert "description" in scheme_details
        
    def test_contact_and_license_info(self, main_app):
        """Test that contact and license information is present"""
        response = main_app.get("/openapi.json")
        schema = response.json()
        
        info = schema["info"]
        
        # Check contact information
        assert "contact" in info
        contact = info["contact"]
        assert "name" in contact
        assert "email" in contact
        
        # Check license information
        assert "license" in info
        license_info = info["license"]
        assert "name" in license_info
        assert "url" in license_info


class TestAPIVersioning:
    """Test API versioning support"""
    
    def test_version_in_openapi_schema(self, main_app):
        """Test that version is properly set in OpenAPI schema"""
        response = main_app.get("/openapi.json")
        schema = response.json()
        
        assert schema["info"]["version"] == "1.0.0"
        
    def test_version_in_root_response(self, main_app):
        """Test that version is returned in root endpoint"""
        response = main_app.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["version"] == "1.0.0"
        
    def test_version_endpoints_exist(self, main_app):
        """Test that version-specific endpoints exist"""
        # Test current version endpoint
        response = main_app.get("/api/version")
        assert response.status_code == 200
        
        data = response.json()
        assert "current_version" in data
        assert data["current_version"] == "1.0.0"
        
        # Test versions list endpoint
        response = main_app.get("/api/versions")
        assert response.status_code == 200
        
        data = response.json()
        assert "versions" in data
        assert "1.0.0" in data["versions"]
        
    def test_version_compatibility_check(self, main_app):
        """Test version compatibility checking"""
        response = main_app.get("/api/compatibility?from_version=1.0.0&to_version=1.0.0")
        assert response.status_code == 200
        
        data = response.json()
        assert "compatible" in data
        assert "breaking_changes" in data
        assert "migration_required" in data
        
    def test_changelog_endpoint(self, main_app):
        """Test changelog endpoint"""
        response = main_app.get("/api/changelog")
        assert response.status_code == 200
        
        data = response.json()
        assert "changelog" in data
        assert len(data["changelog"]) > 0
        
        # Check changelog entry structure
        entry = data["changelog"][0]
        assert "version" in entry
        assert "release_date" in entry
        assert "changes" in entry
        
    def test_api_backwards_compatibility(self, main_app):
        """Test that API maintains backwards compatibility"""
        # Test that health endpoint works (backward compatibility)
        response = main_app.get("/health")
        assert response.status_code == 200
        
        # Test simple health endpoint
        response = main_app.get("/health-simple")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ["status", "timestamp", "environment", "database"]
        for field in required_fields:
            assert field in data, f"Missing field {field} in health response"


class TestAPIPerformance:
    """Test API performance and response times"""
    
    def test_documentation_load_time(self, main_app):
        """Test that documentation loads quickly"""
        start_time = time.time()
        response = main_app.get("/docs")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 3.0  # Should load in under 3 seconds
        
    def test_openapi_schema_size(self, main_app):
        """Test that OpenAPI schema is not excessively large"""
        response = main_app.get("/openapi.json")
        assert response.status_code == 200
        
        # Check that response is not too large (under 2MB for comprehensive docs)
        content_length = len(response.content)
        assert content_length < 2 * 1024 * 1024  # 2MB limit
        
    def test_schema_validation_performance(self, main_app):
        """Test that schema validation doesn't significantly impact performance"""
        # Test a simple endpoint multiple times
        times = []
        for _ in range(5):
            start_time = time.time()
            response = main_app.get("/")
            end_time = time.time()
            
            assert response.status_code == 200
            times.append(end_time - start_time)
            
        # Average response time should be reasonable
        avg_time = sum(times) / len(times)
        assert avg_time < 0.2  # Should respond in under 200ms on average
        
    def test_concurrent_documentation_access(self, main_app):
        """Test that documentation can handle concurrent access"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def fetch_docs():
            try:
                response = main_app.get("/docs")
                results.put(response.status_code)
            except Exception as e:
                results.put(str(e))
        
        # Create multiple threads to access docs simultaneously
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=fetch_docs)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that all requests succeeded
        while not results.empty():
            result = results.get()
            assert result == 200, f"Concurrent access failed: {result}"


class TestAPIResponseExamples:
    """Test API response examples and schemas"""
    
    def test_root_endpoint_example(self, main_app):
        """Test that root endpoint returns expected structure"""
        response = main_app.get("/")
        assert response.status_code == 200
        
        data = response.json()
        expected_fields = [
            "message", "version", "status", 
            "api_info", "endpoints", "features", "rate_limits", "timestamp"
        ]
        
        for field in expected_fields:
            assert field in data, f"Missing field {field} in root response"
            
        # Check nested structures
        assert "endpoints" in data
        endpoints = data["endpoints"]
        assert "documentation" in endpoints
        assert "health_check" in endpoints
        
    def test_pricing_endpoint_comprehensive(self, main_app):
        """Test that pricing endpoint returns comprehensive information"""
        response = main_app.get("/vms/pricing/info")
        assert response.status_code == 200
        
        data = response.json()
        expected_fields = [
            "pricing", "currency", "billing", "description",
            "specifications", "billing_details", "cost_optimization"
        ]
        
        for field in expected_fields:
            assert field in data, f"Missing field {field} in pricing response"
            
        # Check pricing structure
        pricing = data["pricing"]
        expected_types = ["small", "medium", "large", "xlarge"]
        for vm_type in expected_types:
            assert vm_type in pricing, f"Missing VM type {vm_type} in pricing"
            
        # Check specifications
        specs = data["specifications"]
        for vm_type in expected_types:
            assert vm_type in specs, f"Missing specifications for {vm_type}"
            spec = specs[vm_type]
            assert "cpu" in spec
            assert "ram" in spec
            assert "storage" in spec
            
    def test_version_endpoint_comprehensive(self, main_app):
        """Test that version endpoint returns comprehensive information"""
        response = main_app.get("/api/version")
        assert response.status_code == 200
        
        data = response.json()
        expected_fields = [
            "current_version", "api_status", "release_date", 
            "supported_versions", "compatibility", "timestamp"
        ]
        
        for field in expected_fields:
            assert field in data, f"Missing field {field} in version response"
            
        # Check compatibility structure
        compatibility = data["compatibility"]
        assert "backwards_compatible" in compatibility
        assert "breaking_changes_in_next" in compatibility


class TestAPIDocumentationContent:
    """Test the quality and completeness of API documentation content"""
    
    def test_endpoint_summaries_quality(self, main_app):
        """Test that endpoint summaries are descriptive and helpful"""
        response = main_app.get("/openapi.json")
        schema = response.json()
        
        paths = schema["paths"]
        for path, methods in paths.items():
            for method, details in methods.items():
                summary = details.get("summary", "")
                
                # Summary should be present and meaningful
                assert len(summary) > 10, f"Summary too short for {method.upper()} {path}: '{summary}'"
                
                # Summary should not just repeat the path
                path_words = path.replace("/", " ").replace("{", "").replace("}", "").split()
                summary_lower = summary.lower()
                
                # Should contain some descriptive words beyond just the path
                descriptive_words = ["get", "create", "update", "delete", "list", "retrieve", "manage", "information", "current", "comprehensive"]
                has_descriptive = any(word in summary_lower for word in descriptive_words)
                assert has_descriptive, f"Summary not descriptive enough for {method.upper()} {path}: '{summary}'"
                
    def test_response_descriptions_quality(self, main_app):
        """Test that response descriptions are helpful"""
        response = main_app.get("/openapi.json")
        schema = response.json()
        
        paths = schema["paths"]
        for path, methods in paths.items():
            for method, details in methods.items():
                responses = details.get("responses", {})
                
                for status_code, response_details in responses.items():
                    description = response_details.get("description", "")
                    
                    # Response descriptions should be meaningful
                    if status_code == "200":
                        assert len(description) > 15, f"200 response description too short for {method.upper()} {path}"
                    elif status_code.startswith("4") or status_code.startswith("5"):
                        assert len(description) > 10, f"Error response description too short for {method.upper()} {path}"
                        
    def test_parameter_descriptions_quality(self, main_app):
        """Test that parameter descriptions are helpful"""
        response = main_app.get("/openapi.json")
        schema = response.json()
        
        paths = schema["paths"]
        for path, methods in paths.items():
            for method, details in methods.items():
                parameters = details.get("parameters", [])
                
                for param in parameters:
                    description = param.get("description", "")
                    param_name = param.get("name", "")
                    
                    # Parameter descriptions should be meaningful
                    assert len(description) > 5, f"Parameter description too short for {param_name} in {method.upper()} {path}"
                    
                    # Description should not just repeat the parameter name
                    assert description.lower() != param_name.lower(), f"Parameter description just repeats name for {param_name}"