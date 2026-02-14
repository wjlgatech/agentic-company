"""
Simple Calculator with Basic Operations

A calculator class that provides basic arithmetic operations including
addition, subtraction, multiplication, and division with proper error handling.
"""

from typing import Union

Number = Union[int, float]


class Calculator:
    """
    A simple calculator that performs basic arithmetic operations.
    
    This calculator supports addition, subtraction, multiplication, and division
    operations on integers and floating-point numbers with comprehensive error
    handling and edge case management.
    """
    
    def add(self, a: Number, b: Number) -> Number:
        """
        Add two numbers together.
        
        Args:
            a: First number (int or float)
            b: Second number (int or float)
            
        Returns:
            The sum of a and b
            
        Raises:
            TypeError: If inputs are not numeric types
        """
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise TypeError("Both arguments must be numbers (int or float)")
        
        return a + b
    
    def subtract(self, a: Number, b: Number) -> Number:
        """
        Subtract the second number from the first number.
        
        Args:
            a: First number (minuend)
            b: Second number (subtrahend)
            
        Returns:
            The difference of a - b
            
        Raises:
            TypeError: If inputs are not numeric types
        """
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise TypeError("Both arguments must be numbers (int or float)")
        
        return a - b
    
    def multiply(self, a: Number, b: Number) -> Number:
        """
        Multiply two numbers together.
        
        Args:
            a: First number (int or float)
            b: Second number (int or float)
            
        Returns:
            The product of a and b
            
        Raises:
            TypeError: If inputs are not numeric types
        """
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise TypeError("Both arguments must be numbers (int or float)")
        
        return a * b
    
    def divide(self, a: Number, b: Number) -> float:
        """
        Divide the first number by the second number.
        
        Args:
            a: Dividend (number to be divided)
            b: Divisor (number to divide by)
            
        Returns:
            The quotient of a / b as a float
            
        Raises:
            TypeError: If inputs are not numeric types
            ZeroDivisionError: If divisor (b) is zero
        """
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise TypeError("Both arguments must be numbers (int or float)")
        
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        
        return a / b