from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import tempfile
import logging

from main import build_workflow, init_llm

app = FastAPI(title="AI Code Review API")

# Setup CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM and Workflow on startup
print("Initializing LLM...")
llm = init_llm(max_retries=1, retry_delay=1.0)
workflow = build_workflow(llm=llm)
print("Workflow ready.")

class AnalyzeRequest(BaseModel):
    code: str
    use_ai: bool = False

@app.post("/analyze")
async def analyze_code(request: AnalyzeRequest):
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty.")
        
    # We need to save the code to a temporary file because the file_reader tool expects a file path
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(request.code)
        temp_file_path = temp_file.name

    try:
        initial_state = {
            "file_path": temp_file_path,
            "code_content": "",
            "use_ai": request.use_ai,
            "parsed_data": {},
            "bugs": [],
            "security_issues": [],
            "fixes": [],
            "final_report": "",
            "analysis_metadata": {},
            "security_metadata": {},
        }
        
        # Execute the LangGraph workflow
        final_state = workflow.invoke(initial_state)
        report = final_state.get("final_report", {})
        
        # Extract logs (mocking logs here since we didn't capture stdout in the agent execution)
        logs = [
            "[START] AI Code Review & Bug Detection System",
            f"[TARGET] Target file: {temp_file_path}",
            "[Node] Code Parser Agent",
            f"Parsed: {len(report.get('parsed_structure', {}).get('functions', []))} functions",
            "[Node] Bug Detector Agent",
            f"Bugs found: {len(report.get('bugs', []))}",
            "[Node] Security Analyzer Agent",
            f"Security issues found: {len(report.get('security_issues', []))}",
            "[Node] Fix Suggestion Agent",
            f"Fixes generated: {len(report.get('fixes', []))}",
            "[END] Pipeline completed successfully."
        ]
        
        return {
            "parsed_data": report.get("parsed_structure", {}),
            "bugs": report.get("bugs", []),
            "security_issues": report.get("security_issues", []),
            "fixes": report.get("fixes", []),
            "summary": report.get("summary", {}),
            "logs": logs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temp file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
