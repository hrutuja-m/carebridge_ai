# CareBridge AI

**CareBridge AI** is a HIPAA-aware healthcare payer data pipeline and executive insight layer. It unifies synthetic member, enrollment, and pharmacy benefit manager (PBM) claims data into privacy-safe analytics outputs with PHI/PII classification, tokenized member identifiers, aggregate-only metrics, a Streamlit dashboard, controlled natural-language insights, and audit logging.

> This is a prototype built with synthetic data. It demonstrates healthcare data governance patterns, not production HIPAA compliance.

## Why this project matters

Healthcare payer data often lives across disconnected systems: member management, enrollment, and PBM claims. Executives need fast visibility into performance, but raw payer data contains sensitive member-level information. CareBridge AI solves this by creating an executive-safe analytics layer that blocks unsafe requests and exposes only minimum-necessary, aggregate insights.

## Core features

- **Synthetic payer data generation** for members, enrollment, and pharmacy claims
- **Data quality checks** for missing values, duplicates, invalid dates, invalid SSNs, null paid amounts, and unmatched member IDs
- **PHI/PII classification** with allow, mask, block, and aggregate-only handling
- **Tokenized safe data layer** using member tokens instead of raw member IDs
- **Executive metrics** for active enrollment, PBM spend, risk, claim volume, and compliance score
- **Controlled Ask Insights layer** that maps questions to predefined aggregate-safe queries
- **Unsafe query blocking** for SSNs, member names, individual claims, and member-level health details
- **Audit logging** for pipeline actions and insight requests
- **Streamlit dashboard** for demo-ready visualization

## Tech stack

| Area | Tools |
|---|---|
| Language | Python |
| Data processing | pandas |
| App / dashboard | Streamlit |
| Governance logic | Rule-based PHI/PII classification, safe-query routing |
| Data format | CSV, JSON manifest |

## Architecture

```text
Member System        Enrollment System        PBM Claims System
      ↓                     ↓                         ↓
             Raw Synthetic Data Generation
                         ↓
                 Data Quality Validation
                         ↓
                  PHI/PII Classification
                         ↓
          Tokenize / Mask / Block / Aggregate
                         ↓
              Executive-Safe Data Layer
                         ↓
        Dashboard + Controlled Ask Insights
                         ↓
                 Audit Log + Manifest
```

## Repository structure

```text
carebridge-ai/
├── app/
│   └── streamlit_app.py
├── data/
│   ├── members.csv
│   ├── enrollment.csv
│   └── pharmacy_claims.csv
├── docs/
│   ├── CMS_DATASET_STRATEGY.md
│   └── LOVABLE_PROMPT.md
├── output/
│   ├── executive_metrics.csv
│   ├── ingestion_quality_summary.csv
│   ├── phi_pii_classification.csv
│   ├── audit_log.csv
│   └── other generated safe analytics outputs
├── scripts/
│   ├── generate_synthetic_data.py
│   ├── ingest_pipeline.py
│   ├── ask_insights.py
│   └── run_all.py
├── requirements.txt
├── LICENSE
└── README.md
```

## Quickstart

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/carebridge-ai.git
cd carebridge-ai
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

For Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the full pipeline

```bash
python scripts/run_all.py
```

### 5. Launch the Streamlit app

```bash
streamlit run app/streamlit_app.py
```

## Demo flow

1. Generate synthetic payer datasets.
2. Run data quality checks.
3. Classify sensitive fields as allowed, masked, blocked, or aggregate-only.
4. Create tokenized executive-safe tables.
5. Build aggregate metrics.
6. Ask safe and unsafe natural-language questions.
7. Review the audit log.

## Example safe questions

- Which plan has the highest PBM spend?
- How many active members are enrolled by plan type?
- Show pharmacy spend by age group.
- What is the claims trend by month?
- Summarize executive performance this month.

## Example blocked questions

- Show me member names with diabetes.
- Give me SSNs for all active members.
- Show individual pharmacy claims for member M001.

## Key outputs

| Output | Purpose |
|---|---|
| `output/ingestion_quality_summary.csv` | Data validation results by source file |
| `output/phi_pii_classification.csv` | Sensitivity classification and access policy by field |
| `output/members_safe.csv` | Tokenized and masked member data |
| `output/enrollment_safe.csv` | Tokenized enrollment data |
| `output/pharmacy_claims_safe.csv` | Tokenized pharmacy claims data |
| `output/executive_metrics.csv` | One-row executive KPI summary |
| `output/audit_log.csv` | Governance log for actions and insight requests |
| `output/manifest.json` | Pipeline run metadata |

## Privacy and governance design

CareBridge AI follows a minimum-necessary pattern:

- Raw member identifiers are replaced with stable tokens.
- SSNs are blocked from the executive-safe layer.
- Names, emails, and phone numbers are masked.
- Health and drug-class attributes are treated as aggregate-only.
- Natural-language insight requests are routed through predefined safe queries.
- Unsafe member-level requests are blocked and logged.

## Limitations

This project is a demo prototype. A production-grade HIPAA system would require business associate agreements, encryption at rest and in transit, role-based access controls, secure secrets management, monitoring, formal compliance review, tested de-identification methods, and organization-specific governance policies.

## Resume-ready project bullet

Built **CareBridge AI**, a HIPAA-aware healthcare payer analytics prototype using Python, pandas, and Streamlit to ingest synthetic member, enrollment, and PBM claims data; implemented data quality checks, PHI/PII classification, tokenized safe tables, aggregate executive metrics, controlled natural-language insights, unsafe-query blocking, and audit logging.

## Author

**Rutuja More**  
MS Data Science, University of Massachusetts Dartmouth
