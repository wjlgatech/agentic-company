import unittest
from typing import Any


class TestIsEven(unittest.TestCase):
    """Comprehensive test suite for is_even function."""
    
    def test_positive_even_numbers(self):
        """Test positive even numbers return True."""
        test_cases = [2, 4, 6, 100, 1000]
        for num in test_cases:
            with self.subTest(number=num):
                self.assertTrue(is_even(num))
    
    def test_positive_odd_numbers(self):
        """Test positive odd numbers return False."""
        test_cases = [1, 3, 5, 99, 1001]
        for num in test_cases:
            with self.subTest(number=num):
                self.assertFalse(is_even(num))
    
    def test_negative_even_numbers(self):
        """Test negative even numbers return True."""
        test_cases = [-2, -4, -6, -100, -1000]
        for num in test_cases:
            with self.subTest(number=num):
                self.assertTrue(is_even(num))
    
    def test_negative_odd_numbers(self):
        """Test negative odd numbers return False."""
        test_cases = [-1, -3, -5, -99, -1001]
        for num in test_cases:
            with self.subTest(number=num):
                self.assertFalse(is_even(num))
    
    def test_zero(self):
        """Test that zero returns True (even)."""
        self.assertTrue(is_even(0))
    
    def test_string_integers(self):
        """Test string representations of integers."""
        self.assertTrue(is_even("4"))
        self.assertFalse(is_even("3"))
        self.assertTrue(is_even("0"))
        self.assertTrue(is_even("-2"))
        self.assertFalse(is_even("-1"))
    
    def test_float_whole_numbers(self):
        """Test float values that are whole numbers."""
        self.assertTrue(is_even(4.0))
        self.assertFalse(is_even(3.0))
        self.assertTrue(is_even(0.0))
        self.assertTrue(is_even(-2.0))
    
    def test_string_floats_whole_numbers(self):
        """Test string representations of whole number floats."""
        self.assertTrue(is_even("4.0"))
        self.assertFalse(is_even("3.0"))
        self.assertTrue(is_even("0.0"))
    
    def test_none_input(self):
        """Test None input raises TypeError."""
        with self.assertRaises(TypeError) as context:
            is_even(None)
        self.assertIn("Input cannot be None", str(context.exception))
    
    def test_invalid_string_input(self):
        """Test invalid string inputs raise TypeError."""
        invalid_strings = ["abc", "12abc", "3.14.15", ""]
        for invalid_str in invalid_strings:
            with self.subTest(string=invalid_str):
                with self.assertRaises(TypeError):
                    is_even(invalid_str)
    
    def test_float_with_decimals(self):
        """Test float values with decimal places raise TypeError."""
        decimal_floats = [3.14, 2.5, -1.7, 0.1]
        for num in decimal_floats:
            with self.subTest(number=num):
                with self.assertRaises(TypeError) as context:
                    is_even(num)
                self.assertIn("whole numbers", str(context.exception))
    
    def test_invalid_types(self):
        """Test invalid data types raise TypeError."""
        invalid_inputs = [[], {}, set(), object(), complex(1, 2)]
        for invalid_input in invalid_inputs:
            with self.subTest(input_type=type(invalid_input).__name__):
                with self.assertRaises(TypeError):
                    is_even(invalid_input)
    
    def test_boolean_inputs(self):
        """Test boolean inputs raise TypeError."""
        with self.assertRaises(TypeError):
            is_even(True)
        with self.assertRaises(TypeError):
            is_even(False)


if __name__ == "__main__":
    # Run tests with coverage
    unittest.main(verbosity=2)