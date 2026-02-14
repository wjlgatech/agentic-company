#!/usr/bin/env python3
"""
Example usage demonstration of the is_even function.
"""

from number_utils import is_even


def demonstrate_usage():
    """Demonstrate various usage scenarios."""
    
    print("=== Number Even Check Function Demo ===\n")
    
    # Test cases with expected results
    test_cases = [
        (4, True, "Positive even"),
        (7, False, "Positive odd"), 
        (-2, True, "Negative even"),
        (-3, False, "Negative odd"),
        (0, True, "Zero"),
        ("6", True, "String even"),
        ("5", False, "String odd"),
        (10.0, True, "Float whole even"),
        (9.0, False, "Float whole odd"),
    ]
    
    print("Valid inputs:")
    for value, expected, description in test_cases:
        try:
            result = is_even(value)
            status = "✓" if result == expected else "✗"
            print(f"{status} is_even({value!r}) = {result} ({description})")
        except Exception as e:
            print(f"✗ is_even({value!r}) raised {type(e).__name__}: {e}")
    
    print("\nError cases:")
    error_cases = [
        (3.14, "Float with decimals"),
        ("abc", "Invalid string"),
        (None, "None input"),
        ([], "List input"),
    ]
    
    for value, description in error_cases:
        try:
            result = is_even(value)
            print(f"✗ is_even({value!r}) = {result} (should have raised error)")
        except Exception as e:
            print(f"✓ is_even({value!r}) raised {type(e).__name__}: {e} ({description})")


if __name__ == "__main__":
    demonstrate_usage()