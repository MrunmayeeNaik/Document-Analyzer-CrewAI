
# Financial Document Analyzer — Multi-Agent AI Pipeline

Upload any financial PDF (annual report, investor deck, earnings statement) 
and get structured investment insights returned via a REST API.

Built with CrewAI multi-agent orchestration — a financial analyst agent 
reads the document, reasons over it, and optionally searches the web 
for market context before producing a structured report.

---

## Tech stack

| Layer | Tool |
|---|---|
| Agent orchestration | CrewAI |
| LLM backend | OpenAI-compatible (Groq) |
| PDF extraction | Custom tool (PyMuPDF) |
| Web search | Serper API |
| API layer | FastAPI |
| Storage | SQLite via SQLAlchemy |
| Testing | Postman |

---

## What it produces

For any uploaded financial PDF, the system returns:
1. Document summary
2. Key financial metrics and trends
3. Analysis relevant to your specific query
4. Risks and uncertainties
5. High-level recommendations (with disclaimer)

Previous analyses are stored and retrievable via `GET /history`.

---

### 1. Bugs Found and How They Were Fixed

- **LLM ignored the uploaded PDF and returned a generic answer**
  - **Symptom**: `analysis` field said things like “without access to the specific financial document…” even though a PDF was uploaded.
  - **Cause**: The `analyze_financial_document` task in `task.py` only referenced `{query}` and never mentioned `{file_path}`, so the `financial_analyst` agent was not clearly instructed to use the PDF reader tool with the actual path.
  - **Fix**: Updated the task description to explicitly include `{file_path}` and to instruct the agent to call the `financial_document_reader` tool with that path before analyzing.

- **HTTP 500 with LLM error `Request too large / rate_limit_exceeded`**
  - **Symptom**: `POST /analyze` returned a 500 with a nested 413‑style error from Groq: “Request too large for model … Limit 12000, Requested 13632”.
  - **Cause**: `FinancialDocumentTool` in `tools.py` always returned the full text of the PDF, which made some prompts exceed the model’s token‑per‑minute limits for large documents.
  - **Fix**: Added truncation in `FinancialDocumentTool._run` so only the first N characters (default 20,000, configurable via `MAX_PDF_CHARS`) are passed to the model, with a note appended when truncation occurs.

- **No records visible in `/history`**
  - **Symptom**: `GET /history` always returned an empty list.
  - **Causes**:
    - Earlier `/analyze` calls failed (see above), so the DB write in `main.py` never executed.
    - The SQLite URL (`sqlite:///./analysis.db`) is relative, so starting the server from the wrong working directory can create or query the wrong DB file.
  - **Fix**: After fixing the LLM errors and ensuring the server is started from the project root, successful `/analyze` calls now insert rows into `Analysis`, and `/history` returns data.

- **Incorrect install command in README**
  - **Symptom**: README instructed `pip install -r requirement.txt`.
  - **Cause**: The actual dependency file in the repo is `requirements.txt`.
  - **Fix**: Updated the installation instructions to use `requirements.txt`.

---

### 2. Setup Instructions

- **Requirements**
  - Python 3.10+ recommended
  - `pip` for installing dependencies

- **Install dependencies**

```sh
pip install -r requirements.txt
```

- **Environment variables**

Create a `.env` file in the project root with at least:

- **`OPENAI_API_KEY`**: Groq/OpenAI‑compatible key used by CrewAI’s `LLM` (backed by the Groq endpoint).
- **`OPENAI_BASE_URL`**: Base URL for the Groq OpenAI‑compatible API (already set to `https://api.groq.com/openai/v1` in this project).
- **`SERPER_API_KEY`**: API key for the Serper search tool used by the agents.
- **Optional**: `MAX_PDF_CHARS` – maximum number of characters of PDF text passed to the LLM (defaults to `20000`).

> **Security note**: Keep `.env` out of version control; do not share your API keys.

- **Run the API**

From the project root (`financial-document-analyzer-debug`):

