#!/usr/bin/env python3
"""
Test runner script for the local music generator project.
Runs both backend and frontend tests with coverage reporting.
"""

import subprocess
import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Tuple
import argparse

def run_command(cmd: List[str], cwd: str = None) -> Tuple[bool, str]:
    """Run a command and return success status and output"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)

def run_backend_tests(args) -> Dict:
    """Run backend tests with pytest"""
    print("🧪 Running backend tests...")
    
    backend_dir = Path(__file__).parent / "local-music-generator" / "backend"
    
    # Prepare pytest command
    cmd = ["python", "-m", "pytest"]
    
    if args.verbose:
        cmd.append("-v")
    
    if args.coverage:
        cmd.extend([
            "--cov=.",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-report=json:coverage.json"
        ])
    
    if args.parallel:
        cmd.extend(["-n", "auto"])
    
    if args.markers:
        cmd.extend(["-m", args.markers])
    
    if args.test_file:
        cmd.append(args.test_file)
    
    # Run tests
    success, output = run_command(cmd, str(backend_dir))
    
    # Parse coverage if available
    coverage_data = None
    if args.coverage:
        coverage_file = backend_dir / "coverage.json"
        if coverage_file.exists():
            try:
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
            except:
                pass
    
    return {
        "success": success,
        "output": output,
        "coverage": coverage_data,
        "type": "backend"
    }

def run_frontend_tests(args) -> Dict:
    """Run frontend tests with Jest"""
    print("🧪 Running frontend tests...")
    
    frontend_dir = Path(__file__).parent / "local-music-generator" / "frontend"
    
    # Prepare Jest command
    cmd = ["npm", "test"]
    
    if args.coverage:
        cmd.extend(["--", "--coverage", "--watchAll=false"])
    else:
        cmd.extend(["--", "--watchAll=false"])
    
    if args.verbose:
        cmd.extend(["--verbose"])
    
    if args.test_file:
        cmd.extend(["--testNamePattern", args.test_file])
    
    # Run tests
    success, output = run_command(cmd, str(frontend_dir))
    
    # Parse coverage if available
    coverage_data = None
    if args.coverage:
        coverage_file = frontend_dir / "coverage" / "coverage-summary.json"
        if coverage_file.exists():
            try:
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
            except:
                pass
    
    return {
        "success": success,
        "output": output,
        "coverage": coverage_data,
        "type": "frontend"
    }

def run_integration_tests(args) -> Dict:
    """Run integration tests"""
    print("🧪 Running integration tests...")
    
    backend_dir = Path(__file__).parent / "local-music-generator" / "backend"
    
    cmd = [
        "python", "-m", "pytest",
        "-m", "integration",
        "--verbose" if args.verbose else "",
    ]
    cmd = [arg for arg in cmd if arg]  # Remove empty strings
    
    success, output = run_command(cmd, str(backend_dir))
    
    return {
        "success": success,
        "output": output,
        "type": "integration"
    }

def run_performance_tests(args) -> Dict:
    """Run performance tests"""
    print("🧪 Running performance tests...")
    
    backend_dir = Path(__file__).parent / "local-music-generator" / "backend"
    
    cmd = [
        "python", "-m", "pytest",
        "-m", "performance",
        "--verbose" if args.verbose else "",
    ]
    cmd = [arg for arg in cmd if arg]  # Remove empty strings
    
    success, output = run_command(cmd, str(backend_dir))
    
    return {
        "success": success,
        "output": output,
        "type": "performance"
    }

def print_coverage_summary(result: Dict):
    """Print coverage summary"""
    if not result.get("coverage"):
        return
    
    print(f"\n📊 Coverage Summary ({result['type']}):")
    print("-" * 40)
    
    if result["type"] == "backend":
        # Python coverage format
        totals = result["coverage"].get("totals", {})
        print(f"Lines: {totals.get('percent_covered', 0):.1f}%")
        print(f"Functions: {totals.get('percent_covered_display', 'N/A')}")
        print(f"Branches: {totals.get('percent_covered_display', 'N/A')}")
        
    elif result["type"] == "frontend":
        # Jest coverage format
        total = result["coverage"].get("total", {})
        print(f"Lines: {total.get('lines', {}).get('pct', 0)}%")
        print(f"Functions: {total.get('functions', {}).get('pct', 0)}%")
        print(f"Branches: {total.get('branches', {}).get('pct', 0)}%")
        print(f"Statements: {total.get('statements', {}).get('pct', 0)}%")

def print_test_summary(results: List[Dict]):
    """Print overall test summary"""
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["success"])
    failed_tests = total_tests - passed_tests
    
    print(f"Total test suites: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    
    if failed_tests > 0:
        print("\n❌ Failed test suites:")
        for result in results:
            if not result["success"]:
                print(f"  - {result['type']}")
    
    print("\n" + "="*60)
    
    for result in results:
        print_coverage_summary(result)
    
    return failed_tests == 0

def main():
    parser = argparse.ArgumentParser(description="Run tests for the local music generator")
    parser.add_argument("--backend", action="store_true", help="Run only backend tests")
    parser.add_argument("--frontend", action="store_true", help="Run only frontend tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage reports")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--markers", "-m", help="Run tests with specific markers")
    parser.add_argument("--test-file", "-t", help="Run specific test file or pattern")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first failure")
    
    args = parser.parse_args()
    
    # Default to running all tests if no specific test type is selected
    if not any([args.backend, args.frontend, args.integration, args.performance]):
        args.backend = True
        args.frontend = True
    
    results = []
    
    try:
        if args.backend:
            result = run_backend_tests(args)
            results.append(result)
            if args.fail_fast and not result["success"]:
                print("❌ Backend tests failed, stopping due to --fail-fast")
                sys.exit(1)
        
        if args.frontend:
            result = run_frontend_tests(args)
            results.append(result)
            if args.fail_fast and not result["success"]:
                print("❌ Frontend tests failed, stopping due to --fail-fast")
                sys.exit(1)
        
        if args.integration:
            result = run_integration_tests(args)
            results.append(result)
            if args.fail_fast and not result["success"]:
                print("❌ Integration tests failed, stopping due to --fail-fast")
                sys.exit(1)
        
        if args.performance:
            result = run_performance_tests(args)
            results.append(result)
            if args.fail_fast and not result["success"]:
                print("❌ Performance tests failed, stopping due to --fail-fast")
                sys.exit(1)
        
        # Print individual test outputs if verbose
        if args.verbose:
            for result in results:
                print(f"\n{'='*60}")
                print(f"{result['type'].upper()} TEST OUTPUT")
                print(f"{'='*60}")
                print(result["output"])
        
        # Print summary
        all_passed = print_test_summary(results)
        
        if all_passed:
            print("🎉 All tests passed!")
            sys.exit(0)
        else:
            print("❌ Some tests failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()