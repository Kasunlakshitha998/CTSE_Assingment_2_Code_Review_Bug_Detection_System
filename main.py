"""
AI Code Review & Bug Detection System - Main Orchestration

Uses LangGraph to orchestrate 4 agents in a sequential pipeline:
  Code Parser → Bug Detector → Security Analyzer → Fix Suggestion

All agents share a global state dictionary and communicate through it.
Ollama (llama3:8b) is used as the local LLM backend.
"""

import os
import sys
import json
import time
import logging
from typing import TypedDict, Dict, Any, List, Optional

from langgraph.graph import StateGraph, END

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "agent.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-40s | %(levelname)-7s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("ai_code_review.main")


# ---------------------------------------------------------------------------
# Import agents
# ---------------------------------------------------------------------------
from agents.parser_agent import run_parser_agent
from agents.bug_agent import run_bug_agent
from agents.security_agent import run_security_agent
from agents.fix_agent import run_fix_agent


# ---------------------------------------------------------------------------
# Global state definition
# ---------------------------------------------------------------------------
class ReviewState(TypedDict, total=False):
    """Shared state passed between all agents in the pipeline."""
    file_path: str
    code_content: str
    parsed_data: Dict[str, Any]
    bugs: List[Dict[str, Any]]
    security_issues: List[Dict[str, Any]]
    fixes: List[Dict[str, Any]]
    final_report: Any
    analysis_metadata: Dict[str, Any]
    security_metadata: Dict[str, Any]


# ---------------------------------------------------------------------------
# Ollama LLM initialisation (with retry logic)
# ---------------------------------------------------------------------------
def init_llm(max_retries: int = 3, retry_delay: float = 2.0):
    """Initialise the Ollama LLM with retry logic.

    Args:
        max_retries: Maximum number of connection attempts.
        retry_delay: Seconds to wait between retries.

    Returns:
        Ollama LLM instance or None if connection fails.
    """
    for attempt in range(1, max_retries + 1):
        try:
            from langchain_community.llms import Ollama
            llm = Ollama(
                model="llama3:8b",
                temperature=0.2,
            )
            # Quick test to verify connection
            logger.info("Testing Ollama connection (attempt %d/%d)...", attempt, max_retries)
            llm.invoke("Say OK")
            logger.info("Ollama connection successful.")
            return llm
        except Exception as e:
            logger.warning("Ollama connection attempt %d/%d failed: %s", attempt, max_retries, e)
            if attempt < max_retries:
                time.sleep(retry_delay)
    logger.error(
        "Could not connect to Ollama after %d attempts. "
        "Running in tool-only mode (no LLM enhancement).",
        max_retries,
    )
    return None


# ---------------------------------------------------------------------------
# LangGraph node wrappers
# ---------------------------------------------------------------------------
# We need closures so nodes can access the LLM instance.

