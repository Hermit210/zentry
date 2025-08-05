#!/usr/bin/env python3
"""
Test script for enhanced data models and validation
"""

import sys
from datetime import datetime, timezone
from decimal import Decimal
from models import *

def test_basic_models():
    """Test basic model creation and validation"""
    print("Testing basic models...")
    
    # Test user model
    user = UserResponse(
        id='123e4567-e89b-12d3-a456-426614174000',
        email='test@example.com',
        name='Test User',
        credits=100.0,
        created_at=datetime.now(timezone.utc)
    )
    assert user.email == 'test@example.com'
    print("✓ User model creation passed")
    
    # Test VM model with auto-populated specs
    vm = VMResponse(
        id='123e4567-e89b-12d3-a456-426614174001',
        name='test-vm',
        instance_type=InstanceType.SMALL,
        image=VMImage.UBUNTU_22_04,
        status=VMStatus.RUNNING,
        user_id='123e4567-e89b-12d3-a456-426614174000',
        project_id='123e4567-e89b-12d3-a456-426614174002',
        created_at=datetime.now(timezone.utc)
    )
    assert vm.specs['cpu'] == '1 vCPU'
    assert vm.cost_per_hour == 0.05
    print("✓ VM model with specs population passed")

def test_enhanced_validation():
    """Test enhanced validation features"""
    print("\nTesting enhanced validation...")
    
    # Test reserved name validation
    try:
        VMCreateEnhanced(
            name='admin',
            instance_type=InstanceType.SMALL,
            image=VMImage.UBUNTU_22_04,
            project_id='123e4567-e89b-12d3-a456-426614174000'
        )
        assert False, "Should have failed for reserved name"
    except ValueError:
        print("✓ Reserved name validation passed")
    
    # Test tag validation
    try:
        VMCreateEnhanced(
            name='test-vm',
            instance_type=InstanceType.SMALL,
            image=VMImage.UBUNTU_22_04,
            project_id='123e4567-e89b-12d3-a456-426614174000',
            tags={f'tag{i}': f'value{i}' for i in range(15)}
        )
        assert False, "Should have failed for too many tags"
    except ValueError:
        print("✓ Tag limit validation passed")
    
    # Test validation utilities
    utils = EnhancedValidationUtils()
    
    # Credit validation
    errors = utils.validate_credit_requirements(5.0, 10.0, 'VM creation')
    assert len(errors) == 1
    print("✓ Credit validation passed")
    
    # State transition validation
    errors = utils.validate_vm_state_transition(VMStatus.TERMINATED, VMStatus.RUNNING)
    assert len(errors) == 1
    print("✓ State transition validation passed")

def test_comprehensive_validation():
    """Test comprehensive validation system"""
    print("\nTesting comprehensive validation...")
    
    validator = ComprehensiveModelValidator()
    
    # Create test data
    user = UserResponse(
        id='123e4567-e89b-12d3-a456-426614174000',
        email='test@example.com',
        name='Test User',
        credits=0.01,  # Very low credits
        vm_count=49,   # Near limit
        created_at=datetime.now(timezone.utc)
    )
    
    project = ProjectResponse(
        id='123e4567-e89b-12d3-a456-426614174001',
        name='Test Project',
        user_id='123e4567-e89b-12d3-a456-426614174000',
        vm_count=19,   # Near limit
        created_at=datetime.now(timezone.utc)
    )
    
    vm_data = VMCreateEnhanced(
        name='test-vm',
        instance_type=InstanceType.LARGE,  # Expensive
        image=VMImage.UBUNTU_22_04,
        project_id='123e4567-e89b-12d3-a456-426614174001'
    )
    
    errors = validator.validate_vm_creation(vm_data, user, project)
    assert len(errors) > 0  # Should have credit errors
    print("✓ Comprehensive VM validation passed")

def test_model_integrity():
    """Test model integrity checking"""
    print("\nTesting model integrity...")
    
    checker = ModelIntegrityChecker()
    
    # Test valid user
    user = UserResponse(
        id='123e4567-e89b-12d3-a456-426614174000',
        email='test@example.com',
        name='Test User',
        credits=100.0,
        vm_count=5,
        active_vm_count=3,
        created_at=datetime.now(timezone.utc)
    )
    
    errors = checker.check_user_integrity(user)
    assert len(errors) == 0
    print("✓ User integrity check passed")
    
    # Test invalid user (negative credits)
    user.credits = -10.0
    errors = checker.check_user_integrity(user)
    assert len(errors) > 0
    print("✓ User integrity validation passed")

def test_serialization():
    """Test enhanced serialization features"""
    print("\nTesting serialization...")
    
    user = UserResponseEnhanced(
        id='123e4567-e89b-12d3-a456-426614174000',
        email='test@example.com',
        name='Test User',
        credits=123.456789,
        created_at=datetime.now(timezone.utc)
    )
    
    # Test default serialization
    serialized = user.serialize()
    assert isinstance(serialized, dict)
    assert serialized['credits'] == 123.46  # Rounded to 2 decimal places
    print("✓ Default serialization passed")
    
    # Test custom serialization
    config = SerializationConfig(decimal_places=4)
    serialized = user.serialize(config)
    assert serialized['credits'] == 123.4568
    print("✓ Custom serialization passed")

def test_model_conversion():
    """Test model conversion utilities"""
    print("\nTesting model conversion...")
    
    converter = ModelConverter()
    
    # Test user conversion
    user_db = UserDB(
        id='123e4567-e89b-12d3-a456-426614174000',
        email='test@example.com',
        name='Test User',
        hashed_password='hashed_password',
        credits=Decimal('100.50'),
        total_spent=Decimal('25.75'),
        is_active=True,
        role='user',
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        last_login=None
    )
    
    user_response = converter.user_db_to_response(user_db)
    assert user_response.credits == 100.5
    assert user_response.email == 'test@example.com'
    print("✓ User model conversion passed")

def test_relationships():
    """Test model relationships definition"""
    print("\nTesting model relationships...")
    
    relationships = ModelRelationships()
    assert len(relationships.relationships) > 0
    
    # Check that we have the expected relationships
    table_names = [rel.table for rel in relationships.relationships]
    assert 'projects' in table_names
    assert 'vms' in table_names
    assert 'billing_records' in table_names
    assert 'vm_metrics' in table_names
    print("✓ Model relationships definition passed")

def main():
    """Run all tests"""
    print("Running enhanced models and validation tests...\n")
    
    try:
        test_basic_models()
        test_enhanced_validation()
        test_comprehensive_validation()
        test_model_integrity()
        test_serialization()
        test_model_conversion()
        test_relationships()
        
        print("\n🎉 All tests passed! Enhanced models and validation are working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()