"""
Comprehensive test suite for the Calculator class.

Tests cover all basic operations with normal cases, edge cases, boundary conditions,
and error scenarios to ensure 100% code coverage and reliability.
"""

import pytest
import math
from calculator import Calculator


class TestCalculator:
    """Test suite for Calculator class with comprehensive coverage."""
    
    def setup_method(self):
        """Set up a fresh calculator instance for each test."""
        self.calc = Calculator()
    
    # Addition Tests
    def test_add_positive_numbers(self):
        """Test addition with positive numbers."""
        assert self.calc.add(2, 3) == 5
        assert self.calc.add(10, 15) == 25
    
    def test_add_negative_numbers(self):
        """Test addition with negative numbers."""
        assert self.calc.add(-2, -3) == -5
        assert self.calc.add(-10, -15) == -25
    
    def test_add_mixed_signs(self):
        """Test addition with mixed positive and negative numbers."""
        assert self.calc.add(-5, 3) == -2
        assert self.calc.add(5, -3) == 2
    
    def test_add_with_zero(self):
        """Test addition with zero values."""
        assert self.calc.add(0, 5) == 5
        assert self.calc.add(5, 0) == 5
        assert self.calc.add(0, 0) == 0
        assert self.calc.add(0, -5) == -5
    
    def test_add_decimal_numbers(self):
        """Test addition with decimal numbers."""
        assert self.calc.add(2.5, 3.7) == 6.2
        assert self.calc.add(-2.5, 1.5) == -1.0
        assert abs(self.calc.add(0.1, 0.2) - 0.3) < 1e-10  # Handle floating point precision
    
    def test_add_large_numbers(self):
        """Test addition with large numbers."""
        assert self.calc.add(1000000, 2000000) == 3000000
        assert self.calc.add(1e10, 2e10) == 3e10
    
    def test_add_invalid_types(self):
        """Test addition with invalid input types."""
        with pytest.raises(TypeError):
            self.calc.add("5", 3)
        with pytest.raises(TypeError):
            self.calc.add(5, "3")
        with pytest.raises(TypeError):
            self.calc.add(None, 5)
        with pytest.raises(TypeError):
            self.calc.add(5, [])
    
    # Subtraction Tests
    def test_subtract_positive_numbers(self):
        """Test subtraction with positive numbers."""
        assert self.calc.subtract(5, 3) == 2
        assert self.calc.subtract(10, 4) == 6
    
    def test_subtract_negative_result(self):
        """Test subtraction resulting in negative numbers."""
        assert self.calc.subtract(3, 5) == -2
        assert self.calc.subtract(1, 10) == -9
    
    def test_subtract_negative_numbers(self):
        """Test subtraction with negative numbers."""
        assert self.calc.subtract(-5, -3) == -2
        assert self.calc.subtract(-3, -5) == 2
        assert self.calc.subtract(-5, 3) == -8
        assert self.calc.subtract(5, -3) == 8
    
    def test_subtract_with_zero(self):
        """Test subtraction with zero values."""
        assert self.calc.subtract(5, 0) == 5
        assert self.calc.subtract(0, 5) == -5
        assert self.calc.subtract(0, 0) == 0
        assert self.calc.subtract(-5, 0) == -5
    
    def test_subtract_decimal_numbers(self):
        """Test subtraction with decimal numbers."""
        assert self.calc.subtract(5.5, 2.3) == 3.2
        assert self.calc.subtract(1.1, 2.2) == -1.1
        assert abs(self.calc.subtract(0.3, 0.1) - 0.2) < 1e-10
    
    def test_subtract_large_numbers(self):
        """Test subtraction with large numbers."""
        assert self.calc.subtract(3000000, 1000000) == 2000000
        assert self.calc.subtract(1e10, 3e9) == 7e9
    
    def test_subtract_invalid_types(self):
        """Test subtraction with invalid input types."""
        with pytest.raises(TypeError):
            self.calc.subtract("5", 3)
        with pytest.raises(TypeError):
            self.calc.subtract(5, "3")
        with pytest.raises(TypeError):
            self.calc.subtract(None, 5)
    
    # Multiplication Tests
    def test_multiply_positive_numbers(self):
        """Test multiplication with positive numbers."""
        assert self.calc.multiply(3, 4) == 12
        assert self.calc.multiply(7, 8) == 56
    
    def test_multiply_with_zero(self):
        """Test multiplication with zero."""
        assert self.calc.multiply(0, 5) == 0
        assert self.calc.multiply(5, 0) == 0
        assert self.calc.multiply(0, 0) == 0
        assert self.calc.multiply(-5, 0) == 0
        assert self.calc.multiply(0, -5) == 0
    
    def test_multiply_negative_numbers(self):
        """Test multiplication with negative numbers."""
        assert self.calc.multiply(-3, 4) == -12
        assert self.calc.multiply(3, -4) == -12
        assert self.calc.multiply(-3, -4) == 12
        assert self.calc.multiply(-7, -8) == 56
    
    def test_multiply_decimal_numbers(self):
        """Test multiplication with decimal numbers."""
        assert self.calc.multiply(2.5, 4) == 10.0
        assert self.calc.multiply(3.2, 2.5) == 8.0
        assert abs(self.calc.multiply(0.1, 0.2) - 0.02) < 1e-10
    
    def test_multiply_large_numbers(self):
        """Test multiplication with large numbers."""
        assert self.calc.multiply(1000, 2000) == 2000000
        assert self.calc.multiply(1e5, 1e5) == 1e10
    
    def test_multiply_by_one(self):
        """Test multiplication by one (identity)."""
        assert self.calc.multiply(5, 1) == 5
        assert self.calc.multiply(1, 5) == 5
        assert self.calc.multiply(-5, 1) == -5
    
    def test_multiply_invalid_types(self):
        """Test multiplication with invalid input types."""
        with pytest.raises(TypeError):
            self.calc.multiply("5", 3)
        with pytest.raises(TypeError):
            self.calc.multiply(5, "3")
        with pytest.raises(TypeError):
            self.calc.multiply([], 5)
    
    # Division Tests
    def test_divide_positive_numbers(self):
        """Test division with positive numbers."""
        assert self.calc.divide(8, 2) == 4.0
        assert self.calc.divide(15, 3) == 5.0
        assert self.calc.divide(7, 2) == 3.5
    
    def test_divide_by_zero_error(self):
        """Test division by zero raises appropriate error."""
        with pytest.raises(ZeroDivisionError, match="Cannot divide by zero"):
            self.calc.divide(5, 0)
        with pytest.raises(ZeroDivisionError):
            self.calc.divide(-5, 0)
        with pytest.raises(ZeroDivisionError):
            self.calc.divide(0, 0)
    
    def test_divide_zero_dividend(self):
        """Test division with zero as dividend."""
        assert self.calc.divide(0, 5) == 0.0
        assert self.calc.divide(0, -5) == 0.0
        assert self.calc.divide(0, 2.5) == 0.0
    
    def test_divide_negative_numbers(self):
        """Test division with negative numbers."""
        assert self.calc.divide(-8, 2) == -4.0
        assert self.calc.divide(8, -2) == -4.0
        assert self.calc.divide(-8, -2) == 4.0
        assert self.calc.divide(-15, -3) == 5.0
    
    def test_divide_decimal_results(self):
        """Test division resulting in decimal numbers."""
        assert self.calc.divide(1, 3) == pytest.approx(0.3333333333333333)
        assert self.calc.divide(5, 2) == 2.5
        assert self.calc.divide(1, 8) == 0.125
    
    def test_divide_decimal_numbers(self):
        """Test division with decimal inputs."""
        assert self.calc.divide(5.5, 2.5) == 2.2
        assert self.calc.divide(7.5, 1.5) == 5.0
        assert abs(self.calc.divide(0.6, 0.2) - 3.0) < 1e-10
    
    def test_divide_large_numbers(self):
        """Test division with large numbers."""
        assert self.calc.divide(1000000, 1000) == 1000.0
        assert self.calc.divide(1e10, 1e5) == 1e5
    
    def test_divide_by_one(self):
        """Test division by one (identity)."""
        assert self.calc.divide(5, 1) == 5.0
        assert self.calc.divide(-5, 1) == -5.0
        assert self.calc.divide(3.7, 1) == 3.7
    
    def test_divide_invalid_types(self):
        """Test division with invalid input types."""
        with pytest.raises(TypeError):
            self.calc.divide("8", 2)
        with pytest.raises(TypeError):
            self.calc.divide(8, "2")
        with pytest.raises(TypeError):
            self.calc.divide({}, 2)
    
    # Integration Tests
    def test_multiple_operations_sequence(self):
        """Test performing multiple operations in sequence."""
        # Test: (5 + 3) * 2 - 4 / 2 = 8 * 2 - 2 = 16 - 2 = 14
        result1 = self.calc.add(5, 3)  # 8
        result2 = self.calc.multiply(result1, 2)  # 16
        result3 = self.calc.divide(4, 2)  # 2.0
        final_result = self.calc.subtract(result2, result3)  # 14.0
        assert final_result == 14.0
    
    def test_calculator_state_independence(self):
        """Test that calculator operations don't maintain state between calls."""
        # Each operation should be independent
        assert self.calc.add(2, 3) == 5
        assert self.calc.multiply(4, 5) == 20
        assert self.calc.subtract(10, 3) == 7
        assert self.calc.divide(15, 3) == 5.0
        
        # Previous operations shouldn't affect new ones
        assert self.calc.add(1, 1) == 2
    
    def test_multiple_calculator_instances(self):
        """Test that multiple calculator instances work independently."""
        calc1 = Calculator()
        calc2 = Calculator()
        
        result1 = calc1.add(5, 5)
        result2 = calc2.multiply(3, 4)
        
        assert result1 == 10
        assert result2 == 12
        
        # Both calculators should still work independently
        assert calc1.subtract(result1, 2) == 8
        assert calc2.divide(result2, 3) == 4.0
    
    def test_complex_calculation_chain(self):
        """Test a complex chain of calculations."""
        # Calculate: ((10 + 5) * 3 - 20) / 5 = (15 * 3 - 20) / 5 = (45 - 20) / 5 = 25 / 5 = 5
        step1 = self.calc.add(10, 5)        # 15
        step2 = self.calc.multiply(step1, 3) # 45
        step3 = self.calc.subtract(step2, 20) # 25
        final = self.calc.divide(step3, 5)   # 5.0
        
        assert final == 5.0
    
    def test_edge_case_combinations(self):

