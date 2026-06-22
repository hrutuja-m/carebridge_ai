"""Controlled, demo-safe Ask Insights layer for CareBridge AI.

This is intentionally not a free-form SQL agent. It maps common executive
questions to predefined aggregate-safe outputs and blocks PII/PHI/member-level
questions.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"

BLOCK_TERMS = [
    "ssn", "social security", "member name", "member names", "name with", "names with",
    "email", "phone", "address", "dob", "date of birth", "individual", "member m", "raw claim",
    "claim for member", "diabetes members", "members with diabetes", "show me member",
]

SQL_MAP = {
    "active_members_by_plan": """SELECT plan_name, plan_type, COUNT(DISTINCT member_token) AS active_members\nFROM enrollment_safe\nWHERE status = 'Active'\nGROUP BY plan_name, plan_type\nORDER BY active_members DESC;""",
    "pbm_spend_by_plan": """SELECT e.plan_name, e.plan_type, SUM(p.paid_amount) AS total_pbm_spend\nFROM pharmacy_claims_safe p\nJOIN enrollment_safe e ON p.member_token = e.member_token\nGROUP BY e.plan_name, e.plan_type\nORDER BY total_pbm_spend DESC;""",
    "rx_spend_by_age_group": """SELECT m.age_group, AVG(p.paid_amount) AS avg_rx_spend\nFROM pharmacy_claims_safe p\nJOIN members_safe m ON p.member_token = m.member_token\nGROUP BY m.age_group\nORDER BY m.age_group;""",
    "claims_trend_by_month": """SELECT claim_month, SUM(paid_amount) AS total_pbm_spend, COUNT(*) AS claim_count\nFROM pharmacy_claims_safe\nGROUP BY claim_month\nORDER BY claim_month;""",
    "executive_summary": """SELECT month, total_members, active_members, total_pbm_spend, avg_risk_score, high_risk_members, compliance_score\nFROM executive_metrics\nORDER BY month DESC\nLIMIT 1;""",
}


def _read(name: str) -> pd.DataFrame:
    path = OUTPUT_DIR / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run scripts/ingest_pipeline.py first.")
    return pd.read_csv(path)


def classify_question(question: str) -> str:
    q = question.lower()
    if any(term in q for term in BLOCK_TERMS):
        return "blocked"
    if "age" in q:
        return "rx_spend_by_age_group"
    if "active" in q or "enrolled" in q or "enrollment" in q:
        return "active_members_by_plan"
    if "highest" in q and ("pbm" in q or "pharmacy" in q or "spend" in q):
        return "pbm_spend_by_plan"
    if "pbm" in q or "pharmacy" in q or "spend" in q:
        return "rx_spend_by_age_group"
    if "trend" in q or "month" in q or "claims" in q:
        return "claims_trend_by_month"
    if "summary" in q or "performance" in q or "executive" in q:
        return "executive_summary"
    return "executive_summary"


def answer_question(question: str, user_role: str = "Executive") -> dict:
    intent = classify_question(question)
    now = datetime.now().isoformat(timespec="seconds")

    if intent == "blocked":
        result = {
            "timestamp": now,
            "question": question,
            "allowed": False,
            "answer": "Request blocked. This question may expose PII, PHI-like data, or member-level claim details. CareBridge AI only allows aggregate, minimum-necessary executive insights.",
            "sql_used": "No SQL executed.",
            "tables_used": "None",
            "privacy_status": "Blocked: potential PHI/PII/member-level request",
            "confidence": "High",
            "reason": "Unsafe query terms detected.",
        }
        append_audit(result, user_role=user_role)
        return result

    df = _read(intent)
    sql = SQL_MAP[intent]

    if intent == "active_members_by_plan":
        top = df.iloc[0]
        answer = f"{top['plan_name']} has the highest active enrollment with {int(top['active_members']):,} active members."
        tables = "enrollment_safe"
    elif intent == "pbm_spend_by_plan":
        top = df.iloc[0]
        answer = f"{top['plan_name']} has the highest PBM spend at ${float(top['total_pbm_spend']):,.2f}."
        tables = "pharmacy_claims_safe,enrollment_safe"
    elif intent == "rx_spend_by_age_group":
        top = df.sort_values("avg_rx_spend", ascending=False).iloc[0]
        answer = f"The {top['age_group']} age group has the highest average Rx spend at ${float(top['avg_rx_spend']):,.2f}."
        tables = "pharmacy_claims_safe,members_safe"
    elif intent == "claims_trend_by_month":
        latest = df.iloc[-1]
        answer = f"The latest month, {latest['claim_month']}, shows ${float(latest['total_pbm_spend']):,.2f} in PBM spend across {int(latest['claim_count']):,} claims."
        tables = "pharmacy_claims_safe"
    else:
        row = df.iloc[0]
        answer = (
            f"For {row['month']}, CareBridge AI shows {int(row['active_members']):,} active members, "
            f"${float(row['total_pbm_spend']):,.2f} total PBM spend, {int(row['high_risk_members']):,} high-risk members, "
            f"and a compliance score of {int(row['compliance_score'])}."
        )
        tables = "executive_metrics"

    result = {
        "timestamp": now,
        "question": question,
        "allowed": True,
        "answer": answer + " Generated from aggregated metrics only. No raw PHI accessed.",
        "sql_used": sql,
        "tables_used": tables,
        "privacy_status": "Allowed: aggregate-only executive-safe data",
        "confidence": "High",
        "reason": "Mapped to predefined safe aggregate query.",
    }
    append_audit(result, user_role=user_role)
    return result


def append_audit(result: dict, user_role: str) -> None:
    path = OUTPUT_DIR / "audit_log.csv"
    if path.exists():
        audit = pd.read_csv(path)
    else:
        audit = pd.DataFrame(columns=["timestamp", "user_role", "question_or_action", "allowed_or_blocked", "reason", "tables_accessed", "privacy_status"])
    row = {
        "timestamp": result["timestamp"],
        "user_role": user_role,
        "question_or_action": result["question"],
        "allowed_or_blocked": "Allowed" if result["allowed"] else "Blocked",
        "reason": result["reason"],
        "tables_accessed": result["tables_used"],
        "privacy_status": result["privacy_status"],
    }
    audit = pd.concat([audit, pd.DataFrame([row])], ignore_index=True)
    audit.to_csv(path, index=False)


if __name__ == "__main__":
    demo_questions = [
        "How many active members are enrolled by plan type?",
        "Which plan has the highest PBM spend?",
        "Show pharmacy spend by age group.",
        "Show me member names with diabetes.",
        "Give me SSNs for all active members.",
    ]
    for question in demo_questions:
        print("\nQUESTION:", question)
        response = answer_question(question)
        print("ALLOWED:", response["allowed"])
        print("ANSWER:", response["answer"])
        print("PRIVACY:", response["privacy_status"])
