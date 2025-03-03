"""
Example module to demonstrate local module imports in the LSP server
"""

def add(a, b):
    """Add two numbers and return the result."""
    return a + b

def subtract(a, b):
    """Subtract b from a and return the result."""
    return a - b

def multiply(a, b):
    """Multiply two numbers and return the result."""
    return a * b

def divide(a, b):
    """Divide a by b and return the result."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

class Calculator:
    """A simple calculator class."""
    
    def __init__(self, initial_value=0):
        """Initialize with an optional starting value."""
        self.value = initial_value
    
    def add(self, number):
        """Add a number to the current value."""
        self.value += number
        return self.value
    
    def subtract(self, number):
        """Subtract a number from the current value."""
        self.value -= number
        return self.value
    
    def reset(self):
        """Reset the calculator to zero."""
        self.value = 0
        return self.value
    
    def get_value(self):
        """Return the current value."""
        return self.value