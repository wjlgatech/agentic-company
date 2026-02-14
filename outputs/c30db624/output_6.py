def run_all_tests():
    """Run all test suites and report results."""
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestSubtractUnitTests,
        TestSubtractIntegration,
        TestSubtractEdgeCases,
        TestSubtractErrorHandling,
        TestSubtractPerformance,
        TestSubtractCompatibility
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    # Run all tests
    success = run_all_tests()
    
    if success:
        print(f"\n🎉 ALL TESTS PASSED! 🎉")
        print(f"The subtract function implementation is ready for production.")
    else:
        print(f"\n❌ SOME TESTS FAILED")
        print(f"Please review the failures and fix the implementation.")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)