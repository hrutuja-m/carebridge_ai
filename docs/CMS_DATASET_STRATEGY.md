# Optional Public Dataset Strategy

For the hackathon MVP, use the synthetic files in `/data` first. Then, if time allows, replace or augment them with real public CMS datasets.

Recommended public sources:

1. CMS Medicare Advantage / Part D Contract and Enrollment Data
   - Use for plan/contract/county enrollment trends.
   - Join at safe aggregate keys such as state, county, month, contract, and plan type.

2. CMS Medicare Part D Prescribers by Provider and Drug
   - Use for prescription volume and total drug cost analytics.
   - Join at safe aggregate keys such as state, drug class/category, and month/year.

Important:
Do not claim these public datasets are linked member-level payer data. They are public aggregate/de-identified datasets. In the demo, explain that CareBridge AI can handle real public enrollment/PBM files and uses synthetic member data only to demonstrate PHI/PII controls safely.

Recommended pitch line:
"CareBridge AI uses real-public-data-compatible schemas for enrollment and PBM analytics, combined with a synthetic member-management layer to safely demonstrate PHI/PII protection. The executive and AI layers only access aggregate-safe metrics."
