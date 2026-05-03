import pytest
from agents.security_agent import run_security_agent

def test_security_agent_evaluation():
    """
    Evaluation for Sathsara U.A.R (IT22585776)
    Validates that the Security Agent identifies critical vulnerabilities.
    """
    vulnerable_code = "import os\nos.system('rm -rf /')\npassword = '12345_admin_secret'"
    state = {
        "file_path": "vuln.py",
        "code_content": vulnerable_code,
        "use_ai": False
    }
    
    result = run_security_agent(state, llm=None)
    
    # Verify vulnerability detection
    assert len(result["security_issues"]) >= 2
    types = [i["type"] for i in result["security_issues"]]
    assert "command_injection" in types
    assert "hardcoded_secret" in types
    
    # Verify risk score logic
    assert "security_metadata" in result
    assert result["security_metadata"]["risk_score"] > 50
