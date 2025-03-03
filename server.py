from typing import Dict, List, Optional
from pydantic import BaseModel
import jedi
import ast
from fastapi import FastAPI, HTTPException
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Python Jedi LSP Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, you may want to restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define data models for the API following LSP specifications
class Position(BaseModel):
    """Represents a position in a text document (0-based indexing)."""
    line: int        # 0-based line number
    character: int   # 0-based character offset within the line

class TextDocument(BaseModel):
    """Represents a text document/file content."""
    text: str        # full text content of the document

class CompletionParams(BaseModel):
    """Parameters required for completion requests."""
    text_document: TextDocument  # The document to get completions for
    position: Position           # The cursor position to get completions at

class CompletionItem(BaseModel):
    """A single completion item to be presented in the IDE."""
    label: str                     # The text to be displayed and inserted
    kind: int                      # Type of completion item (function, variable, etc.)
    detail: Optional[str] = None   # Additional details (e.g., type information)
    documentation: Optional[str] = None  # Documentation string if available

class Diagnostic(BaseModel):
    """Represents a detected issue in the code."""
    range: Dict[str, Dict[str, int]]  # Affected text range (start/end positions)
    message: str                      # Description of the issue
    severity: int                     # 1: Error, 2: Warning, 3: Info, 4: Hint

class CompletionResponse(BaseModel):
    """Response containing completion suggestions."""
    items: List[CompletionItem]

class DiagnosticResponse(BaseModel):
    """Response containing diagnostic information."""
    diagnostics: List[Diagnostic]

# Mapping of Jedi completion types to LSP completion kinds
# LSP defines specific numeric codes for different completion item types
COMPLETION_KINDS = {
    'module': 9, 'class': 7, 'instance': 6, 'function': 3,
    'param': 6, 'path': 17, 'keyword': 14, 'property': 10, 'method': 2
}

def get_completion_kind(type_name: str) -> int:
    """
    Convert Jedi completion type names to LSP completion kind numbers.
    If type_name is not found in the mapping, defaults to 1 (Text).
    """
    return COMPLETION_KINDS.get(type_name, 1)  # Default to 1 (Text)

def create_range(line, column, end_line=None, end_column=None):
    """
    Create an LSP-compatible range object representing a region in the text.
    A range has start and end positions, each with line and character properties.
    """
    end_line = end_line or line
    end_column = end_column or column + 1
    return {
        "start": {"line": line, "character": column},
        "end": {"line": end_line, "character": end_column}
    }

def get_virtual_path(document_text):
    """
    Generate a virtual file path for in-memory document content.
    
    Jedi works better with files that have paths. For unsaved or temporary
    content, we create a virtual path based on the content hash to ensure
    consistency across requests for the same content.
    """
    import hashlib
    content_hash = hashlib.md5(document_text.encode()).hexdigest()
    
    return f"<virtual_document_{content_hash}.py>"


@app.post("/completion", response_model=CompletionResponse)
async def provide_completion(params: CompletionParams):
    """
    Endpoint that provides code completion suggestions.
    
    Analyzes the document content and cursor position to generate appropriate
    completion suggestions using Jedi's code intelligence.
    """
    try:
        # Extract parameters from the request
        document_text = params.text_document.text
        # Convert from 0-based (LSP) to 1-based line numbers (Jedi)
        line = params.position.line + 1
        character = params.position.character
        
        # Generate a virtual path to help Jedi with module resolution
        path = get_virtual_path(document_text)
        
        # Create Jedi Script object to analyze the code
        script = jedi.Script(code=document_text, path=path)
        
        # Get completions at the current cursor position
        completions = script.complete(line, character)
        
        # Convert Jedi completions to LSP-compatible completion items
        completion_items = []
        for completion in completions:
            item = CompletionItem(
                label=completion.name,
                kind=get_completion_kind(completion.type),
                detail=completion.type,
                documentation=completion.docstring()
            )
            completion_items.append(item)
        
        print(f"Found {len(completion_items)} completions")
        
        return CompletionResponse(items=completion_items)
    
    except Exception as e:
        # Provide detailed error information for debugging
        import traceback
        print("Error in completion:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Completion error: {str(e)}")

@app.post("/diagnostic", response_model=DiagnosticResponse)
async def provide_diagnostics(params: TextDocument):
    """
    Endpoint that provides syntax diagnostics for the given document.
    
    Currently detects Python syntax errors using the built-in ast module.
    Could be extended in the future for more sophisticated static analysis.
    """
    document_text = params.text
    diagnostics = []
    
    # Check for syntax errors by attempting to parse the Python code
    try:
        ast.parse(document_text)
    except SyntaxError as e:
        # Convert the Python syntax error to an LSP diagnostic
        # Convert from 1-based (Python) to 0-based indices (LSP)
        line = e.lineno - 1 if e.lineno is not None else 0
        col = e.offset - 1 if e.offset is not None else 0
        
        # Ensure indices are valid (non-negative)
        if line < 0: line = 0
        if col < 0: col = 0
            
        # Create the diagnostic object with the error details
        diagnostic = Diagnostic(
            range=create_range(line, col),
            message=str(e),
            severity=1  # Error severity
        )
        diagnostics.append(diagnostic)
    
    return DiagnosticResponse(diagnostics=diagnostics)

if __name__ == "__main__":
    print(f"Starting Python LSP server on http://localhost:8000")
    print(f"Server will provide completions for installed libraries (including pandas and numpy if installed)")
    print(f"Press Ctrl+C to exit")
    uvicorn.run(app, host="0.0.0.0", port=8000)