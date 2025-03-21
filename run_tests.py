#!/usr/bin/env python3
"""
Test Runner for YouTube Shorts Machine

This script runs all tests and generates a comprehensive test report.
"""

import os
import sys
import pytest
import time
import json
from datetime import datetime
from pathlib import Path

# Directories
TEST_DIR = Path(__file__).parent
REPORT_DIR = TEST_DIR / "test-output"
REPORT_DIR.mkdir(exist_ok=True)

# Test files to run
TEST_FILES = [
    "test_api_endpoints.py",
    "test_implemented_features.py"
]

# Additional test files from the codebase
ADDITIONAL_TEST_FILES = [
    "test_core_features.py",
    "test_all_features.py",
    "test_thumbnail_optimization.py",
    "test_scheduler.py",
    "test_social_media.py",
    "test_analytics.py",
    "test_presets.py",
    "test_music_responsive.py",
    "test_export.py"
]

def run_tests():
    """Run all tests and generate reports."""
    print(f"Starting test run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Results dictionary
    results = {
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "total_duration": None,
        "test_files": {},
        "summary": {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0
        }
    }
    
    # Environment information
    results["environment"] = {
        "python_version": sys.version,
        "platform": sys.platform,
        "pytest_version": pytest.__version__
    }
    
    # Run tests for each file
    for test_file in TEST_FILES:
        if not Path(test_file).exists():
            print(f"Test file {test_file} not found, skipping.")
            continue
        
        print(f"\n{'='*80}\nRunning tests from {test_file}\n{'='*80}")
        
        # Run test with pytest
        start_time = time.time()
        exit_code = pytest.main([
            "-v",
            "--junitxml", str(REPORT_DIR / f"{Path(test_file).stem}_results.xml"),
            test_file
        ])
        end_time = time.time()
        
        # Parse run information
        run_info = {
            "exit_code": exit_code,
            "duration": end_time - start_time,
            "status": "success" if exit_code == 0 else "failure"
        }
        
        results["test_files"][test_file] = run_info
    
    # Try to run additional tests if they exist
    for test_file in ADDITIONAL_TEST_FILES:
        if Path(test_file).exists():
            print(f"\n{'='*80}\nRunning tests from {test_file}\n{'='*80}")
            
            # Run test with pytest
            start_time = time.time()
            exit_code = pytest.main([
                "-v",
                "--junitxml", str(REPORT_DIR / f"{Path(test_file).stem}_results.xml"),
                test_file
            ])
            end_time = time.time()
            
            # Parse run information
            run_info = {
                "exit_code": exit_code,
                "duration": end_time - start_time,
                "status": "success" if exit_code == 0 else "failure"
            }
            
            results["test_files"][test_file] = run_info
    
    # Calculate summary information
    total_tests = 0
    passed = 0
    failed = 0
    skipped = 0
    errors = 0
    
    # For real stats, we'd parse the JUnit XML files here
    # For now, just use simple heuristics based on exit codes
    for file_name, run_info in results["test_files"].items():
        if run_info["exit_code"] == 0:
            passed += 1
        elif run_info["exit_code"] == 1:
            failed += 1
        elif run_info["exit_code"] == 2:
            errors += 1
        elif run_info["exit_code"] == 5:
            skipped += 1
            
    total_tests = len(results["test_files"])
    
    results["summary"] = {
        "total_tests": total_tests,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "errors": errors
    }
    
    # Set end time
    results["end_time"] = datetime.now().isoformat()
    results["total_duration"] = sum(info["duration"] for info in results["test_files"].values())
    
    # Write results to JSON file
    with open(REPORT_DIR / "test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Generate simple HTML report
    generate_html_report(results)
    
    return results

def generate_html_report(results):
    """Generate an HTML report from test results."""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>YouTube Shorts Machine - Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        .summary {{ display: flex; margin: 20px 0; }}
        .summary-box {{ 
            padding: 15px; margin: 0 10px; border-radius: 5px; 
            text-align: center; min-width: 120px; 
        }}
        .passed {{ background-color: #d4edda; color: #155724; }}
        .failed {{ background-color: #f8d7da; color: #721c24; }}
        .skipped {{ background-color: #fff3cd; color: #856404; }}
        .errors {{ background-color: #d6d8d9; color: #1b1e21; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
        tr.success {{ background-color: #f6fff6; }}
        tr.failure {{ background-color: #fff6f6; }}
        .duration {{ font-style: italic; color: #666; }}
    </style>
</head>
<body>
    <h1>YouTube Shorts Machine - Test Report</h1>
    <p>Test run completed at {datetime.fromisoformat(results['end_time']).strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p class="duration">Total duration: {results['total_duration']:.2f} seconds</p>
    
    <h2>Summary</h2>
    <div class="summary">
        <div class="summary-box">
            <h3>Total Tests</h3>
            <p>{results['summary']['total_tests']}</p>
        </div>
        <div class="summary-box passed">
            <h3>Passed</h3>
            <p>{results['summary']['passed']}</p>
        </div>
        <div class="summary-box failed">
            <h3>Failed</h3>
            <p>{results['summary']['failed']}</p>
        </div>
        <div class="summary-box skipped">
            <h3>Skipped</h3>
            <p>{results['summary']['skipped']}</p>
        </div>
        <div class="summary-box errors">
            <h3>Errors</h3>
            <p>{results['summary']['errors']}</p>
        </div>
    </div>
    
    <h2>Test Files</h2>
    <table>
        <tr>
            <th>File</th>
            <th>Status</th>
            <th>Duration</th>
            <th>Exit Code</th>
        </tr>
    """
    
    for file_name, info in results["test_files"].items():
        status_class = "success" if info["status"] == "success" else "failure"
        html += f"""
        <tr class="{status_class}">
            <td>{file_name}</td>
            <td>{info["status"]}</td>
            <td>{info["duration"]:.2f} seconds</td>
            <td>{info["exit_code"]}</td>
        </tr>
        """
    
    html += """
    </table>
    
    <h2>Environment</h2>
    <table>
        <tr>
            <th>Key</th>
            <th>Value</th>
        </tr>
    """
    
    for key, value in results["environment"].items():
        html += f"""
        <tr>
            <td>{key}</td>
            <td>{value}</td>
        </tr>
        """
    
    html += """
    </table>
</body>
</html>
    """
    
    with open(REPORT_DIR / "test_report.html", "w") as f:
        f.write(html)
    
    print(f"\nTest report generated at {REPORT_DIR / 'test_report.html'}")

if __name__ == "__main__":
    results = run_tests()
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY:")
    print(f"Total tests: {results['summary']['total_tests']}")
    print(f"Passed: {results['summary']['passed']}")
    print(f"Failed: {results['summary']['failed']}")
    print(f"Skipped: {results['summary']['skipped']}")
    print(f"Errors: {results['summary']['errors']}")
    print("="*80)
    
    # Exit with appropriate exit code
    sys.exit(1 if results['summary']['failed'] > 0 or results['summary']['errors'] > 0 else 0) 