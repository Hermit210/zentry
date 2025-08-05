import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from services.auth_service import AuthService
from services.vm_service import VMService
from services.project_service import ProjectService
from services.billing_service import BillingService
from services.monitoring_service import MonitoringService
from services.user_service import UserService
from services.base_service import ServiceError, ValidationError, NotFoundError, InsufficientCreditsError
from models import (
    UserSignup, UserLogin, UserUpdate, VMCreate, ProjectCreate, 
    InstanceType, VMImage, VMStatus, BillingActionType, VMMetricsCreate
)

class TestAuthService:
    """Test cases for AuthService"""
    
    @pytest.fixture
    def auth_service(self):
        return AuthService()
    
    @pytest.fixture
    def mock_user_data(self):
        return {
            "id": "test-user-id",
            "email": "test@example.com",
            "name": "Test User",
            "hashed_password": "hashed_password",
            "credits": 50.0,
            "total_spent": 0.0,
            "vm_count": 0,
            "project_count": 0,
            "active_vm_count": 0,
            "is_active": True,
            "role": "user",
            "created_at": datetime.utcnow(),
            "updated_at": None,
            "last_login": None
        }
    
    @pytest.mark.asyncio
    async def test_signup_success(self, auth_service, mock_user_data):
        """Test successful user signup"""
        signup_data = UserSignup(
            email="test@example.com",
            name="Test User",
            password="password123"
        )
        
        with patch.object(auth_service, '_user_exists', return_value=False), \
             patch.object(auth_service, '_create_user', return_value=mock_user_data), \
             patch.object(auth_service, 'log_audit_event', new_callable=AsyncMock), \
             patch('services.auth_service.get_password_hash', return_value="hashed_password"), \
             patch('services.auth_service.create_access_token', return_value="test_token"):
            
            result = await auth_service.signup(signup_data)
            
            assert result.access_token == "test_token"
            assert result.user.email == "test@example.com"
            assert result.user.name == "Test User"
    
    @pytest.mark.asyncio
    async def test_signup_user_exists(self, auth_service):
        """Test signup with existing user"""
        signup_data = UserSignup(
            email="test@example.com",
            name="Test User",
            password="password123"
        )
        
        with patch.object(auth_service, '_user_exists', return_value=True):
            with pytest.raises(ValidationError) as exc_info:
                await auth_service.signup(signup_data)
            
            assert "Email already registered" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, mock_user_data):
        """Test successful user login"""
        login_data = UserLogin(
            email="test@example.com",
            password="password123"
        )
        
        with patch.object(auth_service, '_get_user_by_email', return_value=mock_user_data), \
             patch.object(auth_service, '_update_last_login', new_callable=AsyncMock), \
             patch.object(auth_service, 'log_audit_event', new_callable=AsyncMock), \
             patch('services.auth_service.check_rate_limit', return_value=True), \
             patch('services.auth_service.verify_password', return_value=True), \
             patch('services.auth_service.clear_failed_login'), \
             patch('services.auth_service.create_access_token', return_value="test_token"):
            
            result = await auth_service.login(login_data)
            
            assert result.access_token == "test_token"
            assert result.user.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, auth_service):
        """Test login with invalid credentials"""
        login_data = UserLogin(
            email="test@example.com",
            password="wrong_password"
        )
        
        with patch.object(auth_service, '_get_user_by_email', return_value=None), \
             patch('services.auth_service.check_rate_limit', return_value=True), \
             patch('services.auth_service.record_failed_login'):
            
            with pytest.raises(ValidationError) as exc_info:
                await auth_service.login(login_data)
            
            assert "Invalid email or password" in str(exc_info.value)

