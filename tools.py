## Importing libraries and files
import os
import stat
from dotenv import load_dotenv
from pypdf import PdfReader
from crewai.tools import BaseTool
from crewai_tools import SerperDevTool

load_dotenv()

## Creating search tool
search_tool = SerperDevTool()


class FinancialDocumentTool(BaseTool):
    """CrewAI tool for reading and cleaning financial PDF documents."""

    name: str = "financial_document_reader"
    description: str = (
        "Read and clean the text content of a financial PDF document given its file path."
    )

    def _run(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        reader = PdfReader(file_path)

        full_report = ""
        for page in reader.pages:
            content = page.extract_text() or ""

            while "\n\n" in content:
                content = content.replace("\n\n", "\n")

            full_report += content + "\n"

        # To avoid exceeding LLM token limits on very large PDFs,
        # truncate the extracted text to a configurable maximum length.
        max_chars_env = os.getenv("MAX_PDF_CHARS")
        try:
            max_chars = int(max_chars_env) if max_chars_env else 20000
        except ValueError:
            max_chars = 20000

        if len(full_report) > max_chars:
            truncated = full_report[:max_chars]
            notice = (
                "\n\n[Note: Document was very large. "
                f"Only the first {max_chars} characters were provided to the model "
                "to stay within token limits. Focus your analysis on these sections.]"
            )
            return truncated + notice

        return full_report

financial_document_tool = FinancialDocumentTool()