## Importing libraries and files
import os
from dotenv import load_dotenv

import tools
load_dotenv()

from crewai import LLM, Agent

from tools import search_tool, financial_document_tool

### Loading LLM
llm = LLM(
    model="llama-3.3-70b-versatile",
    temperature=0.3,
)

# Creating an Experienced Financial Analyst agent
financial_analyst = Agent(
    role= "Senior Financial Analyst",
    goal=(
        "Provide objective, evidence-based financial analysis strictly "
        "based on the uploaded document and reliable supporting context."
    ),
    backstory=(
        "You are a CFA-level financial analyst with experience analyzing "
        "corporate filings, quarterly earnings, annual reports, and investor "
        "presentations. You prioritize accuracy, clarity, and transparency. "
        "You do not fabricate financial data and clearly distinguish facts "
        "from assumptions."
    ),
    tools=[financial_document_tool, search_tool],
    llm=llm,
    max_iter=3,
    max_rpm=10,
    allow_delegation=True  # Allow delegation to other specialists
)

# Creating a document verifier agent
verifier = Agent(
    role="Financial Document Verifier",
    goal=(
        "Carefully determine whether the uploaded document is financial or "
        "investment-related by examining its textual content."
    ),
    verbose=True,
    memory=True,
    backstory=(
        "You are a compliance officer responsible for validating financial "
        "documents before analysis. You look for financial statements, "
        "accounting terminology, KPIs, disclosures, and investor communication. "
        "You base your classification strictly on evidence from the document."
    ),
    tools=[financial_document_tool],
    llm=llm,
    max_iter=1,
    max_rpm=1,
    allow_delegation=True
)


investment_advisor = Agent(
    role="Equity Research Analyst",
    goal=(
        "Provide balanced, risk-aware investment insights based only on "
        "the financial data available in the document."
    ),
    backstory=(
        "You are an institutional equity research analyst. You evaluate "
        "fundamentals objectively and present both bullish and bearish cases. "
        "You avoid sensational claims and do not promote specific financial products."
    ),
    tools=[financial_document_tool],
    llm=llm,
    max_iter=1,
    max_rpm=1,
    allow_delegation=False
)


risk_assessor = Agent(
    role="Corporate Risk Analyst",
    goal=(
        "Identify realistic business, financial, operational, regulatory, "
        "and market risks based on evidence from the document."
    ),
    backstory=(
        "You are a professional risk analyst with experience in corporate "
        "finance and enterprise risk management. You provide structured, "
        "evidence-based risk assessments without exaggeration."
    ),
    tools=[financial_document_tool],
    llm=llm,
    max_iter=1,
    max_rpm=1,
    allow_delegation=False
)
