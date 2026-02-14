from typing import Union, Any
import math

Number = Union[int, float]

def add_two_numbers(a: Any, b: Any) -> Number:
    """
    Add two numbers together with comprehensive validation and error handling.
    
    This function performs addition of two numeric values while handling various
    edge cases including infinity, NaN, and type validation.
    
    Args:
        a: First number to add (int, float, or numeric string)
        b: Second number to add (int, float, or numeric string)
    
    Returns:
        Number: The sum of the two input numbers as int or float
    
    Raises:
        TypeError: If inputs cannot be converted to numbers
        ValueError: If inputs are None or invalid numeric strings
        
    Examples:
        >>> add_two_numbers(5, 3)
        8
        >>> add_two_numbers(2.5, 1.5)
        4.0
        >>> add_two_numbers(-10, 15)
        5
        >>> add_two_numbers("5", "3")
        8
        >>> add_two_numbers(float('inf'), 10)
        inf
        
    Edge Cases:
        - Handles infinity values correctly
        - Returns NaN when appropriate (inf + (-inf))
        - Supports very large numbers within system limits
        - Handles negative numbers and zero
        - Converts numeric strings to numbers
    """
    
    # Input validation - check for None values
    if a is None or b is None:
        raise ValueError("Input parameters cannot be None")
    
    # Type conversion and validation
    try:
        # Convert inputs to numbers if they're strings
        if isinstance(a, str):
            # Handle empty strings
            if not a.strip():
                raise ValueError("Empty string is not a valid number")
            a = float(a) if '.' in a or 'e' in a.lower() else int(a)
        
        if isinstance(b, str):
            # Handle empty strings
            if not b.strip():
                raise ValueError("Empty string is not a valid number")
            b = float(b) if '.' in b or 'e' in b.lower() else int(b)
        
        # Validate that inputs are numeric types
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise TypeError(f"Inputs must be numbers or numeric strings. Got types: {type(a).__name__}, {type(b).__name__}")
        
        # Check for complex numbers (not supported)
        if isinstance(a, complex) or isinstance(b, complex):
            raise TypeError("Complex numbers are not supported")
            
    except (ValueError, TypeError) as e:
        if "could not convert" in str(e) or "invalid literal" in str(e):
            raise TypeError(f"Cannot convert inputs to numbers: a='{a}', b='{b}'")
        raise
    
    # Handle special floating-point cases
    if math.isnan(a) or math.isnan(b):
        return float('nan')
    
    # Perform addition
    result = a + b
    
    # Handle infinity cases
    if math.isinf(result):
        return result
    
    # Return appropriate type (preserve int if both inputs were int)
    if isinstance(a, int) and isinstance(b, int):
        return result
    else:
        return float(result)


# Comprehensive test suite
import unittest
import sys

