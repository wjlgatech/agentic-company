from typing import Optional, Union


def greet(name: Optional[str]) -> str:
    """
    Generate a greeting message for the given name.
    
    This function creates a personalized greeting by concatenating "Hello " 
    with the provided name. It handles various edge cases including null/undefined 
    inputs, empty strings, and special characters.
    
    Args:
        name (Optional[str]): The name to include in the greeting. Can be None,
                             empty string, or any valid string containing letters,
                             numbers, spaces, and special characters.
    
    Returns:
        str: A greeting message in the format "Hello <name>". If name is None
             or empty, returns "Hello Guest".
    
    Examples:
        >>> greet("Alice")
        'Hello Alice'
        
        >>> greet("John Doe")
        'Hello John Doe'
        
        >>> greet("")
        'Hello Guest'
        
        >>> greet(None)
        'Hello Guest'
        
        >>> greet("José María")
        'Hello José María'
        
        >>> greet("User123")
        'Hello User123'
    """
    # Handle null/undefined inputs
    if name is None:
        return "Hello Guest"
    
    # Handle empty strings and whitespace-only strings
    if not name or not name.strip():
        return "Hello Guest"
    
    # Clean the name by stripping leading/trailing whitespace
    clean_name = name.strip()
    
    # Return the formatted greeting
    return f"Hello {clean_name}"


# Unit Tests
import unittest
from unittest.mock import patch


class TestGreetFunction(unittest.TestCase):
    """Comprehensive test suite for the greet function."""
    
    def test_normal_cases(self):
        """Test normal cases with valid names."""
        self.assertEqual(greet("Alice"), "Hello Alice")
        self.assertEqual(greet("Bob"), "Hello Bob")
        self.assertEqual(greet("John Doe"), "Hello John Doe")
        self.assertEqual(greet("Mary Jane Watson"), "Hello Mary Jane Watson")
    
    def test_edge_cases_null_undefined(self):
        """Test handling of null/undefined inputs."""
        self.assertEqual(greet(None), "Hello Guest")
    
    def test_edge_cases_empty_strings(self):
        """Test handling of empty and whitespace strings."""
        self.assertEqual(greet(""), "Hello Guest")
        self.assertEqual(greet("   "), "Hello Guest")
        self.assertEqual(greet("\t"), "Hello Guest")
        self.assertEqual(greet("\n"), "Hello Guest")
        self.assertEqual(greet("  \t\n  "), "Hello Guest")
    
    def test_special_characters(self):
        """Test handling of names with special characters."""
        self.assertEqual(greet("José"), "Hello José")
        self.assertEqual(greet("François"), "Hello François")
        self.assertEqual(greet("李小明"), "Hello 李小明")
        self.assertEqual(greet("O'Connor"), "Hello O'Connor")
        self.assertEqual(greet("Jean-Pierre"), "Hello Jean-Pierre")
        self.assertEqual(greet("Smith Jr."), "Hello Smith Jr.")
        self.assertEqual(greet("User@123"), "Hello User@123")
        self.assertEqual(greet("Test_User"), "Hello Test_User")
    
    def test_whitespace_handling(self):
        """Test proper whitespace trimming."""
        self.assertEqual(greet("  Alice  "), "Hello Alice")
        self.assertEqual(greet("\tBob\t"), "Hello Bob")
        self.assertEqual(greet("\nCharlie\n"), "Hello Charlie")
        self.assertEqual(greet("  John Doe  "), "Hello John Doe")
    
    def test_numeric_and_mixed_content(self):
        """Test names with numbers and mixed content."""
        self.assertEqual(greet("User123"), "Hello User123")
        self.assertEqual(greet("2Pac"), "Hello 2Pac")
        self.assertEqual(greet("R2D2"), "Hello R2D2")
        self.assertEqual(greet("Agent007"), "Hello Agent007")
    
    def test_exact_output_format(self):
        """Verify exact output format requirements."""
        result = greet("TestUser")
        self.assertTrue(result.startswith("Hello "))
        self.assertEqual(result, "Hello TestUser")
        self.assertIsInstance(result, str)
    
    def test_long_names(self):
        """Test handling of very long names."""
        long_name = "A" * 100
        expected = f"Hello {long_name}"
        self.assertEqual(greet(long_name), expected)
    
    def test_single_character_names(self):
        """Test single character names."""
        self.assertEqual(greet("A"), "Hello A")
        self.assertEqual(greet("X"), "Hello X")
        self.assertEqual(greet("1"), "Hello 1")


def run_tests():
    """Run all unit tests and display results."""
    unittest.main(argv=[''], exit=False, verbosity=2)


# Usage Examples and Documentation
def demonstrate_usage():
    """
    Demonstrate various usage scenarios of the greet function.
    
    This function shows practical examples of how to use the greet function
    in different contexts and with various types of input.
    """
    print("=== Greeting Function Usage Examples ===\n")
    
    # Normal usage examples
    print("Normal Usage:")
    print(f"greet('Alice') -> {greet('Alice')}")
    print(f"greet('John Doe') -> {greet('John Doe')}")
    print(f"greet('Mary') -> {greet('Mary')}")
    print()
    
    # Edge case examples
    print("Edge Cases:")
    print(f"greet(None) -> {greet(None)}")
    print(f"greet('') -> {greet('')}")
    print(f"greet('   ') -> {greet('   ')}")
    print()
    
    # Special character examples
    print("Special Characters:")
    print(f"greet('José María') -> {greet('José María')}")
    print(f"greet('O\\'Connor') -> {greet('O\\'Connor')}")
    print(f"greet('Jean-Pierre') -> {greet('Jean-Pierre')}")
    print(f"greet('李小明') -> {greet('李小明')}")
    print()
    
    # Practical usage in applications
    print("Practical Application Examples:")
    
    # Simulating user input scenarios
    user_inputs = ["Alice", "", None, "  Bob  ", "User123", "José"]
    print("Processing various user inputs:")
    for user_input in user_inputs:
        result = greet(user_input)
        print(f"Input: {repr(user_input)} -> Output: {result}")


if __name__ == "__main__":
    # Demonstrate the function
    demonstrate_usage()
    
    print("\n" + "="*50)
    print("Running Unit Tests...")
    print("="*50)
    
    # Run the test suite
    run_tests()