"""Generate synthetic healthcare payer source files for CareBridge AI.

Creates three siloed payer datasets with deliberate data quality issues:
- members.csv
- enrollment.csv
- pharmacy_claims.csv

The values are synthetic and safe for demos. Some columns intentionally look like
PII/PHI so the privacy pipeline can demonstrate detection, masking, blocking,
and aggregate-only controls.
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

random.seed(42)

FIRST_NAMES = [
    "Ava", "Mia", "Noah", "Liam", "Emma", "Olivia", "Sophia", "Ethan", "Lucas", "Amelia",
    "Harper", "Isabella", "James", "Benjamin", "Charlotte", "Elijah", "Henry", "Evelyn", "Aria", "Mason"
]
LAST_NAMES = [
    "Smith", "Johnson", "Garcia", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor", "Anderson",
    "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Martinez", "Robinson", "Clark", "Lewis"
]
COUNTIES = ["Dallas", "Tarrant", "Collin", "Denton", "Harris", "Travis", "Bexar", "El Paso"]
STATES = ["TX", "MA", "CA", "NY", "FL", "IL", "PA", "OH"]
AGE_GROUPS = ["18-34", "35-44", "45-54", "55-64", "65+"]
CHRONIC = ["None", "Diabetes", "Hypertension", "COPD", "Heart Failure", "Depression", "CKD"]
PLANS = [
    ("P100", "Gold PPO", "PPO"),
    ("P200", "Silver HMO", "HMO"),
    ("P300", "Care EPO", "EPO"),
    ("P400", "Medicare Advantage Plus", "MA"),
]
DRUG_CLASSES = ["Diabetes", "Cardiology", "Oncology", "Specialty", "Respiratory", "Behavioral Health"]
PHARMACIES = ["CVS", "Walgreens", "OptumRx", "Express Scripts", "Costco Pharmacy", "Local Care Pharmacy"]


def random_ssn(valid: bool = True) -> str:
    if not valid:
        return random.choice(["000-00-0000", "123", "INVALID", "999-99-9999"])
    return f"{random.randint(100, 899):03d}-{random.randint(10, 99):02d}-{random.randint(1000, 9999):04d}"


def generate_members(n: int = 500) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        member_id = f"M{i:05d}"
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        email = f"{first.lower()}.{last.lower()}{i}@example.com"
        phone = f"555-{random.randint(100,999)}-{random.randint(1000,9999)}"
        rows.append(
            {
                "member_id": member_id,
                "member_name": name,
                "email": email,
                "phone": phone,
                "ssn": random_ssn(valid=random.random() > 0.04),
                "age_group": random.choices(AGE_GROUPS, weights=[18, 20, 22, 20, 20])[0],
                "county": random.choice(COUNTIES),
                "state": random.choice(STATES),
                "risk_score": round(random.uniform(0.05, 0.98), 3),
                "chronic_condition": random.choices(CHRONIC, weights=[35, 18, 18, 7, 7, 10, 5])[0],
            }
        )

    df = pd.DataFrame(rows)

    # Deliberate issues: blank IDs and duplicate records.
    df.loc[random.sample(list(df.index), 4), "member_id"] = None
    dupes = df.sample(6, random_state=7)
    df = pd.concat([df, dupes], ignore_index=True)
    return df


def generate_enrollment(members: pd.DataFrame, n_extra_unmatched: int = 12) -> pd.DataFrame:
    valid_member_ids = members["member_id"].dropna().unique().tolist()
    rows = []
    start_base = date(2025, 1, 1)
    for idx, member_id in enumerate(valid_member_ids, 1):
        plan_id, plan_name, plan_type = random.choice(PLANS)
        start = start_base + timedelta(days=random.randint(0, 420))
        terminated = random.random() < 0.16
        termination = start + timedelta(days=random.randint(30, 360)) if terminated else None
        rows.append(
            {
                "enrollment_id": f"E{idx:06d}",
                "member_id": member_id,
                "plan_id": plan_id,
                "plan_name": plan_name,
                "plan_type": plan_type,
                "status": "Terminated" if terminated else "Active",
                "effective_date": start.isoformat(),
                "termination_date": termination.isoformat() if termination else "",
            }
        )

    # Deliberate unmatched member IDs.
    for i in range(n_extra_unmatched):
        plan_id, plan_name, plan_type = random.choice(PLANS)
        rows.append(
            {
                "enrollment_id": f"E999{i:03d}",
                "member_id": f"MISSING{i:03d}",
                "plan_id": plan_id,
                "plan_name": plan_name,
                "plan_type": plan_type,
                "status": random.choice(["Active", "Terminated"]),
                "effective_date": "2026-02-01",
                "termination_date": "",
            }
        )

    df = pd.DataFrame(rows)
    # Deliberate invalid dates.
    bad_idx = random.sample(list(df.index), 5)
    df.loc[bad_idx, "effective_date"] = random.choice(["2026-99-99", "not-a-date", "13/45/2026"])
    return df


def generate_pharmacy_claims(members: pd.DataFrame, n: int = 2000) -> pd.DataFrame:
    valid_member_ids = members["member_id"].dropna().unique().tolist()
    rows = []
    base = date(2025, 7, 1)
    for i in range(1, n + 1):
        member_id = random.choice(valid_member_ids)
        drug_class = random.choices(DRUG_CLASSES, weights=[24, 20, 8, 16, 14, 18])[0]
        cost_multiplier = {
            "Diabetes": 1.0,
            "Cardiology": 1.2,
            "Oncology": 8.5,
            "Specialty": 6.0,
            "Respiratory": 1.8,
            "Behavioral Health": 1.1,
        }[drug_class]
        paid = round(random.uniform(18, 260) * cost_multiplier, 2)
        claim_date = base + timedelta(days=random.randint(0, 350))
        rows.append(
            {
                "claim_id": f"C{i:07d}",
                "member_id": member_id,
                "drug_class": drug_class,
                "pharmacy_name": random.choice(PHARMACIES),
                "claim_date": claim_date.isoformat(),
                "paid_amount": paid,
                "claim_status": random.choices(["Paid", "Rejected", "Reversed"], weights=[88, 8, 4])[0],
            }
        )

    # Deliberate unmatched claims.
    for i in range(10):
        rows.append(
            {
                "claim_id": f"CMISS{i:04d}",
                "member_id": f"MISSING_CLAIM{i:03d}",
                "drug_class": random.choice(DRUG_CLASSES),
                "pharmacy_name": random.choice(PHARMACIES),
                "claim_date": "2026-04-01",
                "paid_amount": round(random.uniform(40, 800), 2),
                "claim_status": "Paid",
            }
        )

    df = pd.DataFrame(rows)
    # Deliberate invalid claim dates and null amounts.
    df.loc[random.sample(list(df.index), 5), "claim_date"] = random.choice(["bad-date", "2026-02-31", ""])
    df.loc[random.sample(list(df.index), 12), "paid_amount"] = None
    # Deliberate duplicate claims.
    df = pd.concat([df, df.sample(8, random_state=11)], ignore_index=True)
    return df


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    members = generate_members()
    enrollment = generate_enrollment(members)
    claims = generate_pharmacy_claims(members)

    members.to_csv(DATA_DIR / "members.csv", index=False)
    enrollment.to_csv(DATA_DIR / "enrollment.csv", index=False)
    claims.to_csv(DATA_DIR / "pharmacy_claims.csv", index=False)

    print("Generated synthetic payer source files:")
    print(f"- {DATA_DIR / 'members.csv'} ({len(members)} rows)")
    print(f"- {DATA_DIR / 'enrollment.csv'} ({len(enrollment)} rows)")
    print(f"- {DATA_DIR / 'pharmacy_claims.csv'} ({len(claims)} rows)")


if __name__ == "__main__":
    main()
