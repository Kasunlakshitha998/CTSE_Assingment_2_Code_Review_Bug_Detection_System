"""
Security Analyzer Agent - Identifies security vulnerabilities.

Uses the security_tool to scan for hardcoded secrets, SQL injection,
eval/exec abuse, command injection, and other security issues.
"""

import json
import logging
from typing import Dict, Any

from tools.security_tool import security_scan

logger = logging.getLogger("ai_code_review.agents.security_agent")

# ---------------------------------------------------------------------------
# System prompt for the Security Analyzer Agent
# ---------------------------------------------------------------------------
SECURITY_SYSTEM_PROMPT = """You are the Security Analyzer Agent in a multi-agent AI code review system.

YOUR ROLE:
- Analyze source code for security vulnerabilities
- Use the security scanning tool output as your PRIMARY source of truth
- Classify vulnerabilities by severity and provide remediation advice

STRICT RULES:
1. You MUST base your analysis on the security tool output. Do NOT hallucinate vulnerabilities.
2. You MUST return ONLY valid JSON. Return raw JSON ONLY. No markdown formatting, no code blocks (e.g., do not use ```json), no preamble, and no postamble.
3. For each vulnerability found, provide severity, explanation, and remediation.
4. Prioritize HIGH severity issues (hardcoded secrets, SQL injection, eval abuse).
5. Do NOT invent vulnerabilities not found by the tool.
6. Be deterministic - same input must produce same output.

OUTPUT FORMAT:
{
    "file": "<filename>",
    "security_issues": [
        {
            "type": "...",
            "line": N,
            "message": "...",
            "severity": "low|medium|high",
            "remediation": "..."
        }
    ],
    "risk_summary": {
        "total_vulnerabilities": N,
        "risk_score": N,
        "severity": "low|medium|high"
    }
}"""


def _format_vulns_for_llm(scan_result: Dict[str, Any], file_path: str) -> str:
    """Format security scan results as LLM prompt context."""
    parts = [f"File: {file_path}"]
    parts.append(f"Total vulnerabilities: {scan_result.get('vulnerability_count', 0)}")
    parts.append(f"Risk score: {scan_result.get('risk_score', 0)}")
    parts.append(f"Overall severity: {scan_result.get('severity', 'unknown')}")
    parts.append("\nDetailed vulnerabilities:")
    for i, vuln in enumerate(scan_result.get("vulnerabilities", []), 1):
        parts.append(
            f"  {i}. [{vuln.get('severity', '?').upper()}] "
            f"{vuln.get('type', 'unknown')} at line {vuln.get('line', '?')}: "
            f"{vuln.get('message', 'No message')}"
        )
        if vuln.get("code_snippet"):
            parts.append(f"     Code: {vuln['code_snippet']}")
    return "\n".join(parts)


def run_security_agent(state: Dict[str, Any], llm=None) -> Dict[str, Any]:
    """Execute the Security Analyzer Agent.

    Runs the security_scan tool on code content from state,
    optionally enhances results using the LLM, and updates state.

    Args:
        state: Shared state dict with "code_content".
        llm: Optional Ollama LLM instance.

    Returns:
        Updated state with "security_issues" populated.
    """
    file_path = state.get("file_path", "unknown")
    code_content = state.get("code_content", "")
    logger.info("=== SECURITY ANALYZER AGENT START ===")
    logger.info("Scanning file: %s", file_path)

    if not code_content:
        state["security_issues"] = [{
            "type": "error",
            "line": 0,
            "message": "No code content available for security scan.",
            "severity": "high",
            "remediation": "Ensure the parser agent provides code content.",
        }]
        logger.warning("No code content for security scan.")
        logger.info("=== SECURITY ANALYZER AGENT END ===")
        return state

    # Use the security tool
    scan_result = security_scan(code_content)
    logger.info("Tool output: %d vulnerabilities, risk_score=%s",
                scan_result.get("vulnerability_count", 0),
                scan_result.get("risk_score", 0))

    security_issues = []

    if scan_result["success"]:
        for vuln in scan_result.get("vulnerabilities", []):
            security_issues.append({
                "type": vuln.get("type", "unknown"),
                "line": vuln.get("line", 0),
                "message": vuln.get("message", ""),
                "severity": vuln.get("severity", "medium"),
                "code_snippet": vuln.get("code_snippet", ""),
                "remediation": "",
            })

        # LLM enhancement
        if llm is not None and security_issues and state.get("use_ai", False):
            try:
                tool_context = _format_vulns_for_llm(scan_result, file_path)
                prompt = (
                    f"{SECURITY_SYSTEM_PROMPT}\n\n"
                    f"TOOL OUTPUT:\n{tool_context}\n\n"
                    f"CODE SNIPPET (first 2000 chars):\n"
                    f"```\n{code_content[:2000]}\n```\n\n"
                    f"Based on the tool output above, provide your security analysis "
                    f"as valid JSON. Include remediation advice for each vulnerability. "
                    f"Do NOT invent vulnerabilities not found by the tool. Output ONLY valid JSON."
                )
                logger.info("Sending to LLM for enhanced security analysis...")
                llm_response = llm.invoke(prompt)
                logger.info("LLM response received (%d chars)", len(str(llm_response)))

                try:
                    resp = str(llm_response)
                    json_start = resp.find("{")
                    json_end = resp.rfind("}") + 1
                    if json_start >= 0 and json_end > json_start:
                        llm_data = json.loads(resp[json_start:json_end])
                        if "security_issues" in llm_data:
                            security_issues = llm_data["security_issues"]
                            logger.info("Using LLM-enhanced security issues (%d)", len(security_issues))
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning("Could not parse LLM response: %s", e)
            except Exception as e:
                logger.warning("LLM call failed: %s", e)
    else:
        security_issues.append({
            "type": "scan_error",
            "line": 0,
            "message": scan_result.get("error", "Security scan failed"),
            "severity": "medium",
            "remediation": "Check tool configuration.",
        })

    state["security_issues"] = security_issues
    state["security_metadata"] = {
        "risk_score": scan_result.get("risk_score", 0),
        "categories": scan_result.get("categories", {}),
    }

    logger.info("Security analysis complete: %d issues found", len(security_issues))
    logger.info("=== SECURITY ANALYZER AGENT END ===")
    return state
