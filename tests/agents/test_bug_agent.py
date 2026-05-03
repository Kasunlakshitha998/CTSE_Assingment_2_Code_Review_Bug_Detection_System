import pytest
from agents.bug_agent import run_bug_agent

def test_bug_agent_evaluation():
    """
    Evaluation for L.A.S. Maddumage (IT22601742)
    Validates that the Bug Agent detects quality issues and respects AI toggle.
    """
    buggy_code = "def very_long_function():\n" + "    print('line')\n" * 40
    state = {
        "file_path": "buggy.py",
        "code_content": buggy_code,
        "use_ai": False # Testing rule-based speed
    }
    
    result = run_bug_agent(state, llm=None)
    
    # Verify bug detection
    assert len(result["bugs"]) > 0
    bug_types = [b["type"] for b in result["bugs"]]
    assert "long_function" in bug_types
    
    # Verify complexity metadata
    assert "analysis_metadata" in result
    assert result["analysis_metadata"]["complexity"]["score"] > 0
