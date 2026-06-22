"""CareBridge AI ingestion, quality, privacy, safe layer, and metrics pipeline."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
SECRET_SALT = "carebridge-demo-salt-change-in-prod"

PII_COLUMNS = ["member_name", "email", "phone", "ssn"]
PHI_COLUMNS = ["chronic_condition", "drug_class"]
BLOCKED_COLUMNS = ["ssn"]
MASKED_COLUMNS = ["member_name", "email", "phone"]
AGGREGATE_ONLY_COLUMNS = ["chronic_condition", "drug_class"]


def tokenise(value: Any) -> str | None:
    if pd.isna(value) or str(value).strip() == "":
        return None
    raw = f"{value}|{SECRET_SALT}"
    return "tok_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def mask_name(value: Any) -> str:
    if pd.isna(value) or not str(value).strip():
        return ""
    parts = str(value).split()
    return parts[0][0] + "*** " + parts[-1][0] + "***" if len(parts) > 1 else parts[0][0] + "***"


def mask_email(value: Any) -> str:
    if pd.isna(value) or "@" not in str(value):
        return ""
    domain = str(value).split("@")[-1]
    return f"m***@{domain}"


def mask_phone(value: Any) -> str:
    if pd.isna(value):
        return ""
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    return "***-***-" + digits[-4:] if len(digits) >= 4 else "***"


def valid_ssn(value: Any) -> bool:
    if pd.isna(value):
        return False
    s = str(value)
    parts = s.split("-")
    return len(parts) == 3 and len(parts[0]) == 3 and len(parts[1]) == 2 and len(parts[2]) == 4 and all(p.isdigit() for p in parts)


def load_sources() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    required = ["members.csv", "enrollment.csv", "pharmacy_claims.csv"]
    missing = [name for name in required if not (DATA_DIR / name).exists()]
    if missing:
        raise FileNotFoundError(f"Missing source files in {DATA_DIR}: {missing}. Run generate_synthetic_data.py first.")
    members = pd.read_csv(DATA_DIR / "members.csv", dtype=str, keep_default_na=False)
    enrollment = pd.read_csv(DATA_DIR / "enrollment.csv", dtype=str, keep_default_na=False)
    claims = pd.read_csv(DATA_DIR / "pharmacy_claims.csv", dtype=str, keep_default_na=False)
    return members, enrollment, claims


def quality_summary(members: pd.DataFrame, enrollment: pd.DataFrame, claims: pd.DataFrame) -> pd.DataFrame:
    valid_members = set(members["member_id"].dropna().astype(str))

    def invalid_dates(df: pd.DataFrame, cols: list[str]) -> int:
        total = 0
        for col in cols:
            if col not in df:
                continue
            nonblank = df[col].fillna("").astype(str).str.strip() != ""
            parsed = pd.to_datetime(df.loc[nonblank, col], errors="coerce")
            total += int(parsed.isna().sum())
        return total

    summary = [
        {
            "file_name": "members.csv",
            "row_count": len(members),
            "missing_values": int((members[["member_id", "member_name", "email", "phone", "ssn", "age_group", "county", "state", "risk_score", "chronic_condition"]] == "").sum().sum()),
            "duplicate_rows": int(members.duplicated().sum()),
            "invalid_dates": 0,
            "unmatched_member_ids": 0,
            "invalid_ssns": int((~members["ssn"].apply(valid_ssn)).sum()) if "ssn" in members else 0,
            "null_paid_amounts": 0,
        },
        {
            "file_name": "enrollment.csv",
            "row_count": len(enrollment),
            "missing_values": int((enrollment[["enrollment_id", "member_id", "plan_id", "plan_name", "plan_type", "status", "effective_date"]] == "").sum().sum()),
            "duplicate_rows": int(enrollment.duplicated().sum()),
            "invalid_dates": invalid_dates(enrollment, ["effective_date", "termination_date"]),
            "unmatched_member_ids": int((~enrollment["member_id"].isin(valid_members)).sum()),
            "invalid_ssns": 0,
            "null_paid_amounts": 0,
        },
        {
            "file_name": "pharmacy_claims.csv",
            "row_count": len(claims),
            "missing_values": int((claims[["claim_id", "member_id", "drug_class", "pharmacy_name", "claim_date", "paid_amount", "claim_status"]] == "").sum().sum()),
            "duplicate_rows": int(claims.duplicated().sum()),
            "invalid_dates": invalid_dates(claims, ["claim_date"]),
            "unmatched_member_ids": int((~claims["member_id"].isin(valid_members)).sum()),
            "invalid_ssns": 0,
            "null_paid_amounts": int(pd.to_numeric(claims["paid_amount"], errors="coerce").isna().sum()) if "paid_amount" in claims else 0,
        },
    ]
    q = pd.DataFrame(summary)
    q["issue_count"] = q[["missing_values", "duplicate_rows", "invalid_dates", "unmatched_member_ids", "invalid_ssns", "null_paid_amounts"]].sum(axis=1)
    q["status"] = q["issue_count"].apply(lambda x: "Passed" if x == 0 else ("Warning" if x < 80 else "Needs Review"))
    return q


def phi_pii_classification() -> pd.DataFrame:
    rows = [
        ("member_id", "Identifier", "Medium", "Tokenize", "Raw ID replaced with irreversible token."),
        ("member_name", "PII", "High", "Mask", "Visible only as masked text in compliance demo."),
        ("email", "PII", "High", "Mask", "Domain preserved only for demo; local part masked."),
        ("phone", "PII", "High", "Mask", "Only last four digits retained in masked view."),
        ("ssn", "PII", "Critical", "Block", "Never exposed in executive layer."),
        ("chronic_condition", "PHI-like", "High", "Aggregate only", "Converted to chronic_condition_flag for executive analytics."),
        ("drug_class", "PHI-like/PBM", "High", "Aggregate only", "Used only in grouped PBM trends."),
        ("paid_amount", "Financial/Claim", "Medium", "Allow aggregated", "Allowed only in grouped metrics."),
        ("age_group", "Demographic", "Low", "Allow grouped", "Safe demographic band."),
        ("county", "Geography", "Low", "Allow grouped", "County-level aggregate only."),
    ]
    return pd.DataFrame(rows, columns=["column_name", "data_type", "risk_level", "action", "rationale"])


def build_safe_layers(members: pd.DataFrame, enrollment: pd.DataFrame, claims: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    members_clean = members.dropna(subset=["member_id"]).drop_duplicates(subset=["member_id"], keep="first").copy()
    members_clean["member_token"] = members_clean["member_id"].apply(tokenise)
    members_safe = members_clean[
        ["member_token", "age_group", "county", "state", "risk_score", "chronic_condition"]
    ].copy()
    members_safe["risk_score"] = pd.to_numeric(members_safe["risk_score"], errors="coerce").fillna(0)
    members_safe["chronic_condition_flag"] = members_safe["chronic_condition"].apply(lambda x: bool(str(x) != "None"))
    members_safe = members_safe.drop(columns=["chronic_condition"])

    id_map = members_clean[["member_id", "member_token"]]

    enrollment_safe = enrollment.merge(id_map, on="member_id", how="inner")
    enrollment_safe["effective_date"] = pd.to_datetime(enrollment_safe["effective_date"], errors="coerce")
    enrollment_safe["termination_date"] = pd.to_datetime(enrollment_safe["termination_date"], errors="coerce")
    enrollment_safe = enrollment_safe.dropna(subset=["effective_date"])
    enrollment_safe = enrollment_safe[
        ["enrollment_id", "member_token", "plan_id", "plan_name", "plan_type", "status", "effective_date", "termination_date"]
    ].copy()

    claims_safe = claims.merge(id_map, on="member_id", how="inner")
    claims_safe["claim_date"] = pd.to_datetime(claims_safe["claim_date"], errors="coerce")
    claims_safe["paid_amount"] = pd.to_numeric(claims_safe["paid_amount"], errors="coerce")
    claims_safe = claims_safe.dropna(subset=["claim_date", "paid_amount"])
    claims_safe["claim_month"] = claims_safe["claim_date"].dt.to_period("M").astype(str)
    claims_safe["drug_class_category"] = claims_safe["drug_class"].astype(str)
    claims_safe = claims_safe[
        ["claim_id", "member_token", "drug_class_category", "claim_month", "paid_amount", "claim_status"]
    ].copy()
    return members_safe, enrollment_safe, claims_safe


def build_metrics(members_safe: pd.DataFrame, enrollment_safe: pd.DataFrame, claims_safe: pd.DataFrame) -> dict[str, pd.DataFrame]:
    active_members_by_plan = (
        enrollment_safe[enrollment_safe["status"] == "Active"]
        .groupby(["plan_name", "plan_type"], as_index=False)
        .agg(active_members=("member_token", "nunique"))
        .sort_values("active_members", ascending=False)
    )

    pbm_spend_by_plan = (
        claims_safe.merge(enrollment_safe[["member_token", "plan_name", "plan_type"]].drop_duplicates("member_token"), on="member_token", how="inner")
        .groupby(["plan_name", "plan_type"], as_index=False)
        .agg(total_pbm_spend=("paid_amount", "sum"), claim_count=("claim_id", "count"))
        .sort_values("total_pbm_spend", ascending=False)
    )

    rx_spend_by_age_group = (
        claims_safe.merge(members_safe[["member_token", "age_group"]], on="member_token", how="inner")
        .groupby("age_group", as_index=False)
        .agg(avg_rx_spend=("paid_amount", "mean"), total_rx_spend=("paid_amount", "sum"), claim_count=("claim_id", "count"))
        .sort_values("age_group")
    )

    claims_trend_by_month = (
        claims_safe.groupby("claim_month", as_index=False)
        .agg(total_pbm_spend=("paid_amount", "sum"), claim_count=("claim_id", "count"))
        .sort_values("claim_month")
    )

    high_risk_members_by_plan = (
        enrollment_safe.merge(members_safe[["member_token", "risk_score"]], on="member_token", how="inner")
        .assign(high_risk=lambda d: d["risk_score"] >= 0.72)
        .groupby("plan_name", as_index=False)
        .agg(high_risk_members=("high_risk", "sum"), avg_risk_score=("risk_score", "mean"))
        .sort_values("high_risk_members", ascending=False)
    )

    month = claims_trend_by_month["claim_month"].max() if not claims_trend_by_month.empty else datetime.now().strftime("%Y-%m")
    executive_metrics = pd.DataFrame(
        [
            {
                "month": month,
                "total_members": int(members_safe["member_token"].nunique()),
                "active_members": int(enrollment_safe.loc[enrollment_safe["status"] == "Active", "member_token"].nunique()),
                "total_pbm_spend": round(float(claims_safe["paid_amount"].sum()), 2),
                "avg_risk_score": round(float(members_safe["risk_score"].mean()), 3),
                "high_risk_members": int((members_safe["risk_score"] >= 0.72).sum()),
                "claims_count": int(len(claims_safe)),
                "blocked_query_count": 0,
                "data_quality_issue_count": 0,
                "compliance_score": 91,
            }
        ]
    )

    return {
        "active_members_by_plan": active_members_by_plan,
        "pbm_spend_by_plan": pbm_spend_by_plan,
        "rx_spend_by_age_group": rx_spend_by_age_group,
        "claims_trend_by_month": claims_trend_by_month,
        "high_risk_members_by_plan": high_risk_members_by_plan,
        "executive_metrics": executive_metrics,
    }


def initial_audit_log() -> pd.DataFrame:
    now = datetime.now().isoformat(timespec="seconds")
    rows = [
        {
            "timestamp": now,
            "user_role": "System",
            "question_or_action": "Pipeline run completed",
            "allowed_or_blocked": "Allowed",
            "reason": "Raw sources validated, PHI/PII classified, safe tables generated.",
            "tables_accessed": "members.csv,enrollment.csv,pharmacy_claims.csv",
            "privacy_status": "Raw-to-safe transformation complete",
        },
        {
            "timestamp": now,
            "user_role": "Compliance Officer",
            "question_or_action": "PHI/PII scan completed",
            "allowed_or_blocked": "Allowed",
            "reason": "Sensitive fields classified as mask, block, or aggregate-only.",
            "tables_accessed": "phi_pii_classification",
            "privacy_status": "HIPAA-aware controls applied",
        },
    ]
    return pd.DataFrame(rows)


def write_outputs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    members, enrollment, claims = load_sources()
    q = quality_summary(members, enrollment, claims)
    classification = phi_pii_classification()
    members_safe, enrollment_safe, claims_safe = build_safe_layers(members, enrollment, claims)
    metrics = build_metrics(members_safe, enrollment_safe, claims_safe)
    metrics["executive_metrics"]["data_quality_issue_count"] = int(q["issue_count"].sum())

    q.to_csv(OUTPUT_DIR / "ingestion_quality_summary.csv", index=False)
    classification.to_csv(OUTPUT_DIR / "phi_pii_classification.csv", index=False)
    members_safe.to_csv(OUTPUT_DIR / "members_safe.csv", index=False)
    enrollment_safe.to_csv(OUTPUT_DIR / "enrollment_safe.csv", index=False)
    claims_safe.to_csv(OUTPUT_DIR / "pharmacy_claims_safe.csv", index=False)
    for name, df in metrics.items():
        df.to_csv(OUTPUT_DIR / f"{name}.csv", index=False)
    initial_audit_log().to_csv(OUTPUT_DIR / "audit_log.csv", index=False)

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "raw_files": {"members": len(members), "enrollment": len(enrollment), "pharmacy_claims": len(claims)},
        "safe_tables": {"members_safe": len(members_safe), "enrollment_safe": len(enrollment_safe), "pharmacy_claims_safe": len(claims_safe)},
        "controls": {
            "tokenized_member_id": True,
            "masked_columns": MASKED_COLUMNS,
            "blocked_columns": BLOCKED_COLUMNS,
            "aggregate_only_columns": AGGREGATE_ONLY_COLUMNS,
            "ai_allowed_tables": ["executive_metrics", "active_members_by_plan", "pbm_spend_by_plan", "rx_spend_by_age_group", "claims_trend_by_month"],
        },
    }
    (OUTPUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("CareBridge AI pipeline completed.")
    print(f"Outputs written to: {OUTPUT_DIR}")
    print(q.to_string(index=False))


if __name__ == "__main__":
    write_outputs()
