"""
Code Analyzer Tool - Detects code quality issues and bad practices.

Uses AST-based analysis for: long functions, unused variables,
bad naming, deep nesting, duplicate code, and complexity scoring.
"""

import re
import ast
import logging
from typing import Dict, Any, List
from collections import Counter

logger = logging.getLogger("ai_code_review.tools.code_analyzer")

MAX_FUNCTION_LINES = 30
MAX_FUNCTION_PARAMS = 5
MAX_NESTING_DEPTH = 4
MIN_DUPLICATE_LINES = 4
VARIABLE_NAME_MIN_LENGTH = 2


def _severity(count: int) -> str:
    """Return severity label based on issue count."""
    if count == 0:
        return "low"
    elif count <= 3:
        return "medium"
    return "high"


def _detect_long_functions(source: str) -> List[Dict[str, Any]]:
    """Detect functions exceeding MAX_FUNCTION_LINES."""
    issues = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return issues
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno
            end = max(
                (getattr(child, "end_lineno", None) or getattr(child, "lineno", start))
                for child in ast.walk(node)
                if hasattr(child, "lineno")
            )
            length = end - start + 1
            if length > MAX_FUNCTION_LINES:
                issues.append({
                    "type": "long_function",
                    "function": node.name,
                    "line": start,
                    "length": length,
                    "threshold": MAX_FUNCTION_LINES,
                    "message": f"Function '{node.name}' is {length} lines long (max {MAX_FUNCTION_LINES}).",
                    "severity": "medium",
                })
    return issues


def _detect_too_many_params(source: str) -> List[Dict[str, Any]]:
    """Detect functions with too many parameters."""
    issues = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return issues
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            params = node.args
            total = len(params.args) + len(params.posonlyargs) + len(params.kwonlyargs)
            if params.args and params.args[0].arg in ("self", "cls"):
                total -= 1
            if total > MAX_FUNCTION_PARAMS:
                issues.append({
                    "type": "too_many_parameters",
                    "function": node.name,
                    "line": node.lineno,
                    "param_count": total,
                    "threshold": MAX_FUNCTION_PARAMS,
                    "message": f"Function '{node.name}' has {total} parameters (max {MAX_FUNCTION_PARAMS}).",
                    "severity": "medium",
                })
    return issues


def _detect_bad_naming(source: str) -> List[Dict[str, Any]]:
    """Detect variables/functions/classes with poor naming conventions."""
    issues = []
    allowed_short = {"i", "j", "k", "x", "y", "z", "e", "f", "_"}
    snake_re = re.compile(r"^_{0,2}[a-z][a-z0-9_]*_{0,2}$")
    pascal_re = re.compile(r"^[A-Z][a-zA-Z0-9]*$")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return issues
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            if len(node.id) < VARIABLE_NAME_MIN_LENGTH and node.id not in allowed_short:
                issues.append({
                    "type": "bad_variable_name", "name": node.id,
                    "line": node.lineno,
                    "message": f"Variable '{node.id}' is too short (min {VARIABLE_NAME_MIN_LENGTH} chars).",
                    "severity": "low",
                })
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("__") and not snake_re.match(node.name):
                issues.append({
                    "type": "bad_function_name", "name": node.name,
                    "line": node.lineno,
                    "message": f"Function '{node.name}' does not follow snake_case.",
                    "severity": "low",
                })
        if isinstance(node, ast.ClassDef):
            if not pascal_re.match(node.name):
                issues.append({
                    "type": "bad_class_name", "name": node.name,
                    "line": node.lineno,
                    "message": f"Class '{node.name}' does not follow PascalCase.",
                    "severity": "low",
                })
    return issues


def _detect_unused_variables(source: str) -> List[Dict[str, Any]]:
    """Detect variables assigned but never used."""
    issues = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return issues
    assigned: Dict[str, int] = {}
    loaded: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Store):
                if node.id not in assigned:
                    assigned[node.id] = node.lineno
            elif isinstance(node.ctx, ast.Load):
                loaded.add(node.id)
    for name, line in assigned.items():
        if name.startswith("_"):
            continue
        if name not in loaded:
            issues.append({
                "type": "unused_variable", "name": name, "line": line,
                "message": f"Variable '{name}' is assigned but never used.",
                "severity": "medium",
            })
    return issues


