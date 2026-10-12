
# MMX V6 Production Deployment

## Architecture

Client / Executive
        |
        v
MMX Streamlit Console -----> Intelligence Database
        |
        +----> MMX REST API ----> External systems
        |
        +----> Audit / Governance

## Recommended production stack

- Managed PostgreSQL
- Streamlit or container hosting for the console
- Flask/Gunicorn API behind HTTPS
- Enterprise identity provider for SSO/MFA
- Secrets manager
- Central logging and monitoring
- Automated encrypted backups

## API

Health:
GET /health

Portfolio:
GET /api/v1/portfolio

Alerts:
GET /api/v1/alerts

Claim ingestion:
POST /api/v1/ingest/claim

Production API requests must include:
X-MMX-API-TOKEN: <secret>

Do not place production tokens in source code.

## Important

This V6 package is a production-oriented reference architecture, not a claim to have connected to MMX's private systems. Real integrations require the relevant MMX data owners, API credentials, schemas, security approvals and legal/compliance review.

AI recommendations remain human-reviewed decision support.
