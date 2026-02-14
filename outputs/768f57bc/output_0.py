def is_even(number) -> bool:
    """
    Check if a number is even (divisible by 2).
    
    Args:
        number: Numeric value to check. Accepts int, float, or string representations.
        
    Returns:
        bool: True if the number is even, False if odd.
        
    Raises:
        TypeError: If input cannot be converted to a numeric value.
        
    Examples:
        >>> is_even(4)
        True
        >>> is_even(3)
        False
        >>> is_even(0)
        True
        >>> is_even(-2)
        True
        >>> is_even("8")
        True
    """
    # Handle None/null inputs
    if number is None:
        raise TypeError("Input cannot be None")
    
    # Convert string inputs to numeric if possible
    if isinstance(number, str):
        try:
            # Try integer conversion first
            if '.' not in number:
                number = int(number)
            else:
                number = float(number)
        except ValueError:
            raise TypeError(f"Cannot convert '{number}' to a numeric value")
    
    # Handle non-numeric types
    if not isinstance(number, (int, float)):
        raise TypeError(f"Expected numeric type, got {type(number).__name__}")
    
    # Convert float to int for even/odd check
    # Handle case where float has decimal places
    if isinstance(number, float):
        if not number.is_integer():
            raise TypeError("Float values must be whole numbers for even/odd check")
        number = int(number)
    
    # Perform even check using modulo operator
    return number % 2 == 0