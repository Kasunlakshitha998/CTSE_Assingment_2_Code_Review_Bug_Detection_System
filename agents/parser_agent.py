"""
Code Parser Agent - Reads and parses source code files.

Extracts code structure (functions, classes, imports, variables)
using the file_reader tool and AST parsing.
"""

import ast
import json
import logging
from typing import Dict, Any, List

from tools.file_reader import read_code_file

logger = logging.getLogger("ai_code_review.agents.parser_agent")

# ---------------------------------------------------------------------------
# System prompt for the Code Parser Agent
# ---------------------------------------------------------------------------
PARSER_SYSTEM_PROMPT = """You are the Code Parser Agent in a multi-agent AI code review system.

YOUR ROLE:
- Read source code files using the file reading tool
- Extract and report code structure: functions, classes, imports, global variables
- Provide accurate structural metadata for downstream agents

STRICT RULES:
1. You MUST rely ONLY on the tool output. Do NOT hallucinate or invent code elements.
2. You MUST return ONLY valid JSON in the exact format specified.
3. Report ALL functions, classes, imports, and global variables found in the code.
4. If the file cannot be read, report the error in JSON format.
5. Be deterministic - same input must produce same output.

OUTPUT FORMAT:
{
    "file": "<filename>",
    "status": "success" | "error",
    "structure": {
        "functions": [{"name": "...", "line": N, "params": [...], "decorators": [...]}],
        "classes": [{"name": "...", "line": N, "methods": [...], "bases": [...]}],
        "imports": [{"module": "...", "names": [...], "line": N}],
        "global_variables": [{"name": "...", "line": N}]
    },
    "metadata": {
        "total_lines": N,
        "total_functions": N,
        "total_classes": N,
        "file_size_bytes": N
    },
    "error": null
}"""


def _extract_structure(source: str) -> Dict[str, Any]:
    """Extract code structure from source using AST.

    Args:
        source: Python source code string.

    Returns:
        Dictionary with functions, classes, imports, global_variables.
    """
    structure: Dict[str, Any] = {
        "functions": [],
        "classes": [],
        "imports": [],
        "global_variables": [],
    }

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        logger.warning("SyntaxError during parsing: %s", e)
        return structure

    for node in ast.iter_child_nodes(tree):
        # Functions
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            params = [arg.arg for arg in node.args.args]
            decorators = []
            for dec in node.decorator_list:
                if isinstance(dec, ast.Name):
                    decorators.append(dec.id)
                elif isinstance(dec, ast.Attribute):
                    decorators.append(ast.dump(dec))
            structure["functions"].append({
                "name": node.name,
                "line": node.lineno,
                "params": params,
                "decorators": decorators,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
            })

        # Classes
        elif isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(item.name)
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(ast.dump(base))
            structure["classes"].append({
                "name": node.name,
                "line": node.lineno,
                "methods": methods,
                "bases": bases,
            })

        # Imports
        elif isinstance(node, ast.Import):
            for alias in node.names:
                structure["imports"].append({
                    "module": alias.name,
                    "alias": alias.asname,
                    "line": node.lineno,
                })
        elif isinstance(node, ast.ImportFrom):
            names = [alias.name for alias in node.names]
            structure["imports"].append({
                "module": node.module or "",
                "names": names,
                "line": node.lineno,
            })

        # Global variables (top-level assignments)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    structure["global_variables"].append({
                        "name": target.id,
                        "line": node.lineno,
                    })

    return structure


def run_parser_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the Code Parser Agent.

    Reads the file specified in state["file_path"], extracts structure,
    and updates the shared state.

    Args:
        state: Shared state dictionary containing at minimum "file_path".

    Returns:
        Updated state dictionary with "code_content" and "parsed_data".
    """
    file_path = state.get("file_path", "")
    logger.info("=== CODE PARSER AGENT START ===")
    logger.info("Input file: %s", file_path)

    # Use the file reader tool
    file_result = read_code_file(file_path)
    logger.info("File reader result: success=%s", file_result["success"])

    if not file_result["success"]:
        error_msg = file_result.get("error", "Unknown error reading file")
        parsed_data = {
            "file": file_path,
            "status": "error",
            "structure": {"functions": [], "classes": [], "imports": [], "global_variables": []},
            "metadata": {"total_lines": 0, "total_functions": 0, "total_classes": 0, "file_size_bytes": 0},
            "error": error_msg,
        }
        state["code_content"] = ""
        state["parsed_data"] = parsed_data
        logger.error("Parser agent failed: %s", error_msg)
        logger.info("=== CODE PARSER AGENT END ===")
        return state

    content = file_result["content"]
    structure = _extract_structure(content)

    parsed_data = {
        "file": file_path,
        "status": "success",
        "structure": structure,
        "metadata": {
            "total_lines": file_result["lines"],
            "total_functions": len(structure["functions"]),
            "total_classes": len(structure["classes"]),
            "file_size_bytes": file_result["size_bytes"],
        },
        "error": None,
    }

    state["code_content"] = content
    state["parsed_data"] = parsed_data

    logger.info("Parsed: %d functions, %d classes, %d imports",
                len(structure["functions"]),
                len(structure["classes"]),
                len(structure["imports"]))
    logger.info("=== CODE PARSER AGENT END ===")
    return state