def _detect_deep_nesting(source: str) -> List[Dict[str, Any]]:
    """Detect deeply nested control-flow blocks."""
    issues = []
    nesting_kw = {"if", "for", "while", "with", "try", "elif", "else", "except"}
    for idx, line in enumerate(source.splitlines(), start=1):
        stripped = line.lstrip()
        first_word = stripped.split("(")[0].split(":")[0].split(" ")[0]
        if first_word in nesting_kw:
            indent = len(line) - len(stripped)
            depth = indent // 4
            if depth >= MAX_NESTING_DEPTH:
                issues.append({
                    "type": "deep_nesting", "line": idx, "depth": depth,
                    "threshold": MAX_NESTING_DEPTH,
                    "message": f"Code at line {idx} is nested {depth} levels deep (max {MAX_NESTING_DEPTH}).",
                    "severity": "medium",
                })
    return issues


def _detect_duplicate_blocks(source: str) -> List[Dict[str, Any]]:
    """Detect duplicate consecutive code blocks."""
    issues = []
    lines = [l.strip() for l in source.splitlines() if l.strip() and not l.strip().startswith("#")]
    if len(lines) < MIN_DUPLICATE_LINES * 2:
        return issues
    seen: Dict[str, int] = {}
    for i in range(len(lines) - MIN_DUPLICATE_LINES + 1):
        block = "\n".join(lines[i : i + MIN_DUPLICATE_LINES])
        if block in seen:
            issues.append({
                "type": "duplicate_code",
                "first_occurrence_line": seen[block] + 1,
                "duplicate_line": i + 1,
                "block_size": MIN_DUPLICATE_LINES,
                "message": f"Duplicate code block at line {i+1} (first at line {seen[block]+1}).",
                "severity": "medium",
            })
        else:
            seen[block] = i
    return issues


def _compute_complexity_score(source: str) -> Dict[str, Any]:
    """Compute basic complexity score from AST."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {"score": 0, "details": "Could not parse code."}
    c: Counter = Counter()
    for node in ast.walk(tree):
        if isinstance(node, ast.If): c["if"] += 1
        elif isinstance(node, ast.For): c["for"] += 1
        elif isinstance(node, ast.While): c["while"] += 1
        elif isinstance(node, ast.Try): c["try"] += 1
        elif isinstance(node, ast.ExceptHandler): c["except"] += 1
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)): c["functions"] += 1
        elif isinstance(node, ast.ClassDef): c["classes"] += 1
        elif isinstance(node, ast.BoolOp): c["bool_ops"] += 1
    score = c["if"] + c["for"]*2 + c["while"]*2 + c["try"] + c["except"] + c["bool_ops"]
    return {
        "score": score,
        "branches": c["if"], "loops": c["for"]+c["while"],
        "exception_handlers": c["try"]+c["except"],
        "functions": c["functions"], "classes": c["classes"],
        "rating": "low" if score < 10 else ("medium" if score < 25 else "high"),
    }


def analyze_code_rules(code: str) -> Dict[str, Any]:
    """Perform rule-based static analysis on Python source code.

    Args:
        code (str): Raw Python source code to analyse.

    Returns:
        Dict[str, Any]: Analysis results with keys: success, issues,
            issue_count, severity, complexity, categories, error.

    Raises:
        This function does not raise exceptions.
    """
    result: Dict[str, Any] = {
        "success": False, "issues": [], "issue_count": 0,
        "severity": "low", "complexity": {}, "categories": {}, "error": None,
    }
    try:
        if not code or not isinstance(code, str):
            result["error"] = "Invalid input: code must be a non-empty string."
            logger.error(result["error"])
            return result
        all_issues: List[Dict[str, Any]] = []
        all_issues.extend(_detect_long_functions(code))
        all_issues.extend(_detect_too_many_params(code))
        all_issues.extend(_detect_bad_naming(code))
        all_issues.extend(_detect_unused_variables(code))
        all_issues.extend(_detect_deep_nesting(code))
        all_issues.extend(_detect_duplicate_blocks(code))
        complexity = _compute_complexity_score(code)
        categories: Counter = Counter()
        for issue in all_issues:
            categories[issue["type"]] += 1
        result["success"] = True
        result["issues"] = all_issues
        result["issue_count"] = len(all_issues)
        result["severity"] = _severity(len(all_issues))
        result["complexity"] = complexity
        result["categories"] = dict(categories)
        logger.info("Code analysis complete: %d issues (severity: %s)", len(all_issues), result["severity"])
        return result
    except Exception as exc:
        result["error"] = f"Analysis failed: {exc}"
        logger.exception(result["error"])
        return result
