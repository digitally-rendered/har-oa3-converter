"""Script to analyze coverage gaps and run targeted tests."""

import os
import sys
import json
from pathlib import Path
import subprocess
import coverage


def run_coverage_analysis():
    """Run coverage analysis to identify gaps."""
    print("Running coverage analysis...")
    
    # Create a Coverage object
    cov = coverage.Coverage(
        source=["har_oa3_converter"],
        omit=["*/__pycache__/*", "*/tests/*", "*/venv/*"]
    )
    
    # Start coverage measurement
    cov.start()
    
    # Run the tests using pytest
    print("Running tests...")
    result = subprocess.run(
        [
            "pytest", 
            "tests/", 
            "-v", 
            "--cov=har_oa3_converter", 
            "--cov-report=term-missing",
            "--cov-report=xml:reports/coverage.xml", 
            "--cov-report=html:reports/coverage",
            "--html=reports/html/report.html", 
            "--json-report", 
            "--json-report-file=reports/json/report.json"
        ],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("Some tests failed:")
        print(result.stdout)
        print(result.stderr)
    
    # Stop coverage measurement
    cov.stop()
    cov.save()
    
    # Get coverage data
    data = cov.get_data()
    
    # Find missing lines by module
    missing_by_module = {}
    print("\nAnalyzing coverage gaps...")
    for filename in data.measured_files():
        # Skip if not in our project
        if "har_oa3_converter" not in filename:
            continue
            
        analysis = cov.analysis2(filename)
        missing_lines = analysis.missing
        
        if missing_lines:
            module_name = filename.split("har_oa3_converter/")[-1]
            missing_by_module[module_name] = missing_lines
            print(f"Missing lines in {module_name}: {missing_lines}")
    
    # Save missing lines to a JSON file for later analysis
    with open('reports/missing_lines.json', 'w') as f:
        json.dump(missing_by_module, f, indent=2)
    
    # Calculate coverage percentage
    covered = sum(len(data.lines(file)) for file in data.measured_files())
    total = covered + sum(len(missing) for missing in missing_by_module.values())
    
    if total > 0:
        coverage_percent = (covered / total) * 100
        print(f"\nOverall coverage: {coverage_percent:.2f}%")
    else:
        print("\nNo code measured")
    
    # Check if we've achieved 100% coverage
    if len(missing_by_module) == 0:
        print("\n🎉 Congratulations! 100% code coverage achieved!")
    else:
        print("\n⚠️ Coverage gaps identified. Run targeted tests to improve coverage.")
        recommend_tests(missing_by_module)


def recommend_tests(missing_by_module):
    """Recommend tests based on coverage gaps."""
    print("\nRecommended actions to improve coverage:")
    
    # Group by module type
    api_modules = [m for m in missing_by_module if "api/" in m]
    converter_modules = [m for m in missing_by_module if "converters/" in m]
    util_modules = [m for m in missing_by_module if "utils/" in m]
    schema_modules = [m for m in missing_by_module if "schemas/" in m]
    
    # Recommend tests for API modules
    if api_modules:
        print("\n1. API Modules:")
        print("   - Run: pytest tests/coverage/test_error_conditions.py -v")
        print("   - Run: pytest tests/coverage/test_edge_cases.py -v")
    
    # Recommend tests for Converter modules
    if converter_modules:
        print("\n2. Converter Modules:")
        print("   - Run: pytest tests/coverage/test_internal_methods.py -v")
        print("   - Run: pytest tests/coverage/test_edge_cases.py::test_converter_edge_cases -v")
    
    # Recommend tests for Utility modules
    if util_modules:
        print("\n3. Utility Modules:")
        print("   - Run: pytest tests/coverage/test_rare_conditions.py -v")
    
    # Recommend tests for Schema modules
    if schema_modules:
        print("\n4. Schema Modules:")
        print("   - Run: pytest tests/coverage/test_internal_methods.py::test_json_schema_validation -v")
    
    print("\nTo run all specialized coverage tests:")
    print("   pytest tests/coverage/ -v")


def main():
    """Main entry point."""
    # Create reports directory if it doesn't exist
    Path("reports/html").mkdir(parents=True, exist_ok=True)
    Path("reports/json").mkdir(parents=True, exist_ok=True)
    Path("reports/coverage").mkdir(parents=True, exist_ok=True)
    
    run_coverage_analysis()


if __name__ == "__main__":
    main()