def create_parser_node():
    """Create the parser agent node function."""
    def parser_node(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[Node] Code Parser Agent")
        return run_parser_agent(state)
    return parser_node


def create_bug_node(llm):
    """Create the bug detector agent node function."""
    def bug_node(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[Node] Bug Detector Agent")
        return run_bug_agent(state, llm=llm)
    return bug_node


def create_security_node(llm):
    """Create the security analyzer agent node function."""
    def security_node(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[Node] Security Analyzer Agent")
        return run_security_agent(state, llm=llm)
    return security_node


def create_fix_node(llm):
    """Create the fix suggestion agent node function."""
    def fix_node(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[Node] Fix Suggestion Agent")
        return run_fix_agent(state, llm=llm)
    return fix_node


# ---------------------------------------------------------------------------
# Build LangGraph workflow
# ---------------------------------------------------------------------------
def build_workflow(llm=None) -> StateGraph:
    """Build the LangGraph workflow with all four agent nodes.

    Pipeline: parser → bug_detector → security_analyzer → fix_suggester → END

    Args:
        llm: Optional Ollama LLM instance.

    Returns:
        Compiled LangGraph StateGraph.
    """
    workflow = StateGraph(dict)

    # Add nodes
    workflow.add_node("parser", create_parser_node())
    workflow.add_node("bug_detector", create_bug_node(llm))
    workflow.add_node("security_analyzer", create_security_node(llm))
    workflow.add_node("fix_suggester", create_fix_node(llm))

    # Define edges (sequential pipeline)
    workflow.set_entry_point("parser")
    workflow.add_edge("parser", "bug_detector")
    workflow.add_edge("bug_detector", "security_analyzer")
    workflow.add_edge("security_analyzer", "fix_suggester")
    workflow.add_edge("fix_suggester", END)

    return workflow.compile()


# ---------------------------------------------------------------------------
# Pretty-print final report
# ---------------------------------------------------------------------------
def print_report(report: Dict[str, Any]) -> None:
    """Print a human-readable final report to the console.

    Args:
        report: The final_report dictionary from state.
    """
    print("\n" + "=" * 70)
    print("  AI CODE REVIEW & BUG DETECTION REPORT")
    print("=" * 70)

    summary = report.get("summary", {})
    print(f"\n[FILE]:           {report.get('file', 'N/A')}")
    print(f"[BUGS]:           {summary.get('total_bugs', 0)}")
    print(f"[SECURITY]:       {summary.get('total_security_issues', 0)}")
    print(f"[FIXES]:          {summary.get('total_fixes', 0)}")
    print(f"[SEVERITY]:       {summary.get('overall_severity', 'N/A').upper()}")

    complexity = summary.get("complexity", {})
    if complexity:
        print(f"[COMPLEXITY]:     {complexity.get('score', 'N/A')} ({complexity.get('rating', 'N/A')})")

    # Parsed structure summary
    structure = report.get("parsed_structure", {})
    if structure:
        funcs = structure.get("functions", [])
        classes = structure.get("classes", [])
        print(f"\n[CODE STRUCTURE]:")
        print(f"   Functions: {len(funcs)}")
        print(f"   Classes:   {len(classes)}")
        for fn in funcs:
            print(f"     - {fn.get('name', '?')}({', '.join(fn.get('params', []))}) @ line {fn.get('line', '?')}")
        for cls in classes:
            print(f"     - class {cls.get('name', '?')} @ line {cls.get('line', '?')}: "
                  f"methods={cls.get('methods', [])}")

    # Bugs
    bugs = report.get("bugs", [])
    if bugs:
        print(f"\n[BUGS] ({len(bugs)}):")
        print("-" * 50)
        for i, bug in enumerate(bugs, 1):
            sev = bug.get("severity", "?").upper()
            print(f"  {i}. [{sev}] {bug.get('type', 'unknown')} @ line {bug.get('line', '?')}")
            print(f"     {bug.get('message', '')}")

    # Security issues
    sec_issues = report.get("security_issues", [])
    if sec_issues:
        print(f"\n[SECURITY ISSUES] ({len(sec_issues)}):")
        print("-" * 50)
        for i, issue in enumerate(sec_issues, 1):
            sev = issue.get("severity", "?").upper()
            print(f"  {i}. [{sev}] {issue.get('type', 'unknown')} @ line {issue.get('line', '?')}")
            print(f"     {issue.get('message', '')}")
            if issue.get("code_snippet"):
                print(f"     Code: {issue['code_snippet']}")

    # Fixes
    fixes = report.get("fixes", [])
    if fixes:
        print(f"\n[FIX SUGGESTIONS] ({len(fixes)}):")
        print("-" * 50)
        for i, fix in enumerate(fixes, 1):
            sev = fix.get("severity", "?").upper()
            print(f"  {i}. [{sev}] {fix.get('issue_type', 'unknown')} @ line {fix.get('line', '?')}")
            print(f"     Problem:  {fix.get('current_problem', '')}")
            print(f"     Fix:      {fix.get('suggested_fix', '')}")
            if fix.get("code_example"):
                print(f"     Example:")
                for eline in fix["code_example"].split("\n"):
                    print(f"       {eline}")

    print("\n" + "=" * 70)
    print("  END OF REPORT")
    print("=" * 70 + "\n")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main():
    """Run the AI Code Review pipeline on a target file."""
    print("\n[START] AI Code Review & Bug Detection System")
    print("=" * 45)

    # Determine target file
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
    else:
        # Default: analyse the sample file
        target_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "sample_code.py",
        )
        print(f"No file specified. Using default: {target_file}")

    target_file = os.path.abspath(target_file)
    print(f"[TARGET] Target file: {target_file}\n")

    if not os.path.exists(target_file):
        print(f"[ERROR] Error: File not found: {target_file}")
        sys.exit(1)

    # Initialise LLM
    print("[INIT] Initialising Ollama (llama3:8b)...")
    llm = init_llm(max_retries=3, retry_delay=2.0)
    if llm is None:
        print("[WARN] Running in tool-only mode (no LLM enhancement).\n")
    else:
        print("[OK] Ollama connected.\n")

    # Build workflow
    print("[BUILD] Building LangGraph workflow...")
    app = build_workflow(llm=llm)
    print("[OK] Workflow ready.\n")

    # Initial state
    initial_state: Dict[str, Any] = {
        "file_path": target_file,
        "code_content": "",
        "parsed_data": {},
        "bugs": [],
        "security_issues": [],
        "fixes": [],
        "final_report": "",
        "analysis_metadata": {},
        "security_metadata": {},
    }

    # Execute pipeline
    print("[RUN] Running agent pipeline...")
    print("   Parser -> Bug Detector -> Security Analyzer -> Fix Suggester\n")
    start_time = time.time()

    final_state = app.invoke(initial_state)

    elapsed = time.time() - start_time
    print(f"\n[TIME] Pipeline completed in {elapsed:.2f} seconds.")

    # Output report
    final_report = final_state.get("final_report", {})
    if final_report:
        print_report(final_report)

        # Save JSON report
        report_path = os.path.join(LOG_DIR, "report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(final_report, f, indent=2, default=str)
        print(f"[FILE] JSON report saved to: {report_path}")
    else:
        print("[ERROR] No report generated.")

    logger.info("Pipeline finished in %.2f seconds.", elapsed)


if __name__ == "__main__":
    main()
