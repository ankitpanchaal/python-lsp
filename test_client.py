"""
Simple test client for Python LSP server
"""
import requests
import json
import os

# LSP server endpoint
LSP_SERVER_URL = "http://localhost:8000"

def get_completions(code, line, character):
    """
    Get code completions at the specified position.
    
    Args:
        code (str): The Python code
        line (int): 0-based line number
        character (int): 0-based character position
    
    Returns:
        List of completion items
    """
    endpoint = f"{LSP_SERVER_URL}/completion"
    
    data = {
        "text_document": {
            "text": code
        },
        "position": {
            "line": line,
            "character": character
        }
    }
    
    response = requests.post(endpoint, json=data)
    if response.status_code == 200:
        return response.json()["items"]
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return []

def get_diagnostics(code):
    """
    Get diagnostic information (syntax errors) for the given code.
    
    Args:
        code (str): The Python code
    
    Returns:
        List of diagnostic items
    """
    endpoint = f"{LSP_SERVER_URL}/diagnostic"
    
    data = {
        "text": code
    }
    
    response = requests.post(endpoint, json=data)
    if response.status_code == 200:
        return response.json()["diagnostics"]
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return []

def test_completions(title, code, line, character, max_display=10):
    """Test completions for the given code and position"""
    print(f"\n=== TESTING {title} ===")
    print(f"Code: {code.strip()}")
    print(f"Position: Line {line}, Character {character}")
    
    completions = get_completions(code, line, character)
    
    if completions:
        print(f"Found {len(completions)} completions, showing first {min(max_display, len(completions))}:")
        for i, item in enumerate(completions):
            if i >= max_display:
                print(f"  ... {len(completions) - max_display} more items not shown")
                break
            print(f"  - {item['label']} ({item['detail']})")
    else:
        print("No completions found.")
    
    return completions

def main():
    print("Testing Python LSP Client")
    print("=========================")
    
    # Check if pandas and numpy are installed
    try:
        import pandas
        pandas_installed = True
        print("pandas is installed")
    except ImportError:
        pandas_installed = False
        print("pandas is NOT installed - install with 'pip install pandas' to test pandas completions")
    
    try:
        import numpy
        numpy_installed = True
        print("numpy is installed")
    except ImportError:
        numpy_installed = False
        print("numpy is NOT installed - install with 'pip install numpy' to test numpy completions")
    
    # Example code with syntax error
    code_with_error = """
def hello():
    print("Hello, world!")
    
# This line has a syntax error
if True
    print("This is broken")
    
hello()
"""
    
    # Example code for completions that uses local module
    code_local_module = """import example_module

example_module."""
    
    # Example code for pandas completions
    code_pandas = """import pandas as pd

df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
df."""
    
    # Example code for numpy completions
    code_numpy = """import numpy as np

arr = np.array([1, 2, 3])
arr."""
    
    # Test getting diagnostics (syntax errors)
    print("\n=== TESTING DIAGNOSTICS ===")
    diagnostics = get_diagnostics(code_with_error)
    if diagnostics:
        for diag in diagnostics:
            line = diag["range"]["start"]["line"]
            char = diag["range"]["start"]["character"]
            print(f"Syntax error at line {line}, char {char}: {diag['message']}")
    else:
        print("No syntax errors found.")
    
    # Test getting completions for local module
    test_completions("LOCAL MODULE COMPLETIONS", code_local_module, 2, 14)
    
    # Test getting completions for pandas
    if pandas_installed:
        test_completions("PANDAS COMPLETIONS", code_pandas, 3, 3)
    
    # Test getting completions for numpy
    if numpy_installed:
        test_completions("NUMPY COMPLETIONS", code_numpy, 3, 4)

if __name__ == "__main__":
    main()