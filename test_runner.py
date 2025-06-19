#!/usr/bin/env python
"""
Test runner for Orquestra QRE project.
Execute this script to run all tests.
"""

import pytest
import os
import sys

if __name__ == "__main__":
    # Add the project root to the path
    sys.path.insert(0, os.path.abspath("."))
    
    # Define pytest arguments
    pytest_args = [
        "tests/",                # Test directory
        "-v",                   # Verbose output
        "--color=yes",         # Colored output
        "--cov=orquestra_qre",  # Coverage for the orquestra_qre package
        "--cov-report=term",   # Display coverage report in the terminal
    ]
    
    # Run the tests
    exit_code = pytest.main(pytest_args)
    
    # Exit with the pytest return code
    sys.exit(exit_code)
