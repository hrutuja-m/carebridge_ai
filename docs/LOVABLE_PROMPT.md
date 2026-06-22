# Lovable Prompt: CareBridge AI

Paste this into Lovable to create the polished UI. Use the CSV outputs from this starter kit as the source of truth.

```text
Build a modern enterprise healthcare analytics product called CareBridge AI.

It is a HIPAA-aware healthcare payer data pipeline and executive insight layer. The product unifies synthetic member, enrollment, and PBM pharmacy claims data into executive-safe analytics.

Create 5 pages:

1. Dashboard:
Show KPI cards for total members, active members, total PBM spend, average risk score, high-risk members, data quality issues, blocked query count, and compliance score. Add charts for active members by plan, PBM spend by plan, average Rx spend by age group, and claims trend by month.

2. Data Ingestion:
Show three source files: members.csv, enrollment.csv, and pharmacy_claims.csv. For each file, show ingestion status, row count, missing values, duplicate records, invalid dates, unmatched member IDs, null paid amounts, and pass/warning/fail status.

3. Privacy & Compliance:
Show a PHI/PII classification table with column name, data type, risk level, and action. Actions include allow, mask, block, and aggregate only. Include badges for tokenization, PHI detection, role-based access, audit logging, and aggregate-only AI.

4. Ask Insights:
Create a chat-like interface where executives can ask questions. Add predefined demo questions. For each answer, show final answer, SQL used, tables used, privacy status, confidence, and allowed/blocked status. Block unsafe questions asking for names, SSNs, individual claims, member-level records, or chronic condition tied to identity.

5. Audit Log:
Show timestamp, user role, question/action, allowed or blocked status, reason, tables accessed, and privacy status.

Use a clean healthcare enterprise SaaS design with blue/green colors, professional cards, charts, compliance badges, and an executive-ready layout.

Important:
Do not expose raw names, SSNs, emails, phone numbers, raw member IDs, or individual pharmacy claims in the dashboard or Ask Insights page. Show member_token only in safe technical views. Add a visible disclaimer: “This prototype uses synthetic data and demonstrates HIPAA-aware design patterns. Production HIPAA compliance would require BAAs, encryption, formal access controls, monitoring, and compliance review.”
```
