#!/usr/bin/env python3
"""
Test runner script for Zentry Cloud API
Provides convenient ways to run different test suites
"""

import sys
import subprocess
import argparse
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle the result"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"\n❌ Command not found: {cmd[0]}")
        print("Make sure pytest is installed: pip install pytest")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run Zentry Cloud API tests")
    parser.add_argument(
        "--suite", 
        choices=["all", "unit", "integration", "system", "auth", "vm", "project", "api", "fast", "slow"],
        default="all",
        help="Test suite to run"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true",
        help="Run tests with coverage report"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--parallel", "-n",
        type=int,
        help="Run tests in parallel (requires pytest-xdist)"
    )
    parser.add_argument(
        "--file",
        help="Run specific test file"
    )
    parser.add_argument(
        "--function",
        help="Run specific test function"
    )
    
    args = parser.parse_args()
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if args.verbose:
        cmd.append("-vv")
    
    # Add coverage
    if args.coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term-missing"])
    
    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    
    # Add specific file or function
    if args.file:
        if args.function:
            cmd.append(f"{args.file}::{args.function}")
        else:
            cmd.append(args.file)
    elif args.function:
        cmd.extend(["-k", args.function])
    
    # Add test suite selection
    if args.suite != "all":
        if args.suite == "fast":
            cmd.extend(["-m", "not slow"])
        elif args.suite == "slow":
            cmd.extend(["-m", "slow"])
        else:
            cmd.extend(["-m", args.suite])
    
    # Run the tests
    success = run_command(cmd, f"Test suite: {args.suite}")
    
    if success:
        print(f"\n🎉 All tests passed!")
        if args.coverage:
            print("📊 Coverage report generated in htmlcov/index.html")
    else:
        print(f"\n💥 Some tests failed!")
        sys.exit(1)

def run_quick_tests():
    """Run a quick subset of tests for development"""
    print("Running quick development tests...")
    
    quick_tests = [
        "tests/test_authentication.py::TestUserSignup::test_successful_signup",
        "tests/test_projects.py::TestProjectCreation::test_create_project_success", 
        "tests/test_vms.py::TestVMCreation::test_create_vm_success",
        "tests/test_api_documentation.py::TestAPIDocumentation::test_openapi_schema_generation"
    ]
    
    cmd = ["python", "-m", "pytest", "-v"] + quick_tests
    return run_command(cmd, "Quick development tests")

def run_smoke_tests():
    """Run smoke tests to verify basic functionality"""
    print("Running smoke tests...")
    
    smoke_tests = [
        "tests/test_system.py::TestSystemHealth::test_root_endpoint",
        "tests/test_system.py::TestSystemHealth::test_health_check_endpoint",
        "tests/test_authentication.py::TestUserSignup::test_successful_signup",
        "tests/test_integration.py::TestUserWorkflow::test_complete_user_journey"
    ]
    
    cmd = ["python", "-m", "pytest", "-v"] + smoke_tests
    return run_command(cmd, "Smoke tests")

def check_test_environment():
    """Check if the test environment is properly set up"""
    print("Checking test environment...")
    
    # Check if pytest is available
    try:
        result = subprocess.run(["python", "-m", "pytest", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Pytest available: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Pytest not available. Install with: pip install pytest")
        return False
    
    # Check if test files exist
    test_files = [
        "tests/test_authentication.py",
        "tests/test_projects.py", 
        "tests/test_vms.py",
        "tests/test_api_documentation.py",
        "tests/test_integration.py",
        "tests/test_system.py"
    ]
    
    missing_files = []
    for test_file in test_files:
        if not Path(test_file).exists():
            missing_files.append(test_file)
    
    if missing_files:
        print(f"❌ Missing test files: {missing_files}")
        return False
    else:
        print("✅ All test files present")
    
    # Check if conftest.py exists
    if Path("tests/conftest.py").exists():
        print("✅ Test configuration file present")
    else:
        print("❌ Missing tests/conftest.py")
        return False
    
    print("✅ Test environment looks good!")
    return True

if __name__ == "__main__":
    # Special commands
    if len(sys.argv) > 1:
        if sys.argv[1] == "quick":
            success = run_quick_tests()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "smoke":
            success = run_smoke_tests()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "check":
            success = check_test_environment()
            sys.exit(0 if success else 1)
    
    # Run main test runner
    main()