```sh
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.

---

### 3. Usage Instructions

- **1) Start the server**
  - Run the `uvicorn` command above from the project root so that `analysis.db` is created and used in the correct directory.

- **2) Analyze a financial PDF**
  - Endpoint: `POST /analyze`
  - Use a tool like Postman, curl, or a frontend form with:
    - A file field named `file` (PDF).
    - An optional form field `query` (defaults to: “Analyze this financial document for investment insights”).
  - The backend will:
    - Save the uploaded PDF to `data/financial_document_<uuid>.pdf`.
    - Run the CrewAI pipeline (financial analyst agent + tools).
    - Store the result in SQLite (`analysis.db`, table `analyses`).
    - Return the structured analysis in the response.

- **3) View analysis history**
  - Endpoint: `GET /history`
  - Returns basic metadata for all stored analyses (ID, file name, query, timestamp).

- **4) Inspect the database (optional)**
  - A SQLite DB file named `analysis.db` is created in the project root.
  - You can open it with any SQLite browser to inspect the `analyses` table.

---

### 4. API Documentation

#### `GET /`

- **Description**: Health check.
- **Response**:
  - `200 OK` – JSON:
    - `message`: `"Financial Document Analyzer API is running"`

#### `POST /analyze`

- **Description**: Analyze an uploaded financial PDF and persist the result.

- **Request**
  - **Content-Type**: `multipart/form-data`
  - **Fields**:
    - **`file`** (required): The PDF to analyze (`UploadFile`).
    - **`query`** (optional, `Form` string):
      - Default: `"Analyze this financial document for investment insights"`.
      - Used as the user’s prompt for the analysis.

- **Processing steps**
  - Save the uploaded file to `data/financial_document_<uuid>.pdf`.
  - Call `run_crew(query, file_path)`:
    - Creates a `Crew` with the `financial_analyst` agent and `analyze_financial_document` task.
    - The task:
      - Uses `financial_document_reader` to read and clean the PDF text (truncated to avoid token limits).
      - Optionally uses the Serper search tool for market context.
      - Produces a structured analysis with:
        1. Document Summary  
        2. Key Financial Metrics and Trends  
        3. Analysis Relevant to the User's Query  
        4. Risks and Uncertainties  
        5. High-level, non-personalized recommendations and a disclaimer
  - Store the result in SQLite via the `Analysis` model.
  - Delete the temporary PDF from `data/` in the `finally` block.

- **Successful Response**
  - **Status**: `200 OK`
  - **Body** (JSON):
    - `status`: `"success"`
    - `query`: The final query string used.
    - `analysis`: The full textual analysis produced by the Crew.
    - `file_processed`: Original filename of the uploaded PDF.

- **Error Responses**
  - **`400/422`**: Validation errors (e.g., missing file field) handled by FastAPI automatically.
  - **`500`**: Internal errors, wrapped as:
    - `{"detail": "Error processing financial document: <message>"}`  
    - Examples:
      - File not found / invalid PDF path.
      - LLM API issues (e.g., network or credential problems).
      - Unexpected exceptions during crew execution.

#### `GET /history`

- **Description**: Return a list of previously stored analyses (metadata only).

- **Response**
  - **Status**: `200 OK`
  - **Body** (JSON array):

```json
[
  {
    "id": "uuid-string",
    "file_name": "example.pdf",
    "query": "Analyze this financial document for investment insights",
    "created_at": "2026-02-26T12:34:56.789000"
  }
]
```

> The full analysis text is stored in the database but not returned by `/history` to keep the payload small. You can extend the API with a `/history/{id}` endpoint if you need to retrieve full analyses by ID.

---

### 5. High-Level Architecture

- **FastAPI (`main.py`)**
  - Defines the HTTP endpoints.
  - Orchestrates file upload, crew execution, and DB persistence.

- **CrewAI Agents and Tasks (`agents.py`, `task.py`)**
  - `financial_analyst`: Main agent that reads the PDF and generates the structured report.
  - Tasks describe what to do with the uploaded document and the user query.

- **Tools (`tools.py`)**
  - `financial_document_reader`: Reads and cleans PDF content, now with length limiting to avoid LLM token issues.
  - `search_tool`: Serper‑based web search for financial and market context.

- **Database (`database.py`)**
  - SQLite via SQLAlchemy.
  - `Analysis` model stores file name, query, analysis text, and creation timestamp.

This README reflects the current, debugged behavior of the project and should be a solid reference for setup, usage, and further extension.
