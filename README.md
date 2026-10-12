
# MMX Smart Insurance Intelligence V6 Production

V5 is an enterprise-oriented insurance intelligence console with a production architecture path.

## Included
- Executive command centre
- Portfolio, policy and claims intelligence
- Fraud and crime risk queue
- Risk scoring and customer retention intelligence
- Broker/channel analytics
- Third-party/provider risk
- Explainable AI decision support
- Human approval workflow
- Alerts and investigation workbench
- Reports and CSV export
- Role-based authentication
- PBKDF2 password hashing
- Audit logging
- SQLite demo database
- PostgreSQL-ready deployment configuration
- Environment-based database configuration

## Demo credentials
- admin / mmx2026
- executive / mmx2026
- claims / mmx2026
- risk / mmx2026
- investigator / mmx2026

These credentials are for demonstration only. Change them before any real deployment.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## PostgreSQL
Set:
```bash
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/mmx
```
The V5 demo UI uses SQLite by default for zero-configuration startup. A production implementation should use managed PostgreSQL, encrypted connections, backups and restricted network access.

## Streamlit Cloud
Upload the project to GitHub and deploy `app.py`. Add production secrets/environment configuration through the deployment platform rather than committing passwords or database credentials.

## Production hardening still required
This reference implementation is not a finished regulated production system. Before live use, implement:
- SSO/OIDC or enterprise identity provider
- MFA
- managed PostgreSQL
- encryption at rest/in transit
- secrets manager
- granular permissions
- data retention/deletion controls
- formal model validation
- model monitoring
- security testing and penetration testing
- backup/restore procedures
- POPIA and applicable insurance regulatory controls
- human approval and documented decision governance

AI features are decision-support only and must not be treated as autonomous claim approval/denial or other high-impact decisions.


## V6 additions
- Secure-token REST API layer
- Health endpoint
- Portfolio and alert API endpoints
- Claim ingestion endpoint
- Gunicorn deployment
- Docker Compose architecture
- Production deployment documentation
- API examples
- PostgreSQL environment configuration
