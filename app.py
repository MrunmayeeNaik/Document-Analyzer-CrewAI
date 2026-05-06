import os

import requests
import streamlit as st

API_URL = os.getenv("ANALYZER_API_URL", "http://localhost:8000")

st.set_page_config(page_title="Financial Document Analyzer", page_icon="📊", layout="wide")

st.title("Financial Document Analyzer")
st.caption("Multi-agent CrewAI pipeline: Verifier → Financial Analyst → Investment Advisor → Risk Analyst")

tab_analyze, tab_history = st.tabs(["Analyze", "History"])


def render_sections(data: dict) -> None:
    sub = st.tabs(["Verification", "Summary", "Investment", "Risks"])
    with sub[0]:
        st.markdown(data.get("verification") or "_no output_")
    with sub[1]:
        st.markdown(data.get("summary") or "_no output_")
    with sub[2]:
        st.markdown(data.get("investment") or "_no output_")
    with sub[3]:
        st.markdown(data.get("risks") or "_no output_")


with tab_analyze:
    uploaded = st.file_uploader("Upload a financial PDF", type=["pdf"])
    query = st.text_area(
        "Query",
        value="Analyze this financial document for investment insights",
        height=80,
    )

    if st.button("Run analysis", type="primary", disabled=uploaded is None):
        with st.status("Running 4-agent crew sequentially (this can take a few minutes)...", expanded=True) as status:
            st.write("Verifier → Financial Analyst → Investment Advisor → Risk Analyst")
            try:
                files = {"file": (uploaded.name, uploaded.getvalue(), "application/pdf")}
                resp = requests.post(
                    f"{API_URL}/analyze",
                    files=files,
                    data={"query": query},
                    timeout=600,
                )
                resp.raise_for_status()
                result = resp.json()
                status.update(label="Analysis complete", state="complete")
            except requests.HTTPError:
                status.update(label="Analysis failed", state="error")
                st.error(f"API error {resp.status_code}: {resp.text}")
                result = None
            except requests.RequestException as e:
                status.update(label="Analysis failed", state="error")
                st.error(f"Request failed: {e}")
                result = None

        if result:
            st.success(f"Saved as record `{result['id']}`")
            render_sections(result)

with tab_history:
    if st.button("Refresh"):
        st.rerun()

    try:
        records = requests.get(f"{API_URL}/history", timeout=15).json()
    except requests.RequestException as e:
        st.error(f"Could not load history: {e}")
        records = []

    if not records:
        st.info("No analyses yet. Run one in the Analyze tab.")
    else:
        labels = [f"{r['created_at']} — {r['file_name']} — {r['query'][:60]}" for r in records]
        choice = st.selectbox("Select a past analysis", range(len(records)), format_func=lambda i: labels[i])
        selected_id = records[choice]["id"]

        try:
            detail = requests.get(f"{API_URL}/history/{selected_id}", timeout=15).json()
            render_sections(detail)
        except requests.RequestException as e:
            st.error(f"Could not load analysis: {e}")
