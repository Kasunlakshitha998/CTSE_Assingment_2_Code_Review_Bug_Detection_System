# AI Code Review & Bug Detection System

A complete Multi-Agent System (MAS) for automated code parsing, bug detection, security analysis, and fix generation using LangGraph and Ollama (llama3:8b).

## Architecture overview
- **Code Parser Agent**: Safely reads files and extracts AST structure (functions, classes, variables, imports).
- **Bug Detector Agent**: Uses rule-based static analysis to detect code smells (long functions, unused variables, deep nesting) and enhances findings via Ollama.
- **Security Analyzer Agent**: Scans for vulnerabilities (SQL injection, hardcoded secrets, eval abuse) using regex patterns, with LLM enhancements for remediation.
- **Fix Suggestion Agent**: Aggregates all issues and generates concrete, actionable fixes.

## Strict LLM Formatting
Based on the feedback, all agent prompts have been optimized to strictly enforce valid JSON output for `llama3:8b`. The LLM is explicitly instructed to avoid markdown code blocks, preambles, postambles, and hallucinations.

## Key Features
- **Local Execution Only**: Uses Ollama (llama3:8b) with deterministic configuration (`temperature=0.2`).
- **LangGraph Orchestration**: Agents are connected in a sequential pipeline sharing a global state dictionary.
- **Robust Custom Tools**: Contains production-ready tools (`file_reader`, `code_analyzer`, `security_tool`) with strict typing, error handling, and `pytest` coverage.
- **Complete Test Suite**: Comprehensive `pytest` test suite covering valid, invalid, and edge-cases.

## How to Run the System

The project can be run entirely locally. You have two options: use the **Command Line Interface (CLI)** or the **Modern React Dashboard**.

### Option 1: Full-Stack Web Dashboard (Recommended)

You need to run both the FastAPI backend and the React frontend simultaneously in two separate terminals.

**Terminal 1: Start the AI Backend**
```bash
# Ensure you are in the root directory (AI-Code-Review)
# Install API dependencies if you haven't yet: pip install fastapi uvicorn
uvicorn api:app --reload --port 8000
```
*Note: The first request may take a moment as it initializes the LLM workflow.*

**Terminal 2: Start the React Frontend**
```bash
# Go into the frontend folder
cd frontend

# Install dependencies (only needed the first time)
npm install

# Start the Vite development server
npm run dev
```
Open your browser to `http://localhost:5173` (or the URL provided in the terminal). You can now drag and drop Python files into the UI for instant AI code review!

### Option 2: Command Line Interface (CLI)

To run the full pipeline directly on a Python file via terminal:
```bash
python main.py path/to/your_file.py
```
*(If no file is provided, it defaults to analyzing the bundled `sample_code.py` file which is packed with intentional vulnerabilities for demonstration purposes.)*

Check `logs/agent.log` for complete execution traces and `logs/report.json` for the final structured JSON output.

### Running the Test Suite
The project includes a robust PyTest suite covering the core validation, parsing, and analysis logic.
```bash
pytest tests/test_tools.py -v
```
