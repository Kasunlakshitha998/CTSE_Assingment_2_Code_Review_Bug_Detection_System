"""
Security Scanning Tool - Detects security vulnerabilities in source code.

Scans for: hardcoded secrets/passwords, unsafe eval/exec usage,
SQL injection patterns, command injection, path traversal,
insecure imports, and debug leftovers.
"""

import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger("ai_code_review.tools.security_tool")


# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

# Hardcoded secrets / passwords
SECRET_PATTERNS = [
    (r"""(?i)(password|passwd|pwd|secret|api_key|apikey|token|auth_token|access_key|secret_key)\s*=\s*["'][^"']{3,}["']""",
     "Hardcoded secret or password detected."),
    (r"""(?i)(password|passwd|pwd|secret|api_key|apikey|token)\s*:\s*["'][^"']{3,}["']""",
     "Hardcoded secret in dict/config detected."),
]

# Unsafe eval / exec
EVAL_PATTERNS = [
    (r"""\beval\s*\(""", "Use of eval() detected – potential code injection risk."),
    (r"""\bexec\s*\(""", "Use of exec() detected – potential code injection risk."),
    (r"""\bcompile\s*\(.*,\s*["']exec["']\)""", "Use of compile() with exec mode detected."),
]

# SQL injection
SQL_PATTERNS = [
    (r"""(?i)(execute|cursor\.execute)\s*\(\s*["'].*%s""",
     "Possible SQL injection via string formatting (%s)."),
    (r"""(?i)(execute|cursor\.execute)\s*\(\s*["'].*\+\s*""",
     "Possible SQL injection via string concatenation."),
    (r"""(?i)(execute|cursor\.execute)\s*\(\s*f["']""",
     "Possible SQL injection via f-string."),
    (r"""(?i)(execute|cursor\.execute)\s*\(\s*["'].*\.format\(""",
     "Possible SQL injection via .format()."),
]

# Command injection
CMD_PATTERNS = [
    (r"""\bos\.system\s*\(""", "Use of os.system() – risk of command injection."),
    (r"""\bsubprocess\.call\s*\(.*shell\s*=\s*True""",
     "subprocess with shell=True – risk of command injection."),
    (r"""\bsubprocess\.Popen\s*\(.*shell\s*=\s*True""",
     "subprocess.Popen with shell=True – risk of command injection."),
    (r"""\bos\.popen\s*\(""", "Use of os.popen() – risk of command injection."),
]

# Path traversal
PATH_PATTERNS = [
    (r"""\.\.\/|\.\.\\""", "Potential path traversal pattern detected."),
    (r"""\bopen\s*\(.*\+.*\)""",
     "Dynamic file open with concatenation – possible path traversal."),
]

# Insecure imports
IMPORT_PATTERNS = [
    (r"""import\s+pickle""", "Use of pickle – potential deserialization vulnerability."),
    (r"""from\s+pickle\s+import""", "Use of pickle – potential deserialization vulnerability."),
    (r"""import\s+shelve""", "Use of shelve – uses pickle internally."),
    (r"""import\s+marshal""", "Use of marshal – unsafe deserialization."),
]

# Debug leftovers
DEBUG_PATTERNS = [
    (r"""(?i)#\s*TODO.*hack""", "TODO comment referencing a hack found."),
    (r"""\bbreakpoint\s*\(\s*\)""", "breakpoint() call left in code."),
    (r"""\bpdb\.set_trace\s*\(\s*\)""", "pdb.set_trace() left in code."),
    (r"""\bprint\s*\(\s*["']debug""", "Debug print statement detected."),
]


def _scan_patterns(
    code: str,
    patterns: List[tuple],
    category: str,
    severity: str,
) -> List[Dict[str, Any]]:
    """Scan code against a list of regex patterns.

    Args:
        code: Source code string.
        patterns: List of (regex, message) tuples.
        category: Category label for found issues.
        severity: Severity label.

    Returns:
        List of issue dicts.
    """
    issues: List[Dict[str, Any]] = []
    lines = code.splitlines()
    for pattern_str, message in patterns:
        try:
            pattern = re.compile(pattern_str)
        except re.error:
            continue
        for idx, line in enumerate(lines, start=1):
            if pattern.search(line):
                issues.append({
                    "type": category,
                    "line": idx,
                    "code_snippet": line.strip()[:120],
                    "message": message,
                    "severity": severity,
                })
    return issues


def security_scan(code: str) -> Dict[str, Any]:
    """Perform a security scan on source code.

    Detects hardcoded secrets, unsafe eval/exec, SQL injection,
    command injection, path traversal, insecure imports, and
    debug leftovers.

    Args:
        code (str): Raw source code to scan.

    Returns:
        Dict[str, Any]: Results with keys: success, vulnerabilities,
            vulnerability_count, severity, categories, risk_score, error.

    Raises:
        This function does not raise exceptions.
    """
    result: Dict[str, Any] = {
        "success": False,
        "vulnerabilities": [],
        "vulnerability_count": 0,
        "severity": "low",
        "categories": {},
        "risk_score": 0,
        "error": None,
    }
    try:
        if not code or not isinstance(code, str):
            result["error"] = "Invalid input: code must be a non-empty string."
            logger.error(result["error"])
            return result

        all_vulns: List[Dict[str, Any]] = []
        all_vulns.extend(_scan_patterns(code, SECRET_PATTERNS, "hardcoded_secret", "high"))
        all_vulns.extend(_scan_patterns(code, EVAL_PATTERNS, "unsafe_eval", "high"))
        all_vulns.extend(_scan_patterns(code, SQL_PATTERNS, "sql_injection", "high"))
        all_vulns.extend(_scan_patterns(code, CMD_PATTERNS, "command_injection", "high"))
        all_vulns.extend(_scan_patterns(code, PATH_PATTERNS, "path_traversal", "medium"))
        all_vulns.extend(_scan_patterns(code, IMPORT_PATTERNS, "insecure_import", "medium"))
        all_vulns.extend(_scan_patterns(code, DEBUG_PATTERNS, "debug_leftover", "low"))

        # De-duplicate by (line, type)
        seen = set()
        unique: List[Dict[str, Any]] = []
        for v in all_vulns:
            key = (v["line"], v["type"])
            if key not in seen:
                seen.add(key)
                unique.append(v)

        # Risk score
        score_map = {"high": 10, "medium": 5, "low": 1}
        risk_score = sum(score_map.get(v["severity"], 0) for v in unique)

        # Categories
        cats: Dict[str, int] = {}
        for v in unique:
            cats[v["type"]] = cats.get(v["type"], 0) + 1

        # Overall severity
        if any(v["severity"] == "high" for v in unique):
            overall = "high"
        elif any(v["severity"] == "medium" for v in unique):
            overall = "medium"
        else:
            overall = "low"

        result["success"] = True
        result["vulnerabilities"] = unique
        result["vulnerability_count"] = len(unique)
        result["severity"] = overall if unique else "low"
        result["categories"] = cats
        result["risk_score"] = risk_score

        logger.info("Security scan complete: %d vulnerabilities (severity: %s)", len(unique), result["severity"])
        return result

    except Exception as exc:
        result["error"] = f"Security scan failed: {exc}"
        logger.exception(result["error"])
        return result
