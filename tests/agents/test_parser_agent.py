import pytest
from agents.parser_agent import run_parser_agent

def test_parser_agent_evaluation():
    """
    Evaluation for Sandeepa K.A.T (IT22581266)
    Validates that the Parser Agent accurately maps AST structures.
    """
    code = "def hello(name):\n    return f'Hello {name}'\n\nclass User:\n    pass"
    state = {
        "file_path": "test.py",
        "code_content": code
    }
    
    result = run_parser_agent(state)
    
    # Assertions for accuracy
    assert "parsed_data" in result
    parsed = result["parsed_data"]
    
    # Verify function detection
    funcs = [f["name"] for f in parsed.get("functions", [])]
    assert "hello" in funcs
    
    # Verify class detection
    classes = [c["name"] for c in parsed.get("classes", [])]
    assert "User" in classes
    
    # Verify metadata integrity
    assert result["code_content"] == code
