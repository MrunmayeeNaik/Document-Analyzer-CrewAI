import os
import uuid

from crewai import Crew, Process
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from agents import financial_analyst
from database import Analysis, SessionLocal
from task import analyze_financial_document as analyze_financial_task

app = FastAPI(title="Financial Document Analyzer")


def run_crew(query: str, file_path: str) -> str:
    """Run the financial analysis crew synchronously."""
    financial_crew = Crew(
        agents=[financial_analyst],
        tasks=[analyze_financial_task],
        process=Process.sequential,
    )
    result = financial_crew.kickoff({"query": query, "file_path": file_path})
    return str(result)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Financial Document Analyzer API is running"}


@app.post("/analyze")
def analyze_endpoints(
    file: UploadFile = File(...),
    query: str = Form(
        default="Analyze this financial document for investment insights"
    ),
):
    """Analyze financial document and return the result directly."""

    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"

    try:
        os.makedirs("data", exist_ok=True)

        with open(file_path, "wb") as f:
            content = file.file.read()
            f.write(content)

        if not query or not query.strip():
            query = "Analyze this financial document for investment insights"

        analysis = run_crew(query=query.strip(), file_path=file_path)
        # Save to database
        db = SessionLocal()
        new_record = Analysis(
            file_name=file.filename,
            query=query.strip(),
            analysis=analysis,
        )
        db.add(new_record)
        db.commit()
        db.close()

        return {
            "status": "success",
            "query": query,
            "analysis": analysis,
            "file_processed": file.filename,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing financial document: {e!s}",
        )
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                # Ignore cleanup errors
                pass


@app.get("/history")
def get_history():
    db = SessionLocal()
    records = db.query(Analysis).all()
    db.close()

    return [
        {
            "id": r.id,
            "file_name": r.file_name,
            "query": r.query,
            "created_at": r.created_at,
        }
        for r in records
    ]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
