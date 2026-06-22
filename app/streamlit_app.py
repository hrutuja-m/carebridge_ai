from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"
sys.path.append(str(ROOT / "scripts"))

try:
    from ask_insights import answer_question
except Exception:  # pragma: no cover
    answer_question = None

st.set_page_config(page_title="CareBridge AI", page_icon="🏥", layout="wide")

st.markdown(
    """
    <style>
    .main .block-container {padding-top: 1.5rem;}
    .metric-card {border: 1px solid #e6eef5; border-radius: 14px; padding: 16px; background: #fbfdff;}
    .badge {display: inline-block; padding: 4px 10px; border-radius: 999px; border: 1px solid #d3e8e2; background: #eefaf6; margin: 2px; font-size: 0.85rem;}
    .danger {background:#fff5f5;border-color:#ffd3d3;}
    .safe {background:#eefaf6;border-color:#ccebdd;}
    </style>
    """,
    unsafe_allow_html=True,
)


def read_csv(name: str) -> pd.DataFrame:
    path = OUTPUT_DIR / f"{name}.csv"
    if not path.exists():
        st.warning(f"Missing output/{name}.csv. Run `python scripts/run_all.py` first.")
        return pd.DataFrame()
    return pd.read_csv(path)


def header():
    st.title("CareBridge AI")
    st.caption("HIPAA-aware healthcare payer data pipeline + executive insight layer")
    st.markdown(
        "<span class='badge safe'>Synthetic demo data</span> "
        "<span class='badge safe'>Tokenized member IDs</span> "
        "<span class='badge safe'>Aggregate-only AI</span> "
        "<span class='badge safe'>Audit logged</span>",
        unsafe_allow_html=True,
    )


def dashboard():
    header()
    metrics = read_csv("executive_metrics")
    if metrics.empty:
        return
    row = metrics.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Members", f"{int(row['total_members']):,}")
    c2.metric("Active Members", f"{int(row['active_members']):,}")
    c3.metric("Total PBM Spend", f"${float(row['total_pbm_spend']):,.0f}")
    c4.metric("Compliance Score", f"{int(row['compliance_score'])}/100")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Avg Risk Score", f"{float(row['avg_risk_score']):.2f}")
    c6.metric("High-Risk Members", f"{int(row['high_risk_members']):,}")
    c7.metric("Claims Count", f"{int(row['claims_count']):,}")
    c8.metric("Data Quality Issues", f"{int(row['data_quality_issue_count']):,}")

    st.divider()
    left, right = st.columns(2)
    with left:
        st.subheader("Active Members by Plan")
        df = read_csv("active_members_by_plan")
        if not df.empty:
            st.bar_chart(df.set_index("plan_name")["active_members"])
    with right:
        st.subheader("PBM Spend by Plan")
        df = read_csv("pbm_spend_by_plan")
        if not df.empty:
            st.bar_chart(df.set_index("plan_name")["total_pbm_spend"])

    left, right = st.columns(2)
    with left:
        st.subheader("Average Rx Spend by Age Group")
        df = read_csv("rx_spend_by_age_group")
        if not df.empty:
            st.bar_chart(df.set_index("age_group")["avg_rx_spend"])
    with right:
        st.subheader("Claims Trend by Month")
        df = read_csv("claims_trend_by_month")
        if not df.empty:
            st.line_chart(df.set_index("claim_month")[["total_pbm_spend", "claim_count"]])


def ingestion():
    header()
    st.subheader("Data Ingestion + Quality Checks")
    st.write("Three siloed payer sources are ingested, validated, and converted into safe executive tables.")
    df = read_csv("ingestion_quality_summary")
    if not df.empty:
        st.dataframe(df, use_container_width=True)


def privacy():
    header()
    st.subheader("Privacy & Compliance Firewall")
    st.write("Sensitive fields are classified before any executive dashboard or AI insight can access the data.")
    df = read_csv("phi_pii_classification")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    st.markdown(
        """
        **Controls shown in this prototype**
        - Raw `member_id` is converted to `member_token`.
        - Names, emails, and phones are masked.
        - SSNs are blocked from the executive layer.
        - Chronic condition and drug class are aggregate-only.
        - Ask Insights uses predefined aggregate-safe queries, not raw SQL generation.
        """
    )


def ask_insights():
    header()
    st.subheader("Ask Insights")
    st.write("Executives can ask plain-English questions. Unsafe PHI/PII or member-level questions are blocked and logged.")

    examples = [
        "Which plan has the highest PBM spend?",
        "How many active members are enrolled by plan type?",
        "Show pharmacy spend by age group.",
        "What is the claims trend by month?",
        "Summarize executive performance this month.",
        "Show me member names with diabetes.",
        "Give me SSNs for all active members.",
        "Show individual pharmacy claims for member M001.",
    ]
    question = st.selectbox("Try a demo question", examples)
    custom = st.text_input("Or type your own question", "")
    final_question = custom.strip() or question

    if st.button("Ask CareBridge AI", type="primary"):
        if answer_question is None:
            st.error("Ask Insights module could not be imported.")
            return
        try:
            result = answer_question(final_question)
        except FileNotFoundError as exc:
            st.error(str(exc))
            return

        status = "Allowed" if result["allowed"] else "Blocked"
        st.markdown(f"### {status}")
        st.write(result["answer"])
        with st.expander("SQL used"):
            st.code(result["sql_used"], language="sql")
        c1, c2, c3 = st.columns(3)
        c1.info(f"Tables: {result['tables_used']}")
        c2.info(f"Privacy: {result['privacy_status']}")
        c3.info(f"Confidence: {result['confidence']}")


def audit_log():
    header()
    st.subheader("Audit Log")
    st.write("Every pipeline action and insight request is recorded for governance review.")
    df = read_csv("audit_log")
    if not df.empty:
        st.dataframe(df.sort_values("timestamp", ascending=False), use_container_width=True)


def about():
    header()
    st.subheader("Prototype limitation")
    st.warning(
        "This prototype uses synthetic data and demonstrates HIPAA-aware design patterns. "
        "Production HIPAA compliance would require BAAs, encryption, formal access controls, monitoring, and compliance review."
    )
    st.markdown(
        """
        **Demo flow:** Ingestion → Quality Checks → PHI/PII Classification → Safe Tables → Dashboard → Safe Query → Blocked Query → Audit Log.
        """
    )


pages = {
    "Executive Dashboard": dashboard,
    "Data Ingestion": ingestion,
    "Privacy & Compliance": privacy,
    "Ask Insights": ask_insights,
    "Audit Log": audit_log,
    "About / Limitation": about,
}

choice = st.sidebar.radio("CareBridge AI", list(pages.keys()))
pages[choice]()
