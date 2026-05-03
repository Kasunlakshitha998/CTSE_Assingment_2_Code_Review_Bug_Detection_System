import pytest
from agents.fix_agent import run_fix_agent

def test_fix_agent_evaluation():
    """
    Evaluation for Lakshitha U.D.K (IT22564436)
    Validates that the Fix Agent generates remediation and final reports.
    """
    state = {
        "file_path": "demo.py",
        "code_content": "eval(x)",
        "bugs": [],
        "security_issues": [{"type": "unsafe_eval", "line": 1, "message": "Use of eval()"}],
        "use_ai": False
    }
    
    result = run_fix_agent(state, llm=None)
    
    # Verify fix generation
    assert len(result["fixes"]) > 0
    assert result["fixes"][0]["issue_type"] == "unsafe_eval"
    assert "suggested_fix" in result["fixes"][0]
    
    # Verify final report structure
    assert "final_report" in result
    assert result["final_report"]["summary"]["total_fixes"] == 1
