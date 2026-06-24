# CareBridge AI Roadmap

## Current Status
CareBridge AI is a HIPAA-aware healthcare payer data pipeline prototype using synthetic member, enrollment, and PBM claims data.

## Production-Readiness Goals

### Data Governance
- Add schema validation for all input files
- Improve PHI/PII classification rules
- Add data quality checks for missing, duplicate, and invalid records

### Security
- Move runtime secrets to environment variables
- Add role-based access control design
- Add audit logging for dashboard and insight queries

### Backend/API Layer
- Add FastAPI endpoints for metrics and controlled insights
- Separate business logic from the Streamlit dashboard
- Add request validation and error handling

### Deployment
- Add Docker-based local deployment
- Prepare Streamlit Cloud deployment
- Add CI checks for tests and linting

### Documentation
- Add architecture diagram
- Add data dictionary
- Add demo screenshots
