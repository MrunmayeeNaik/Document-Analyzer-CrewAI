## Importing libraries and files
from crewai import Task

from agents import financial_analyst, investment_advisor, risk_assessor, verifier
from tools import financial_document_tool, search_tool

## Creating a task to help solve user's query
analyze_financial_document = Task(
    description=(
        "Analyze the uploaded financial document located at the path: {file_path} "
        "in the context of the user's query: {query}. "
        "Always begin by using the 'financial_document_reader' PDF tool with this exact file path "
        "to read the full text of the document. Based on the extracted content, identify key "
        "financial metrics, trends, and qualitative information, and then answer the query in a "
        "clear, structured way. If necessary, use the web search tool to clarify terms or get "
        "recent market context from reputable sources. Always base your conclusions primarily on "
        "the uploaded document and trustworthy data."
    ),
    expected_output=(
        "Return a structured analysis with these sections:\n"
        "1. Document Summary\n"
        "2. Key Financial Metrics and Trends\n"
        "3. Analysis Relevant to the User's Query\n"
        "4. Risks and Uncertainties\n"
        "5. High-level, non-personalized recommendations or insights\n"
        "Include a brief disclaimer that this is not personalized financial advice."
    ),
    agent=financial_analyst,
    tools=[search_tool, financial_document_tool],
    async_execution=False,
)

## Creating an investment analysis task
investment_analysis = Task(
    description=(
        "Analyze the provided financial document and the user's query: {query}.\n"
        "1) Identify the company's recent financial performance (revenue, profit, cash flow, margins, leverage).\n"
        "2) Highlight key drivers of performance and any material changes vs prior periods.\n"
        "3) Based on fundamentals, outline potential investment opportunities (bull and bear cases).\n"
        "4) Clearly explain how the numbers in the document support your conclusions.\n"
        "Only use information that can reasonably be inferred from the document and general market knowledge."
    ),
    expected_output=(
        "Produce a structured, investor-friendly analysis with these sections:\n"
        "- Company overview (1 short paragraph)\n"
        "- Recent financial performance (bullets with key metrics and trends)\n"
        "- Investment thesis (bull case, bear case, and base case)\n"
        "- Key upside catalysts and downside risks\n"
        "- Concise conclusion with a risk-aware recommendation (e.g. watchlist / accumulate / avoid)\n"
        "Avoid sensational language and do not fabricate highly specific numbers not implied by the document."
    ),
    agent=investment_advisor,
    tools=[financial_document_tool],
    async_execution=False,
)

## Creating a risk assessment task
risk_assessment = Task(
    description=(
        "Assess the key risks related to the entity described in the financial document and the user's query: {query}.\n"
        "Focus on: business model risks, financial risks (liquidity, leverage, cash flow), market/industry risks,\n"
        "regulatory/legal risks, and operational risks.\n"
        "Use the document content as primary evidence and supplement with general, reasonable market knowledge when needed."
    ),
    expected_output=(
        "Return a concise but thorough risk assessment with:\n"
        "- High-level risk overview (2–3 sentences)\n"
        "- Bullet list of major risk categories (business, financial, market, regulatory, operational)\n"
        "- For each category: description, why it matters, and potential impact on investors\n"
        "- Short note on overall risk profile (e.g. low/medium/high) and monitoring points for the future\n"
        "Avoid exaggerated language; be realistic and clearly distinguish facts from assumptions."
    ),
    agent=risk_assessor,
    tools=[financial_document_tool],
    async_execution=False,
)


verification = Task(
    description=(
        "Determine whether the provided document is a financial or investment-related document.\n"
        "Check for indicators such as: financial statements (income statement, balance sheet, cash flow),\n"
        "management discussion and analysis, KPIs, guidance, shareholder letters, or investment product terms.\n"
        "If it is financial, briefly summarize what type (e.g. quarterly report, annual report, investor presentation).\n"
        "If it is not clearly financial, explain why and what it appears to be instead."
    ),
    expected_output=(
        "Return a short verification report with:\n"
        "- A classification: 'financial document', 'possibly financial', or 'not financial'\n"
        "- 2–4 bullet points citing textual evidence from the document that supports your classification\n"
        "- If classified as financial/possibly financial: mention the likely type and intended audience\n"
        "- If not financial: suggest what the document most likely is (e.g. marketing brochure, generic PDF)\n"
        "Be honest about uncertainty; do not guess with high confidence when evidence is weak."
    ),
    agent=verifier,
    tools=[financial_document_tool],
    async_execution=False,
)
