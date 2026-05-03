"""
Test suite for the AI Code Review tools.

Tests cover:
- file_reader: valid file, invalid file, edge cases
- code_analyzer: clean code, buggy code, edge cases
- security_tool: clean code, vulnerable code, edge cases

Run with: pytest tests/test_tools.py -v
"""

import os
import sys
import tempfile
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.file_reader import read_code_file
from tools.code_analyzer import analyze_code_rules
from tools.security_tool import security_scan


# =========================================================================
# Fixtures
# =========================================================================

@pytest.fixture
def sample_python_file(tmp_path):
    """Create a temporary valid Python file."""
    code = '''
def hello(name):
    """Greet someone."""
    return f"Hello, {name}!"

class MyClass:
    def __init__(self):
        self.value = 42
'''
    file_path = tmp_path / "valid_sample.py"
    file_path.write_text(code, encoding="utf-8")
    return str(file_path)


@pytest.fixture
def buggy_python_file(tmp_path):
    """Create a temporary Python file with known bugs."""
    code = '''
import os

a = 10
unused_var = "never used"

def CalculateTotal(a, b, c, d, e, f, g):
    result = a + b + c
    return result

def process():
    if True:
        if True:
            if True:
                if True:
                    if True:
                        print("deep")
'''
    file_path = tmp_path / "buggy_sample.py"
    file_path.write_text(code, encoding="utf-8")
    return str(file_path)


@pytest.fixture
def vulnerable_python_code():
    """Return Python code with known security issues."""
    return '''
import pickle
import os

DB_PASSWORD = "super_secret_123"
api_key = "sk-abcdef1234567890"

def unsafe_eval(user_input):
    return eval(user_input)

def get_user(cursor, name):
    cursor.execute(f"SELECT * FROM users WHERE name='{name}'")

def run_cmd(path):
    os.system(f"ls {path}")

def debug():
    breakpoint()
'''


@pytest.fixture
def clean_python_code():
    """Return clean, well-written Python code."""
    return '''
import logging

logger = logging.getLogger(__name__)

def calculate_area(width: float, height: float) -> float:
    """Calculate area of a rectangle."""
    return width * height

class Rectangle:
    """A simple rectangle class."""
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height

    def area(self) -> float:
        """Return the area."""
        return self.width * self.height
'''


# =========================================================================
# Test: file_reader tool
# =========================================================================

class TestFileReader:
    """Tests for the read_code_file tool."""

    def test_valid_file(self, sample_python_file):
        """Test reading a valid Python file."""
        result = read_code_file(sample_python_file)
        assert result["success"] is True
        assert result["content"] != ""
        assert result["lines"] > 0
        assert result["size_bytes"] > 0
        assert result["extension"] == ".py"
        assert result["error"] is None

    def test_file_not_found(self):
        """Test reading a non-existent file."""
        result = read_code_file("/nonexistent/path/fake.py")
        assert result["success"] is False
        assert "not found" in result["error"].lower() or "not found" in result["error"]

    def test_empty_path(self):
        """Test with an empty file path."""
        result = read_code_file("")
        assert result["success"] is False
        assert result["error"] is not None

    def test_none_path(self):
        """Test with None as file path."""
        result = read_code_file(None)
        assert result["success"] is False
        assert result["error"] is not None

    def test_unsupported_extension(self, tmp_path):
        """Test with an unsupported file extension."""
        file_path = tmp_path / "test.xyz"
        file_path.write_text("some content")
        result = read_code_file(str(file_path))
        assert result["success"] is False
        assert "unsupported" in result["error"].lower()

    def test_empty_file(self, tmp_path):
        """Test with an empty file."""
        file_path = tmp_path / "empty.py"
        file_path.write_text("")
        result = read_code_file(str(file_path))
        assert result["success"] is False
        assert "empty" in result["error"].lower()

    def test_directory_path(self, tmp_path):
        """Test with a directory instead of a file."""
        result = read_code_file(str(tmp_path))
        assert result["success"] is False
        assert "not a file" in result["error"].lower()

    def test_file_content_integrity(self, tmp_path):
        """Test that file content is read correctly."""
        content = "print('Hello, World!')\n"
        file_path = tmp_path / "integrity.py"
        file_path.write_text(content, encoding="utf-8")
        result = read_code_file(str(file_path))
        assert result["success"] is True
        assert result["content"] == content


# =========================================================================
# Test: code_analyzer tool
# =========================================================================

