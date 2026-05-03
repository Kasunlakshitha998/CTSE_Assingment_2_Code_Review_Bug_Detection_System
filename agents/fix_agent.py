"""
Fix Suggestion Agent - Suggests improvements and fixes for detected issues.

Aggregates bugs and security issues from previous agents, then
uses the LLM to generate actionable fix recommendations.
"""

import json
import logging
from typing import Dict, Any, List
from tools.fix_engine import generate_remediations

logger = logging.getLogger("ai_code_review.agents.fix_agent")

# ---------------------------------------------------------------------------
# System prompt for the Fix Suggestion Agent
# ---------------------------------------------------------------------------
FIX_SYSTEM_PROMPT = """You are the Fix Suggestion Agent in a multi-agent AI code review system.

YOUR ROLE:
- Review all bugs and security issues found by previous agents
- Generate specific, actionable fix recommendations for each issue
- Prioritize fixes by severity (high > medium > low)
- Provide code examples where possible

STRICT RULES:
1. You MUST base your suggestions on the bugs and security issues provided. Do NOT invent new issues.
2. You MUST return ONLY valid JSON. Return raw JSON ONLY. No markdown formatting, no code blocks (e.g., do not use ```json), no preamble, and no postamble.
3. Each fix must reference the original issue type and line number.
4. Provide concrete, implementable suggestions.
5. Be deterministic - same input must produce same output.

OUTPUT FORMAT:
{
    "file": "<filename>",
    "fixes": [
        {
            "issue_type": "...",
            "line": N,
            "severity": "low|medium|high",
            "current_problem": "...",
            "suggested_fix": "...",
            "code_example": "..."
        }
    ],
    "summary": "...",
    "overall_severity": "low|medium|high"
}"""


def run_fix_agent(state: Dict[str, Any], llm=None) -> Dict[str, Any]:
    """Execute the Fix Suggestion Agent.

    Aggregates bugs and security issues, generates fix suggestions,
    and compiles the final report.

    Args:
        state: Shared state dict with "bugs" and "security_issues".
        llm: Optional Ollama LLM instance.

    Returns:
        Updated state with "fixes" and "final_report".
    """
    file_path = state.get("file_path", "unknown")
    bugs = state.get("bugs", [])
    security_issues = state.get("security_issues", [])
    logger.info("=== FIX SUGGESTION AGENT START ===")
    logger.info("Processing %d bugs and %d security issues", len(bugs), len(security_issues))

    # Generate rule-based fixes as baseline
    fixes = generate_remediations(bugs, security_issues)

    # LLM enhancement
    if llm is not None and (bugs or security_issues) and state.get("use_ai", False):
        try:
            issues_text = json.dumps({"bugs": bugs, "security_issues": security_issues}, indent=2)
            code_snippet = state.get("code_content", "")[:2000]
            prompt = (
                f"{FIX_SYSTEM_PROMPT}\n\n"
                f"ISSUES FOUND:\n{issues_text}\n\n"
                f"CODE SNIPPET:\n```\n{code_snippet}\n```\n\n"
                f"Generate fix suggestions for ALL issues above as valid JSON. "
                f"Do NOT invent issues. Output ONLY valid JSON."
            )
            logger.info("Sending to LLM for fix suggestions...")
            llm_response = llm.invoke(prompt)
            logger.info("LLM response received (%d chars)", len(str(llm_response)))

            try:
                resp = str(llm_response)
                json_start = resp.find("{")
                json_end = resp.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    llm_data = json.loads(resp[json_start:json_end])
                    if "fixes" in llm_data and isinstance(llm_data["fixes"], list):
                        fixes = llm_data["fixes"]
                        logger.info("Using LLM-enhanced fixes (%d)", len(fixes))
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("Could not parse LLM response: %s", e)
        except Exception as e:
            logger.warning("LLM call failed: %s", e)

    state["fixes"] = fixes

    # Compile final report
    overall_severity = "low"
    if any(f.get("severity") == "high" for f in fixes):
        overall_severity = "high"
    elif any(f.get("severity") == "medium" for f in fixes):
        overall_severity = "medium"

    final_report = {
        "file": file_path,
        "summary": {
            "total_bugs": len(bugs),
            "total_security_issues": len(security_issues),
            "total_fixes": len(fixes),
            "overall_severity": overall_severity,
            "complexity": state.get("analysis_metadata", {}).get("complexity", {"score": 0, "rating": "low"}),
        },
        "parsed_structure": state.get("parsed_data", {}),
        "bugs": bugs,
        "security_issues": security_issues,
        "fixes": fixes,
    }

    state["final_report"] = final_report
    logger.info("Final report generated: %d total fixes, severity=%s", len(fixes), overall_severity)
    logger.info("=== FIX SUGGESTION AGENT END ===")
    return state