VERIFICATION:

=== AGENT PROMPT ===
You are Verifier - Cross-Verification Against Spec.

You are a verification specialist.

YOUR JOB:
The developer doesn't mark their own homework.
Check every implementation against the acceptance criteria.

VERIFICATION CHECKLIST:
1. Does the code meet ALL acceptance criteria?
2. Are there any edge cases not handled?
3. Does it follow the specified patterns?
4. Any security concerns?

OUTPUT: VERIFIED or list of issues to fix.


YOUR TASK FOR THIS STEP:
Cross-verify implementation against spec


=== TASK CONTEXT ===
ORIGINAL PLAN:
## Feature: Simple Calculator with Basic Operations

## Tasks:

1. **Design Calculator Interface** - Define the public API and method signatures for the calculator class including add, subtract, multiply, and divide operations - Acceptance criteria: Calculator class interface documented with clear method signatures, parameter types, and return types defined

2. **Implement Addition Function** - Create the add method that takes two numeric inputs and returns their sum - Acceptance criteria: Method accepts two numbers (int/float), returns correct sum, handles edge cases like zero values and negative numbers

3. **Implement Subtraction Function** - Create the subtract method that takes two numeric inputs and returns their difference - Acceptance criteria: Method accepts two numbers, returns correct difference (first - second), handles negative results correctly