class TestCodeAnalyzer:
    """Tests for the analyze_code_rules tool."""

    def test_clean_code(self, clean_python_code):
        """Test analysis of clean code produces few or no issues."""
        result = analyze_code_rules(clean_python_code)
        assert result["success"] is True
        assert result["error"] is None
        # Clean code should have minimal issues
        assert result["issue_count"] <= 2

    def test_buggy_code_detects_issues(self):
        """Test that buggy code is flagged."""
        buggy = '''
a = 10
unused_var = "never used"

def CalculateTotal(a, b, c, d, e, f, g):
    result = a + b
    return result
'''
        result = analyze_code_rules(buggy)
        assert result["success"] is True
        assert result["issue_count"] > 0
        types = [i["type"] for i in result["issues"]]
        assert "bad_function_name" in types or "too_many_parameters" in types

    def test_long_function_detection(self):
        """Test detection of excessively long functions."""
        lines = ["    x = 1"] * 35
        code = "def long_function():\n" + "\n".join(lines)
        result = analyze_code_rules(code)
        assert result["success"] is True
        long_funcs = [i for i in result["issues"] if i["type"] == "long_function"]
        assert len(long_funcs) > 0

    def test_unused_variable_detection(self):
        """Test detection of unused variables."""
        code = '''
def example():
    unused = 42
    used = 10
    return used
'''
        result = analyze_code_rules(code)
        assert result["success"] is True
        unused = [i for i in result["issues"] if i["type"] == "unused_variable"]
        assert len(unused) > 0

    def test_complexity_scoring(self, clean_python_code):
        """Test that complexity is computed."""
        result = analyze_code_rules(clean_python_code)
        assert result["success"] is True
        assert "complexity" in result
        assert "score" in result["complexity"]
        assert "rating" in result["complexity"]

    def test_empty_input(self):
        """Test with empty code string."""
        result = analyze_code_rules("")
        assert result["success"] is False
        assert result["error"] is not None

    def test_none_input(self):
        """Test with None input."""
        result = analyze_code_rules(None)
        assert result["success"] is False
        assert result["error"] is not None

    def test_syntax_error_handling(self):
        """Test that syntax errors don't crash the analyzer."""
        broken = "def broken(:\n    pass"
        result = analyze_code_rules(broken)
        assert result["success"] is True  # Should still succeed
        assert result["error"] is None

    def test_categories_populated(self):
        """Test that categories dict is populated correctly."""
        code = '''
a = 10
unused = 42

def BadName():
    return a
'''
        result = analyze_code_rules(code)
        assert result["success"] is True
        assert isinstance(result["categories"], dict)

    def test_severity_levels(self):
        """Test severity scoring logic."""
        code = "x = 1\nprint(x)"  # minimal code
        result = analyze_code_rules(code)
        assert result["severity"] in ("low", "medium", "high")


# =========================================================================
# Test: security_tool
# =========================================================================

class TestSecurityTool:
    """Tests for the security_scan tool."""

    def test_clean_code_no_vulns(self, clean_python_code):
        """Test that clean code has no security vulnerabilities."""
        result = security_scan(clean_python_code)
        assert result["success"] is True
        assert result["vulnerability_count"] == 0
        assert result["severity"] == "low"

    def test_hardcoded_password(self):
        """Test detection of hardcoded passwords."""
        code = 'password = "my_secret_password"'
        result = security_scan(code)
        assert result["success"] is True
        assert result["vulnerability_count"] > 0
        types = [v["type"] for v in result["vulnerabilities"]]
        assert "hardcoded_secret" in types

    def test_eval_detection(self):
        """Test detection of eval() usage."""
        code = 'result = eval(user_input)'
        result = security_scan(code)
        assert result["success"] is True
        types = [v["type"] for v in result["vulnerabilities"]]
        assert "unsafe_eval" in types

    def test_sql_injection_fstring(self):
        """Test detection of SQL injection via f-string."""
        code = '''cursor.execute(f"SELECT * FROM users WHERE id={uid}")'''
        result = security_scan(code)
        assert result["success"] is True
        types = [v["type"] for v in result["vulnerabilities"]]
        assert "sql_injection" in types

    def test_command_injection(self):
        """Test detection of command injection via os.system."""
        code = 'os.system(f"ls {path}")'
        result = security_scan(code)
        assert result["success"] is True
        types = [v["type"] for v in result["vulnerabilities"]]
        assert "command_injection" in types

    def test_multiple_vulnerabilities(self, vulnerable_python_code):
        """Test detection of multiple vulnerability types."""
        result = security_scan(vulnerable_python_code)
        assert result["success"] is True
        assert result["vulnerability_count"] >= 3
        types = set(v["type"] for v in result["vulnerabilities"])
        assert len(types) >= 2  # At least 2 different types

    def test_risk_score_calculation(self, vulnerable_python_code):
        """Test that risk score is calculated."""
        result = security_scan(vulnerable_python_code)
        assert result["success"] is True
        assert result["risk_score"] > 0

    def test_empty_input(self):
        """Test with empty code string."""
        result = security_scan("")
        assert result["success"] is False
        assert result["error"] is not None

    def test_none_input(self):
        """Test with None input."""
        result = security_scan(None)
        assert result["success"] is False
        assert result["error"] is not None

    def test_pickle_import_detection(self):
        """Test detection of insecure pickle import."""
        code = "import pickle\ndata = pickle.loads(raw)"
        result = security_scan(code)
        assert result["success"] is True
        types = [v["type"] for v in result["vulnerabilities"]]
        assert "insecure_import" in types

    def test_breakpoint_detection(self):
        """Test detection of debug breakpoints."""
        code = "def test():\n    breakpoint()\n    return 42"
        result = security_scan(code)
        assert result["success"] is True
        types = [v["type"] for v in result["vulnerabilities"]]
        assert "debug_leftover" in types

    def test_severity_classification(self, vulnerable_python_code):
        """Test that severity is correctly classified."""
        result = security_scan(vulnerable_python_code)
        assert result["severity"] in ("low", "medium", "high")
        # Vulnerable code should be high severity
        assert result["severity"] == "high"

    def test_categories_populated(self, vulnerable_python_code):
        """Test that categories dict is populated."""
        result = security_scan(vulnerable_python_code)
        assert isinstance(result["categories"], dict)
        assert len(result["categories"]) > 0
