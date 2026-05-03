"""
Fix Engine Tool - Provides rule-based remediation templates for detected issues.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger("ai_code_review.tools.fix_engine")

# ---------------------------------------------------------------------------
# Rule-based fix suggestions
# ---------------------------------------------------------------------------

FIX_TEMPLATES: Dict[str, Dict[str, str]] = {
    "long_function": {
        "suggested_fix": "Break the function into smaller, focused helper functions. Each function should do one thing well.",
        "code_example": "# Instead of one long function:\ndef process_data(data):\n    # ... 50 lines ...\n\n# Split into:\ndef validate_data(data): ...\ndef transform_data(data): ...\ndef save_data(data): ...",
    },
    "too_many_parameters": {
        "suggested_fix": "Group related parameters into a dataclass or dictionary. Consider using **kwargs for optional params.",
        "code_example": "# Instead of:\ndef func(a, b, c, d, e, f): ...\n\n# Use:\n@dataclass\nclass Config:\n    a: str\n    b: int\n    ...\n\ndef func(config: Config): ...",
    },
    "bad_variable_name": {
        "suggested_fix": "Use descriptive variable names that convey meaning. Follow PEP 8 naming conventions.",
        "code_example": "# Instead of: a = 10\n# Use: max_retries = 10",
    },
    "bad_function_name": {
        "suggested_fix": "Rename the function to use snake_case as per PEP 8.",
        "code_example": "# Instead of: def MyFunction():\n# Use: def my_function():",
    },
    "bad_class_name": {
        "suggested_fix": "Rename the class to use PascalCase as per PEP 8.",
        "code_example": "# Instead of: class my_class:\n# Use: class MyClass:",
    },
    "unused_variable": {
        "suggested_fix": "Remove the unused variable or prefix with underscore if intentionally unused.",
        "code_example": "# Remove: unused_var = compute()\n# Or prefix: _unused_var = compute()",
    },
    "deep_nesting": {
        "suggested_fix": "Reduce nesting by using early returns, guard clauses, or extracting nested logic into functions.",
        "code_example": "# Instead of deeply nested if/else:\nif not condition:\n    return\n# ... rest of logic at lower indent",
    },
    "duplicate_code": {
        "suggested_fix": "Extract the duplicated code into a reusable function.",
        "code_example": "# Extract common logic:\ndef common_operation(params): ...\n\n# Call in both places:\ncommon_operation(args1)\ncommon_operation(args2)",
    },
    "hardcoded_secret": {
        "suggested_fix": "Move secrets to environment variables or a .env file. Use python-dotenv.",
        "code_example": "import os\nfrom dotenv import load_dotenv\nload_dotenv()\n\npassword = os.getenv('DB_PASSWORD')",
    },
    "unsafe_eval": {
        "suggested_fix": "Replace eval/exec with safer alternatives like ast.literal_eval or json.loads.",
        "code_example": "# Instead of: eval(user_input)\n# Use: ast.literal_eval(user_input)\n# Or: json.loads(user_input)",
    },
    "sql_injection": {
        "suggested_fix": "Use parameterized queries instead of string formatting.",
        "code_example": "# Instead of: cursor.execute(f'SELECT * FROM users WHERE id={uid}')\n# Use: cursor.execute('SELECT * FROM users WHERE id=?', (uid,))",
    },
    "command_injection": {
        "suggested_fix": "Use subprocess with a list of args and shell=False. Validate all inputs.",
        "code_example": "# Instead of: os.system(f'ls {path}')\n# Use: subprocess.run(['ls', path], shell=False)",
    },
    "path_traversal": {
        "suggested_fix": "Validate and sanitize file paths. Use os.path.realpath to resolve symlinks.",
        "code_example": "import os\nbase = '/safe/dir'\npath = os.path.realpath(os.path.join(base, user_input))\nassert path.startswith(base)",
    },
    "insecure_import": {
        "suggested_fix": "Avoid pickle for untrusted data. Use JSON or a safer serialization format.",
        "code_example": "# Instead of: import pickle\n# Use: import json\ndata = json.loads(raw_data)",
    },
    "debug_leftover": {
        "suggested_fix": "Remove debug statements before committing to production.",
        "code_example": "# Remove: breakpoint()\n# Remove: pdb.set_trace()\n# Use proper logging: logger.debug('...')",
    },
}

def generate_remediations(
    bugs: List[Dict[str, Any]],
    security_issues: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Generate fix suggestions using rule-based templates.
    """
    fixes = []
    all_issues = []

    for bug in bugs:
        all_issues.append(("bug", bug))
    for sec in security_issues:
        all_issues.append(("security", sec))

    # Sort by severity: high first
    severity_order = {"high": 0, "medium": 1, "low": 2}
    all_issues.sort(key=lambda x: severity_order.get(x[1].get("severity", "low"), 3))

    for source, issue in all_issues:
        issue_type = issue.get("type", "unknown")
        template = FIX_TEMPLATES.get(issue_type, {})

        fixes.append({
            "issue_type": issue_type,
            "line": issue.get("line", 0),
            "severity": issue.get("severity", "medium"),
            "current_problem": issue.get("message", "Issue detected"),
            "suggested_fix": template.get("suggested_fix", "Review and refactor this code section."),
            "code_example": template.get("code_example", ""),
            "source": source,
        })

    return fixes