class TestAddTwoNumbers(unittest.TestCase):
    """Comprehensive test suite for add_two_numbers function."""
    
    def test_basic_integer_addition(self):
        """Test basic integer addition cases."""
        self.assertEqual(add_two_numbers(2, 3), 5)
        self.assertEqual(add_two_numbers(0, 0), 0)
        self.assertEqual(add_two_numbers(-5, 10), 5)
        self.assertEqual(add_two_numbers(-3, -7), -10)
    
    def test_floating_point_addition(self):
        """Test floating-point number addition."""
        self.assertAlmostEqual(add_two_numbers(2.5, 3.7), 6.2, places=10)
        self.assertAlmostEqual(add_two_numbers(0.1, 0.2), 0.3, places=10)
        self.assertEqual(add_two_numbers(1.0, 2.0), 3.0)
    
    def test_mixed_type_addition(self):
        """Test addition of mixed int/float types."""
        self.assertEqual(add_two_numbers(5, 2.5), 7.5)
        self.assertEqual(add_two_numbers(3.0, 4), 7.0)
    
    def test_string_number_conversion(self):
        """Test conversion of numeric strings."""
        self.assertEqual(add_two_numbers("5", "3"), 8)
        self.assertEqual(add_two_numbers("2.5", "1.5"), 4.0)
        self.assertEqual(add_two_numbers("10", 5), 15)
        self.assertEqual(add_two_numbers(7, "3"), 10)
    
    def test_large_numbers(self):
        """Test handling of very large numbers."""
        large_num = sys.maxsize
        self.assertEqual(add_two_numbers(large_num, 1), large_num + 1)
        self.assertEqual(add_two_numbers(1e308, 1e308), 2e308)
    
    def test_infinity_handling(self):
        """Test infinity value handling."""
        inf = float('inf')
        neg_inf = float('-inf')
        
        self.assertEqual(add_two_numbers(inf, 10), inf)
        self.assertEqual(add_two_numbers(10, inf), inf)
        self.assertEqual(add_two_numbers(neg_inf, 10), neg_inf)
        self.assertTrue(math.isnan(add_two_numbers(inf, neg_inf)))
    
    def test_nan_handling(self):
        """Test NaN value handling."""
        nan = float('nan')
        self.assertTrue(math.isnan(add_two_numbers(nan, 5)))
        self.assertTrue(math.isnan(add_two_numbers(5, nan)))
        self.assertTrue(math.isnan(add_two_numbers(nan, nan)))
    
    def test_zero_handling(self):
        """Test zero value handling."""
        self.assertEqual(add_two_numbers(0, 5), 5)
        self.assertEqual(add_two_numbers(-0, 5), 5)
        self.assertEqual(add_two_numbers(0, -5), -5)
    
    def test_none_input_validation(self):
        """Test None input validation."""
        with self.assertRaises(ValueError):
            add_two_numbers(None, 5)
        with self.assertRaises(ValueError):
            add_two_numbers(5, None)
        with self.assertRaises(ValueError):
            add_two_numbers(None, None)
    
    def test_invalid_type_validation(self):
        """Test invalid type validation."""
        with self.assertRaises(TypeError):
            add_two_numbers("hello", 5)
        with self.assertRaises(TypeError):
            add_two_numbers(5, [1, 2, 3])
        with self.assertRaises(TypeError):
            add_two_numbers({}, 5)
        with self.assertRaises(TypeError):
            add_two_numbers(5, {"key": "value"})
    
    def test_empty_string_validation(self):
        """Test empty string validation."""
        with self.assertRaises(ValueError):
            add_two_numbers("", 5)
        with self.assertRaises(ValueError):
            add_two_numbers("   ", 5)
        with self.assertRaises(ValueError):
            add_two_numbers(5, "")
    
    def test_scientific_notation(self):
        """Test scientific notation handling."""
        self.assertEqual(add_two_numbers("1e2", "2e1"), 120.0)
        self.assertEqual(add_two_numbers(1e3, 2e2), 1200.0)
    
    def test_negative_string_numbers(self):
        """Test negative string numbers."""
        self.assertEqual(add_two_numbers("-5", "3"), -2)
        self.assertEqual(add_two_numbers("-2.5", "-1.5"), -4.0)
    
    def test_return_type_preservation(self):
        """Test that return types are preserved appropriately."""
        # Both integers should return int
        result = add_two_numbers(5, 3)
        self.assertIsInstance(result, int)
        
        # Any float should return float
        result = add_two_numbers(5.0, 3)
        self.assertIsInstance(result, float)
        
        result = add_two_numbers(5, 3.0)
        self.assertIsInstance(result, float)


def run_tests():
    """Run the complete test suite."""
    unittest.main(argv=[''], exit=False, verbosity=2)


# Usage examples and demonstration
def demonstrate_usage():
    """Demonstrate various usage scenarios of the add_two_numbers function."""
    
    print("=== Add Two Numbers Function Demonstration ===\n")
    
    # Basic usage examples
    examples = [
        (5, 3, "Basic integer addition"),
        (2.5, 1.5, "Floating-point addition"),
        (-10, 15, "Negative and positive numbers"),
        ("5", "3", "String numbers"),
        (float('inf'), 10, "Infinity handling"),
        (1e10, 2e10, "Large numbers"),
        (0, 0, "Zero values"),
    ]
    
    for a, b, description in examples:
        try:
            result = add_two_numbers(a, b)
            print(f"{description}: {a} + {b} = {result}")
        except Exception as e:
            print(f"{description}: {a} + {b} -> Error: {e}")
    
    print("\n=== Error Handling Examples ===\n")
    
    # Error cases
    error_examples = [
        (None, 5, "None input"),
        ("hello", 5, "Invalid string"),
        ([], 5, "List input"),
        ("", 5, "Empty string"),
    ]
    
    for a, b, description in error_examples:
        try:
            result = add_two_numbers(a, b)
            print(f"{description}: {a} + {b} = {result}")
        except Exception as e:
            print(f"{description}: {a} + {b} -> Error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    # Run demonstrations
    demonstrate_usage()
    
    print("\n" + "="*50)
    print("Running comprehensive test suite...")
    print("="*50 + "\n")
    
    # Run tests
    run_tests()