class TestVMService:
    """Test cases for VMService"""
    
    @pytest.fixture
    def vm_service(self):
        return VMService()
    
    @pytest.fixture
    def mock_user(self):
        from models import UserResponse
        return UserResponse(
            id="test-user-id",
            email="test@example.com",
            name="Test User",
            credits=100.0,
            created_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def mock_vm_data(self):
        return VMCreate(
            name="test-vm",
            instance_type=InstanceType.SMALL,
            image=VMImage.UBUNTU_22_04,
            project_id="test-project-id"
        )
    
    @pytest.mark.asyncio
    async def test_create_vm_success(self, vm_service, mock_user, mock_vm_data):
        """Test successful VM creation"""
        mock_vm_record = {
            "id": "test-vm-id",
            "name": "test-vm",
            "instance_type": "small",
            "image": "ubuntu-22.04",
            "status": "running",
            "ip_address": "192.168.1.10",
            "user_id": "test-user-id",
            "project_id": "test-project-id",
            "cost_per_hour": 0.05,
            "uptime_hours": 0.0,
            "total_cost": 0.05,
            "created_at": datetime.utcnow()
        }
        
        with patch.object(vm_service, 'validate_user_ownership', return_value=True), \
             patch.object(vm_service, '_vm_name_exists_in_project', return_value=False), \
             patch.object(vm_service, '_create_vm_record', return_value=mock_vm_record), \
             patch.object(vm_service, 'update_user_credits', return_value=True), \
             patch.object(vm_service, '_update_vm_status', new_callable=AsyncMock), \
             patch.object(vm_service, 'log_audit_event', new_callable=AsyncMock), \
             patch.object(vm_service.billing_service, 'record_transaction', new_callable=AsyncMock):
            
            result = await vm_service.create_vm(mock_vm_data, mock_user)
            
            assert result.name == "test-vm"
            assert result.instance_type == InstanceType.SMALL
            assert result.status == VMStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_create_vm_insufficient_credits(self, vm_service, mock_vm_data):
        """Test VM creation with insufficient credits"""
        from models import UserResponse
        poor_user = UserResponse(
            id="test-user-id",
            email="test@example.com",
            name="Test User",
            credits=0.01,  # Insufficient credits
            created_at=datetime.utcnow()
        )
        
        with patch.object(vm_service, 'validate_user_ownership', return_value=True), \
             patch.object(vm_service, '_vm_name_exists_in_project', return_value=False):
            
            with pytest.raises(InsufficientCreditsError):
                await vm_service.create_vm(mock_vm_data, poor_user)

class TestProjectService:
    """Test cases for ProjectService"""
    
    @pytest.fixture
    def project_service(self):
        return ProjectService()
    
    @pytest.fixture
    def mock_project_data(self):
        return ProjectCreate(
            name="test-project",
            description="Test project description"
        )
    
    @pytest.mark.asyncio
    async def test_create_project_success(self, project_service, mock_project_data):
        """Test successful project creation"""
        mock_project_record = {
            "id": "test-project-id",
            "name": "test-project",
            "description": "Test project description",
            "user_id": "test-user-id",
            "vm_count": 0,
            "active_vm_count": 0,
            "total_cost": 0.0,
            "created_at": datetime.utcnow(),
            "updated_at": None
        }
        
        with patch.object(project_service, '_project_name_exists_for_user', return_value=False), \
             patch.object(project_service, '_create_project_record', return_value=mock_project_record), \
             patch.object(project_service, 'log_audit_event', new_callable=AsyncMock):
            
            result = await project_service.create_project(mock_project_data, "test-user-id")
            
            assert result.name == "test-project"
            assert result.description == "Test project description"
            assert result.user_id == "test-user-id"
    
    @pytest.mark.asyncio
    async def test_create_project_name_exists(self, project_service, mock_project_data):
        """Test project creation with existing name"""
        with patch.object(project_service, '_project_name_exists_for_user', return_value=True):
            
            with pytest.raises(ValidationError) as exc_info:
                await project_service.create_project(mock_project_data, "test-user-id")
            
            assert "already exists" in str(exc_info.value)

class TestBillingService:
    """Test cases for BillingService"""
    
    @pytest.fixture
    def billing_service(self):
        return BillingService()
    
    @pytest.mark.asyncio
    async def test_record_transaction_success(self, billing_service):
        """Test successful transaction recording"""
        mock_billing_record = {
            "id": "test-billing-id",
            "user_id": "test-user-id",
            "vm_id": "test-vm-id",
            "action_type": "vm_create",
            "amount": 0.05,
            "description": "VM creation cost",
            "created_at": datetime.utcnow()
        }
        
        with patch.object(billing_service, '_create_billing_record', return_value=mock_billing_record), \
             patch.object(billing_service, 'log_audit_event', new_callable=AsyncMock):
            
            result = await billing_service.record_transaction(
                user_id="test-user-id",
                action_type="vm_create",
                amount=0.05,
                description="VM creation cost",
                vm_id="test-vm-id"
            )
            
            assert result.user_id == "test-user-id"
            assert result.amount == 0.05
            assert result.action_type == "vm_create"
    
    @pytest.mark.asyncio
    async def test_add_credits_success(self, billing_service):
        """Test successful credit addition"""
        with patch.object(billing_service, 'get_user_credits', return_value=50.0), \
             patch.object(billing_service, 'update_user_credits', return_value=True), \
             patch.object(billing_service, 'record_transaction', new_callable=AsyncMock) as mock_record:
            
            await billing_service.add_credits("test-user-id", 25.0, "Credit addition")
            
            mock_record.assert_called_once()
            args = mock_record.call_args[1]
            assert args['amount'] == 25.0
            assert args['action_type'] == BillingActionType.CREDIT_ADD.value

class TestMonitoringService:
    """Test cases for MonitoringService"""
    
    @pytest.fixture
    def monitoring_service(self):
        return MonitoringService()
    
    @pytest.fixture
    def mock_metrics_data(self):
        return VMMetricsCreate(
            cpu_usage=50.0,
            memory_usage=60.0,
            disk_usage=30.0,
            network_in=100.0,
            network_out=80.0
        )
    
    @pytest.mark.asyncio
    async def test_record_vm_metrics_success(self, monitoring_service, mock_metrics_data):
        """Test successful VM metrics recording"""
        mock_metrics_record = {
            "id": "test-metrics-id",
            "vm_id": "test-vm-id",
            "cpu_usage": 50.0,
            "memory_usage": 60.0,
            "disk_usage": 30.0,
            "network_in": 100.0,
            "network_out": 80.0,
            "recorded_at": datetime.utcnow()
        }
        
        with patch.object(monitoring_service, 'validate_user_ownership', return_value=True), \
             patch.object(monitoring_service, '_create_metrics_record', return_value=mock_metrics_record), \
             patch.object(monitoring_service, '_cleanup_old_metrics', new_callable=AsyncMock):
            
            result = await monitoring_service.record_vm_metrics(
                "test-vm-id", mock_metrics_data, "test-user-id"
            )
            
            assert result.vm_id == "test-vm-id"
            assert result.cpu_usage == 50.0
            assert result.memory_usage == 60.0
    
    @pytest.mark.asyncio
    async def test_record_vm_metrics_invalid_data(self, monitoring_service):
        """Test VM metrics recording with invalid data"""
        invalid_metrics = VMMetricsCreate(
            cpu_usage=150.0,  # Invalid: > 100
            memory_usage=60.0,
            disk_usage=30.0,
            network_in=100.0,
            network_out=80.0
        )
        
        with patch.object(monitoring_service, 'validate_user_ownership', return_value=True):
            
            with pytest.raises(ValidationError) as exc_info:
                await monitoring_service.record_vm_metrics(
                    "test-vm-id", invalid_metrics, "test-user-id"
                )
            
            assert "CPU usage must be between 0 and 100" in str(exc_info.value)

class TestUserService:
    """Test cases for UserService"""
    
    @pytest.fixture
    def user_service(self):
        return UserService()
    
    @pytest.fixture
    def mock_user_record(self):
        return {
            "id": "test-user-id",
            "email": "test@example.com",
            "name": "Test User",
            "credits": 50.0,
            "total_spent": 10.0,
            "vm_count": 2,
            "project_count": 1,
            "active_vm_count": 1,
            "is_active": True,
            "role": "user",
            "created_at": datetime.utcnow(),
            "updated_at": None,
            "last_login": None
        }
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_service, mock_user_record):
        """Test successful user retrieval by ID"""
        with patch.object(user_service, '_get_user_record', return_value=mock_user_record), \
             patch.object(user_service, '_calculate_user_stats', return_value={}):
            
            result = await user_service.get_user_by_id("test-user-id")
            
            assert result.id == "test-user-id"
            assert result.email == "test@example.com"
            assert result.name == "Test User"
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_service):
        """Test user retrieval with non-existent ID"""
        with patch.object(user_service, '_get_user_record', return_value=None):
            
            with pytest.raises(NotFoundError) as exc_info:
                await user_service.get_user_by_id("non-existent-id")
            
            assert "User not found" in str(exc_info.value)

