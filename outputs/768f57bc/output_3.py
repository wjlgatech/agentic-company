#!/usr/bin/env python3
"""
Test runner script with coverage reporting.
"""

import unittest
import sys
from io import StringIO


def run_tests_with_coverage():
    """Run tests and display coverage information."""
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover('.', pattern='test_*.py')
    
    # Capture test output
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    
    # Display results
    print("=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    print(stream.getvalue())
    
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests_with_coverage()
    sys.exit(0 if success else 1)