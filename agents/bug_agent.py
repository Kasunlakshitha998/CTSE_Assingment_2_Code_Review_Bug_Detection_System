"""
Bug Detector Agent - Detects bugs and bad practices in source code.

Uses the code_analyzer tool and the Ollama LLM to provide
comprehensive bug detection with severity scoring.
"""

import json
import logging
from typing import Dict, Any

from tools.code_analyzer import analyze_code_rules

logger = logging.getLogger("ai_code_review.agents.bug_agent")

# ---------------------------------------------------------------------------
# System prompt for the Bug Detector Agent
# ---------------------------------------------------------------------------
BUG_DETECTOR_SYSTEM_PROMPT = """You are the Bug Detector Agent in a multi-agent AI code review system.

YOUR ROLE:
- Analyze source code for bugs, bad practices, and logical mistakes
- Use the rule-checking tool output as your PRIMARY source of truth
- Enhance tool findings with additional context and explanations

STRICT RULES:
1. You MUST base your analysis on the tool output provided. Do NOT hallucinate bugs.
2. You MUST return ONLY valid JSON. Return raw JSON ONLY. No markdown formatting, no code blocks (e.g., do not use ```json), no preamble, and no postamble.
3. For each issue found by the tool, provide a clear explanation and severity.
4. You may add observations about code quality that the tool detected.
5. Do NOT invent issues that are not supported by the tool output.
6. Be deterministic - same input must produce same output.

OUTPUT FORMAT:
{
    "file": "<filename>",
    "bugs": [
        {
            "type": "...",
            "line": N,
            "message": "...",
            "severity": "low|medium|high",
            "explanation": "..."
        }
    ],
    "summary": {
        "total_issues": N,
        "severity": "low|medium|high",
        "complexity_rating": "low|medium|high"
    }
}"""


def _format_bugs_for_llm(analysis_result: Dict[str, Any], file_path: str) -> str:
    """Format the analysis results as a prompt context for the LLM.

    Args:
        analysis_result: Output from analyze_code_rules().
        file_path: Path to the file being analysed.

    Returns:
        Formatted string for LLM context.
    """
    parts = [f"File: {file_path}"]
    parts.append(f"Total issues found by tool: {analysis_result.get('issue_count', 0)}")
    parts.append(f"Overall severity: {analysis_result.get('severity', 'unknown')}")

    complexity = analysis_result.get("complexity", {})
    if complexity:
        parts.append(f"Complexity score: {complexity.get('score', 0)} ({complexity.get('rating', 'N/A')})")

    parts.append("\nDetailed issues:")
    for i, issue in enumerate(analysis_result.get("issues", []), 1):
        parts.append(f"  {i}. [{issue.get('severity', 'unknown').upper()}] "
                     f"{issue.get('type', 'unknown')} at line {issue.get('line', '?')}: "
                     f"{issue.get('message', 'No message')}")

    return "\n".join(parts)


def run_bug_agent(state: Dict[str, Any], llm=None) -> Dict[str, Any]:
    """Execute the Bug Detector Agent.

    Runs the code_analyzer tool on the code content from state,
    optionally enhances results using the LLM, and updates state.

    Args:
        state: Shared state dictionary with "code_content" and "parsed_data".
        llm: Optional Ollama LLM instance for enhanced analysis.

    Returns:
        Updated state dictionary with "bugs" populated.
    """
    file_path = state.get("file_path", "unknown")
    code_content = state.get("code_content", "")
    logger.info("=== BUG DETECTOR AGENT START ===")
    logger.info("Analyzing file: %s", file_path)

    if not code_content:
        state["bugs"] = [{
            "type": "error",
            "line": 0,
            "message": "No code content available for analysis.",
            "severity": "high",
            "explanation": "The parser agent did not provide code content.",
        }]
        logger.warning("No code content to analyze.")
        logger.info("=== BUG DETECTOR AGENT END ===")
        return state

    # Use the code analyzer tool
    analysis_result = analyze_code_rules(code_content)
    logger.info("Tool output: %d issues, severity=%s",
                analysis_result.get("issue_count", 0),
                analysis_result.get("severity", "unknown"))

    bugs = []

    if analysis_result["success"]:
        # Convert tool issues to bug format
        for issue in analysis_result.get("issues", []):
            bugs.append({
                "type": issue.get("type", "unknown"),
                "line": issue.get("line", 0),
                "message": issue.get("message", ""),
                "severity": issue.get("severity", "medium"),
                "explanation": issue.get("message", ""),
            })

        # If LLM is available and use_ai flag is enabled
        if llm is not None and state.get("use_ai", False):
            try:
                tool_context = _format_bugs_for_llm(analysis_result, file_path)
                prompt = (
                    f"{BUG_DETECTOR_SYSTEM_PROMPT}\n\n"
                    f"TOOL OUTPUT:\n{tool_context}\n\n"
                    f"CODE SNIPPET (first 2000 chars):\n"
                    f"```\n{code_content[:2000]}\n```\n\n"
                    f"Based on the tool output above, provide your analysis as valid JSON. "
                    f"Do NOT invent issues not found by the tool. Output ONLY valid JSON."
                )
                logger.info("Sending to LLM for enhanced analysis...")
                llm_response = llm.invoke(prompt)
                logger.info("LLM response received (%d chars)", len(str(llm_response)))

                # Try to parse LLM JSON response
                try:
                    # Extract JSON from response
                    resp = str(llm_response)
                    json_start = resp.find("{")
                    json_end = resp.rfind("}") + 1
                    if json_start >= 0 and json_end > json_start:
                        llm_data = json.loads(resp[json_start:json_end])
                        if "bugs" in llm_data and isinstance(llm_data["bugs"], list):
                            bugs = llm_data["bugs"]
                            logger.info("Using LLM-enhanced bug list (%d bugs)", len(bugs))
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning("Could not parse LLM response, using tool output: %s", e)

            except Exception as e:
                logger.warning("LLM call failed, using tool output only: %s", e)

    else:
        bugs.append({
            "type": "analysis_error",
            "line": 0,
            "message": analysis_result.get("error", "Analysis failed"),
            "severity": "medium",
            "explanation": "The code analyzer tool encountered an error.",
        })

    state["bugs"] = bugs
    state["analysis_metadata"] = {
        "complexity": analysis_result.get("complexity", {}),
        "categories": analysis_result.get("categories", {}),
    }

    logger.info("Bug detection complete: %d bugs found", len(bugs))
    logger.info("=== BUG DETECTOR AGENT END ===")
    return state