class TestServiceIntegration:
    """Integration tests for service interactions"""
    
    @pytest.mark.asyncio
    async def test_vm_creation_with_billing(self):
        """Test VM creation integrates properly with billing service"""
        vm_service = VMService()
        
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.credits = 100.0
        
        mock_vm_data = VMCreate(
            name="integration-test-vm",
            instance_type=InstanceType.SMALL,
            image=VMImage.UBUNTU_22_04,
            project_id="test-project-id"
        )
        
        mock_vm_record = {
            "id": "test-vm-id",
            "name": "integration-test-vm",
            "instance_type": "small",
            "image": "ubuntu-22.04",
            "status": "running",
            "ip_address": "192.168.1.10",
            "user_id": "test-user-id",
            "project_id": "test-project-id",
            "cost_per_hour": 0.05,
            "uptime_hours": 0.0,
            "total_cost": 0.05,
            "created_at": datetime.utcnow()
        }
        
        with patch.object(vm_service, 'validate_user_ownership', return_value=True), \
             patch.object(vm_service, '_vm_name_exists_in_project', return_value=False), \
             patch.object(vm_service, '_create_vm_record', return_value=mock_vm_record), \
             patch.object(vm_service, 'update_user_credits', return_value=True), \
             patch.object(vm_service, '_update_vm_status', new_callable=AsyncMock), \
             patch.object(vm_service, 'log_audit_event', new_callable=AsyncMock), \
             patch.object(vm_service.billing_service, 'record_transaction', new_callable=AsyncMock) as mock_billing:
            
            result = await vm_service.create_vm(mock_vm_data, mock_user)
            
            # Verify VM was created
            assert result.name == "integration-test-vm"
            
            # Verify billing transaction was recorded
            mock_billing.assert_called_once()
            billing_args = mock_billing.call_args[1]
            assert billing_args['action_type'] == "vm_create"
            assert billing_args['amount'] == 0.05

if __name__ == "__main__":
    pytest.main([__file__])