"""
Number Even Check Module

This module provides functionality to check if a number is even (divisible by 2).

Functions:
    is_even(number) -> bool: Returns True if number is even, False if odd.

Usage Examples:
    Basic usage:
        >>> from number_utils import is_even
        >>> is_even(4)
        True
        >>> is_even(7)
        False
    
    With different input types:
        >>> is_even("6")    # String input
        True
        >>> is_even(8.0)    # Float input (whole number)
        True
        >>> is_even(-3)     # Negative number
        False
    
    Error handling:
        >>> is_even(3.14)   # Float with decimals
        TypeError: Float values must be whole numbers for even/odd check
        >>> is_even("abc")  # Invalid string
        TypeError: Cannot convert 'abc' to a numeric value
        >>> is_even(None)   # None input
        TypeError: Input cannot be None

Edge Cases and Limitations:
    - Zero (0) is considered even and returns True
    - Negative numbers are handled correctly (-2 is even, -1 is odd)
    - String inputs are converted to numbers if possible
    - Float inputs must represent whole numbers (no decimal places)
    - Non-numeric types raise TypeError
    - Very large numbers are supported within Python's integer limits

Performance Notes:
    - Time complexity: O(1) - constant time operation
    - Space complexity: O(1) - constant space usage
    - Suitable for high-frequency calls
    - No performance concerns for standard numeric ranges

Type Information:
    Function Signature:
        def is_even(number: Union[int, float, str]) -> bool
    
    Parameters:
        number: int, float, or str - The number to check
    
    Returns:
        bool - True if even, False if odd
    
    Raises:
        TypeError - For invalid input types or non-whole float values
"""