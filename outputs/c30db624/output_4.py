class TestSubtractPerformance(unittest.TestCase):
    """Performance and stress tests."""
    
    def test_performance_with_large_dataset(self):
        """Test performance with large datasets."""
        import time
        
        # Large number of operations
        start_time = time.perf_counter()
        for i in range(10000):
            subtract(i, i // 2)
        end_time = time.perf_counter()
        
        # Should complete in reasonable time (less than 1 second)
        execution_time = end_time - start_time
        self.assertLess(execution_time, 1.0, "Performance test failed - too slow")
    
    def test_memory_usage(self):
        """Test that function doesn't leak memory."""
        import gc
        
        # Force garbage collection
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Perform many operations
        for i in range(1000):
            result = subtract(i * 1.5, i * 0.5)
            del result
        
        # Force garbage collection again
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Object count shouldn't grow significantly
        object_growth = final_objects - initial_objects
        self.assertLess(object_growth, 100, "Possible memory leak detected")
    
    def test_stress_with_extreme_values(self):
        """Stress test with extreme values."""
        extreme_cases = [
            (sys.maxsize, -sys.maxsize),
            (sys.float_info.max, -sys.float_info.max),
            (1e308, -1e308),
            (-1e308, 1e308)
        ]
        
        for case in extreme_cases:
            try:
                result = subtract(case[0], case[1])
                # Just verify it completes without crashing
                self.assertIsInstance(result, (int, float))
            except OverflowError:
                # Overflow is acceptable for extreme values
                pass