4. **Implement Multiplication Function** - Create the multiply method that takes two numeric inputs and returns their product - Acceptance criteria: Method accepts two numbers, returns correct product, handles zero multiplication and negative number multiplication

5. **Implement Division Function** - Create the divide method that takes two numeric inputs and returns their quotient with proper error handling - Acceptance criteria: Method accepts two numbers, returns correct quotient, throws appropriate error for division by zero, handles decimal results

6. **Create Unit Tests for Addition** - Write comprehensive test cases for the add function covering normal cases, edge cases, and boundary conditions - Acceptance criteria: Tests cover positive numbers, negative numbers, zero, decimal numbers, and large numbers with 100% code coverage

7. **Create Unit Tests for Subtraction** - Write comprehensive test cases for the subtract function - Acceptance criteria: Tests cover all numeric combinations, negative results, zero operations with full coverage

8. **Create Unit Tests for Multiplication** - Write comprehensive test cases for the multiply function - Acceptance criteria: Tests cover zero multiplication, negative numbers, decimals, large numbers with complete coverage

9. **Create Unit Tests for Division** - Write comprehensive test cases for the divide function including error scenarios - Acceptance criteria: Tests cover normal division, decimal results, division by zero error handling, negative number division with full coverage

10. **Integration Testing** - Create tests that verify all calculator operations work together correctly - Acceptance criteria: Tests verify calculator instance can perform multiple operations in sequence, state is maintained correctly

11. **Documentation and Code Review** - Create user documentation and prepare code for review - Acceptance criteria: README with usage examples, inline code comments, code follows style guidelines

## Dependencies:
- Programming language and testing framework selection must be completed first
- Development environment setup required before implementation
- Task 1 (Interface Design) must be completed before any implementation tasks (2-5)
- Implementation tasks (2-5) must be completed before corresponding test tasks (6-9)
- All unit tests (6-9) should be completed before integration testing (10)

## Risks:
- **Floating point precision issues** - Division and decimal operations may have rounding errors
- **Input validation complexity** - Need to handle various numeric types and invalid inputs
- **Error handling inconsistency** - Different operations may handle edge cases differently
- **Testing framework limitations** - Chosen testing framework may not support all required test scenarios
- **Performance considerations** - Large number operations might cause overflow/underflow
- **Cross-platform compatibility** - Numeric operations may behave differently across platforms

STATUS: done

IMPLEMENTATION:
I'll implement a complete calculator with all the specified tasks. I'll use Python with type hints and pytest for testing.

## calculator.py